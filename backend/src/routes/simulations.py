"""
Simulation management API routes.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from celery.result import AsyncResult

# Import with fallback for different execution contexts
from src.models.database import Simulation, Dataset, Forecast, User, db, AuditLog
from src.models.epidemiological import (
    create_seir_model,
    create_agent_based_model,
    create_network_model,
)
from src.models.ml_forecasting import create_forecaster, create_parameter_estimator
from src.auth import token_required, PermissionManager
from src.tasks import run_simulation_task
from src.security import validate_json_input

simulations_bp = Blueprint("simulations", __name__)

# Valid model types
VALID_MODEL_TYPES = ["seir", "agent_based", "network", "ml_forecast"]


@simulations_bp.route("/task-status/<string:task_id>", methods=["GET"])
@token_required
def get_task_status(task_id):
    """Get the status of a Celery task."""
    task = run_simulation_task.AsyncResult(task_id)

    response_data = {
        "task_id": task_id,
        "status": task.state,
        "info": None,
    }

    if task.state == "PENDING":
        response_data["info"] = "Task is waiting for execution or is unknown."
    elif task.state == "SUCCESS":
        response_data["info"] = "Task completed successfully. Simulation data is updated."
        # The result of the task itself might be large, so we don't return it.
        # The frontend should re-fetch the simulation object.
    elif task.state == "FAILURE":
        response_data["info"] = str(task.info)  # Contains the exception
    else:
        # For other states like 'STARTED', 'RETRY'
        response_data["info"] = str(task.info)

    return jsonify(response_data)


@simulations_bp.route("/", methods=["GET"])
@token_required
def get_simulations():
    """Get all simulations for the current user."""
    try:
        user = request.current_user

        if user.role == "admin":
            simulations = Simulation.query.order_by(Simulation.created_at.desc()).all()
        else:
            simulations = (
                Simulation.query.filter_by(user_id=user.id)
                .order_by(Simulation.created_at.desc())
                .all()
            )

        return jsonify({"simulations": [sim.to_dict() for sim in simulations]}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve simulations: {str(e)}"}), 500


@simulations_bp.route("/<int:simulation_id>", methods=["GET"])
@token_required
def get_simulation(simulation_id):
    """Get specific simulation by ID."""
    try:
        user = request.current_user

        if not PermissionManager.can_access_simulation(user, simulation_id):
            return jsonify({"error": "Access denied"}), 403

        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return jsonify({"error": "Simulation not found"}), 404

        return jsonify({"simulation": simulation.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve simulation: {str(e)}"}), 500


@simulations_bp.route("/", methods=["POST"])
@token_required
@validate_json_input(
    required_fields=["name", "model_type"],
    optional_fields=["description", "dataset_id", "parameters"]
)
def create_simulation():
    """Create and run a new simulation."""
    try:
        user = request.current_user
        data = request.get_json()

        # Validate model type
        if data["model_type"] not in VALID_MODEL_TYPES:
            return (
                jsonify({"error": f"model_type must be one of: {VALID_MODEL_TYPES}"}),
                400,
            )

        # Validate dataset access if required
        dataset_id = data.get("dataset_id")
        if dataset_id:
            if not PermissionManager.can_access_dataset(user, dataset_id):
                return jsonify({"error": "Access denied to specified dataset"}), 403

            # Verify dataset exists
            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                return jsonify({"error": "Dataset not found"}), 404

        # Validate parameters
        parameters = data.get("parameters", {})
        if not isinstance(parameters, dict):
            return jsonify({"error": "Parameters must be a JSON object"}), 400

        # Validate model-specific requirements
        if data["model_type"] == "ml_forecast" and not dataset_id:
            return jsonify({"error": "ML forecast simulations require a dataset"}), 400

        # Create simulation record
        simulation = Simulation(
            name=data["name"].strip(),
            description=data.get("description", "").strip(),
            model_type=data["model_type"],
            user_id=user.id,
            dataset_id=dataset_id,
            status="pending",
        )

        simulation.set_parameters(parameters)

        db.session.add(simulation)
        db.session.commit()

        # Create audit log
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="simulation_created",
                resource_type="simulation",
                resource_id=simulation.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            audit_log.set_details(
                {
                    "simulation_name": simulation.name,
                    "model_type": simulation.model_type,
                    "parameters": parameters,
                }
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            print(f"Audit logging failed: {e}")

        # Start simulation using Celery for true asynchronous processing
        task = run_simulation_task.delay(simulation.id)

        # Update simulation with task ID for tracking
        simulation.task_id = task.id
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Simulation created and started",
                    "simulation": simulation.to_dict(),
                    "task_id": task.id,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create simulation: {str(e)}"}), 500


@simulations_bp.route("/<int:simulation_id>", methods=["DELETE"])
@token_required
def delete_simulation(simulation_id):
    """Delete simulation and all associated data."""
    try:
        user = request.current_user

        if not PermissionManager.can_access_simulation(user, simulation_id):
            return jsonify({"error": "Access denied"}), 403

        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return jsonify({"error": "Simulation not found"}), 404

        if simulation.status == "running":
            return jsonify({"error": "Cannot delete running simulation"}), 400

        simulation_name = simulation.name

        # Create audit log before deletion
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="simulation_deleted",
                resource_type="simulation",
                resource_id=simulation.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            audit_log.set_details({"simulation_name": simulation_name})
            db.session.add(audit_log)
        except Exception as e:
            print(f"Audit logging failed: {e}")

        # Delete simulation (cascade will handle forecasts)
        db.session.delete(simulation)
        db.session.commit()

        return jsonify({"message": "Simulation deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete simulation: {str(e)}"}), 500


@simulations_bp.route("/<int:simulation_id>/forecasts", methods=["GET"])
@token_required
def get_simulation_forecasts(simulation_id):
    """Get forecasts for a simulation."""
    try:
        user = request.current_user

        if not PermissionManager.can_access_simulation(user, simulation_id):
            return jsonify({"error": "Access denied"}), 403

        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return jsonify({"error": "Simulation not found"}), 404

        forecasts = (
            Forecast.query.filter_by(simulation_id=simulation_id)
            .order_by(Forecast.target_date)
            .all()
        )

        return (
            jsonify({"forecasts": [forecast.to_dict() for forecast in forecasts]}),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve forecasts: {str(e)}"}), 500


@simulations_bp.route("/compare", methods=["POST"])
@token_required
def compare_simulations():
    """Compare multiple simulations."""
    try:
        user = request.current_user
        data = request.get_json()

        if not data or "simulation_ids" not in data:
            return jsonify({"error": "simulation_ids array is required"}), 400

        simulation_ids = data["simulation_ids"]
        if not isinstance(simulation_ids, list) or len(simulation_ids) < 2:
            return (
                jsonify({"error": "At least 2 simulation IDs required for comparison"}),
                400,
            )

        simulations = []
        for sim_id in simulation_ids:
            if not isinstance(sim_id, int):
                return jsonify({"error": "All simulation IDs must be integers"}), 400

            if not PermissionManager.can_access_simulation(user, sim_id):
                return jsonify({"error": f"Access denied to simulation {sim_id}"}), 403

            simulation = Simulation.query.get(sim_id)
            if not simulation:
                return jsonify({"error": f"Simulation {sim_id} not found"}), 404

            if simulation.status != "completed":
                return jsonify({"error": f"Simulation {sim_id} is not completed"}), 400

            simulations.append(simulation)

        # Build comparison results
        comparison_results = {}
        for simulation in simulations:
            comparison_results[simulation.id] = {
                "name": simulation.name,
                "model_type": simulation.model_type,
                "status": simulation.status,
                "created_at": (
                    simulation.created_at.isoformat() if simulation.created_at else None
                ),
                "completed_at": (
                    simulation.completed_at.isoformat()
                    if simulation.completed_at
                    else None
                ),
                "results": simulation.get_results(),
                "metrics": simulation.get_metrics(),
            }

        # Calculate comparative metrics
        comparative_metrics = {}

        # Compare peak infections
        peak_infections = {}
        for sim_id, data in comparison_results.items():
            metrics = data.get("metrics", {})
            if "max_infections" in metrics:
                peak_infections[sim_id] = metrics["max_infections"]

        if peak_infections:
            comparative_metrics["peak_infections"] = peak_infections
            comparative_metrics["highest_peak"] = max(
                peak_infections, key=peak_infections.get
            )
            comparative_metrics["lowest_peak"] = min(
                peak_infections, key=peak_infections.get
            )

        # Compare R0 values
        r0_values = {}
        for sim_id, data in comparison_results.items():
            metrics = data.get("metrics", {})
            if "r0" in metrics:
                r0_values[sim_id] = metrics["r0"]

        if r0_values:
            comparative_metrics["r0_values"] = r0_values

        return (
            jsonify(
                {
                    "comparison_results": comparison_results,
                    "comparative_metrics": comparative_metrics,
                    "compared_at": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Comparison failed: {str(e)}"}), 500


@simulations_bp.route("/types", methods=["GET"])
@token_required
def get_simulation_types():
    """Get available simulation types and their parameters."""
    try:
        simulation_types = {
            "seir": {
                "name": "SEIR Model",
                "description": "Susceptible-Exposed-Infectious-Recovered compartmental model",
                "parameters": {
                    "beta": {
                        "type": "number",
                        "description": "Transmission rate",
                        "default": 0.5,
                    },
                    "sigma": {
                        "type": "number",
                        "description": "Incubation rate",
                        "default": 0.2,
                    },
                    "gamma": {
                        "type": "number",
                        "description": "Recovery rate",
                        "default": 0.1,
                    },
                    "population": {
                        "type": "integer",
                        "description": "Total population",
                        "default": 100000,
                    },
                    "time_horizon": {
                        "type": "integer",
                        "description": "Simulation time (days)",
                        "default": 365,
                    },
                },
            },
            "agent_based": {
                "name": "Agent-Based Model",
                "description": "Individual agent simulation with contact networks",
                "parameters": {
                    "population_size": {
                        "type": "integer",
                        "description": "Number of agents",
                        "default": 1000,
                    },
                    "transmission_probability": {
                        "type": "number",
                        "description": "Transmission probability",
                        "default": 0.05,
                    },
                    "recovery_time": {
                        "type": "integer",
                        "description": "Recovery time (days)",
                        "default": 10,
                    },
                    "incubation_time": {
                        "type": "integer",
                        "description": "Incubation time (days)",
                        "default": 5,
                    },
                },
            },
            "network": {
                "name": "Network Model",
                "description": "Disease spread on social networks",
                "parameters": {
                    "population_size": {
                        "type": "integer",
                        "description": "Network size",
                        "default": 1000,
                    },
                    "transmission_rate": {
                        "type": "number",
                        "description": "Transmission rate",
                        "default": 0.1,
                    },
                    "recovery_rate": {
                        "type": "number",
                        "description": "Recovery rate",
                        "default": 0.1,
                    },
                    "network_type": {
                        "type": "string",
                        "description": "Network type",
                        "default": "small_world",
                    },
                },
            },
            "ml_forecast": {
                "name": "ML Forecasting",
                "description": "Machine learning-based forecasting",
                "parameters": {
                    "ml_model_type": {
                        "type": "string",
                        "description": "ML model type",
                        "default": "ensemble",
                    },
                    "target_column": {
                        "type": "string",
                        "description": "Target column to forecast",
                        "default": "new_cases",
                    },
                    "forecast_horizon": {
                        "type": "integer",
                        "description": "Forecast horizon (days)",
                        "default": 30,
                    },
                },
                "requires_dataset": True,
            },
        }

        return jsonify({"simulation_types": simulation_types}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get simulation types: {str(e)}"}), 500


@simulations_bp.route("/<int:simulation_id>/run", methods=["POST"])
@token_required
def run_simulation_endpoint(simulation_id):
    """Re-run an existing simulation."""
    try:
        user = request.current_user

        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return jsonify({"error": "Simulation not found"}), 404

        # Check permission
        if simulation.user_id != user.id and user.role != "admin":
            return jsonify({"error": "Access denied"}), 403

        # Reset simulation status
        simulation.status = "pending"
        simulation.started_at = None
        simulation.completed_at = None
        simulation.execution_time = None
        db.session.commit()

        # Re-run simulation using Celery
        task = run_simulation_task.delay(simulation.id)
        simulation.task_id = task.id
        db.session.commit()

        return jsonify({
            "message": "Simulation restarted successfully",
            "simulation": simulation.to_dict(),
            "task_id": task.id,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to run simulation: {str(e)}"}), 500
