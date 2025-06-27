"""
Simulation management API routes.
"""

from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import threading
import time
import traceback

# Import with fallback for different execution contexts
from src.models.database import Simulation, Dataset, Forecast, User, db, AuditLog
from src.models.epidemiological import (
    create_seir_model,
    create_agent_based_model,
    create_network_model,
)
from src.models.ml_forecasting import create_forecaster, create_parameter_estimator
from src.auth import token_required, PermissionManager

simulations_bp = Blueprint("simulations", __name__)

# Valid model types
VALID_MODEL_TYPES = ["seir", "agent_based", "network", "ml_forecast"]


def run_simulation_async(simulation_id, app_context):
    """Run simulation asynchronously in background."""
    simulation = None

    with app_context:
        try:
            simulation = Simulation.query.get(simulation_id)
            if not simulation:
                print(f"Simulation with ID {simulation_id} not found.")
                return

            # Update status to running
            simulation.status = "running"
            simulation.started_at = datetime.utcnow()
            db.session.commit()

            params = simulation.get_parameters()
            model_type = simulation.model_type

            # Run the appropriate simulation
            if model_type == "seir":
                results = run_seir_simulation(simulation, params)
            elif model_type == "agent_based":
                results = run_agent_based_simulation(simulation, params)
            elif model_type == "network":
                results = run_network_simulation(simulation, params)
            elif model_type == "ml_forecast":
                results = run_ml_forecast_simulation(simulation, params)
            else:
                raise ValueError(f"Unknown model type: {model_type}")

            # Save results
            simulation.set_results(results)
            simulation.status = "completed"
            simulation.completed_at = datetime.utcnow()

            # Calculate metrics
            metrics = calculate_simulation_metrics(results, model_type)
            simulation.set_metrics(metrics)

            db.session.commit()
            print(f"Simulation {simulation_id} completed successfully")

        except Exception as e:
            error_msg = str(e)
            print(f"Error running simulation {simulation_id}: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")

            if simulation:
                try:
                    simulation.status = "failed"
                    simulation.completed_at = datetime.utcnow()
                    error_results = {
                        "error": error_msg,
                        "traceback": traceback.format_exc(),
                    }
                    simulation.set_results(error_results)
                    db.session.commit()
                except Exception as commit_error:
                    print(f"Failed to save error state: {commit_error}")


def run_seir_simulation(simulation, params):
    """Run SEIR model simulation."""
    try:
        model = create_seir_model(params)

        time_points = np.linspace(
            0, params.get("time_horizon", 365), params.get("time_steps", 365)
        )

        # Get initial conditions
        population = params.get("population", 100000)
        initial_conditions = params.get(
            "initial_conditions", {"S": population - 1, "E": 0, "I": 1, "R": 0}
        )

        results = model.simulate(initial_conditions, time_points)

        r0 = model.calculate_r0()
        peak_time, peak_infections = model.calculate_peak_infection(initial_conditions)

        return {
            "time": results.time.tolist(),
            "susceptible": results.susceptible.tolist(),
            "exposed": results.exposed.tolist(),
            "infectious": results.infectious.tolist(),
            "recovered": results.recovered.tolist(),
            "r0": float(r0),
            "peak_time": float(peak_time),
            "peak_infections": float(peak_infections),
            "model_type": "seir",
            "parameters": results.parameters,
        }
    except Exception as e:
        raise ValueError(f"SEIR simulation failed: {str(e)}")


def run_agent_based_simulation(simulation, params):
    """Run agent-based model simulation."""
    try:
        model = create_agent_based_model(params)
        time_steps = params.get("time_steps", 100)
        results = model.simulate(time_steps)

        return {
            "time": results["time"],
            "susceptible": results["S"],
            "exposed": results["E"],
            "infectious": results["I"],
            "recovered": results["R"],
            "model_type": "agent_based",
            "parameters": params,
        }
    except Exception as e:
        raise ValueError(f"Agent-based simulation failed: {str(e)}")


def run_network_simulation(simulation, params):
    """Run network-based model simulation."""
    try:
        model = create_network_model(params)
        num_nodes = params.get("population_size", 1000)
        model.create_network(num_nodes)

        time_steps = params.get("time_steps", 100)
        transmission_rate = params.get("transmission_rate", 0.1)
        recovery_rate = params.get("recovery_rate", 0.1)

        results = model.simulate_transmission(
            transmission_rate, recovery_rate, time_steps
        )

        return {
            "time": results["time"],
            "susceptible": results["S"],
            "infectious": results["I"],
            "recovered": results["R"],
            "model_type": "network",
            "parameters": params,
        }
    except Exception as e:
        raise ValueError(f"Network simulation failed: {str(e)}")


def run_ml_forecast_simulation(simulation, params):
    """Run machine learning forecasting simulation."""
    try:
        dataset_id = simulation.dataset_id
        if not dataset_id:
            raise ValueError("ML forecasting requires a dataset")

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")

        from src.models.database import DataPoint

        data_points = (
            DataPoint.query.filter_by(dataset_id=dataset_id)
            .order_by(DataPoint.timestamp)
            .all()
        )

        if not data_points:
            raise ValueError("Dataset contains no data points")

        # Prepare data for ML model
        data_list = []
        for dp in data_points:
            row = {
                "date": dp.timestamp,
                "infectious": dp.infectious or 0,
                "new_cases": dp.new_cases or 0,
                "deaths": dp.deaths or 0,
            }
            # Add any other available fields
            if dp.exposed is not None:
                row["exposed"] = dp.exposed
            if dp.recovered is not None:
                row["recovered"] = dp.recovered
            if dp.susceptible is not None:
                row["susceptible"] = dp.susceptible

            data_list.append(row)

        df = pd.DataFrame(data_list)

        # Validate data
        if df.empty:
            raise ValueError("No valid data found for forecasting")

        model_type = params.get("ml_model_type", "ensemble")
        forecaster = create_forecaster(model_type)

        target_col = params.get("target_column", "new_cases")
        forecast_horizon = params.get("forecast_horizon", 30)

        if target_col not in df.columns:
            available_cols = list(df.columns)
            raise ValueError(
                f"Target column '{target_col}' not found. Available columns: {available_cols}"
            )

        # Run forecasting
        forecast_result = forecaster.forecast(df, target_col, forecast_horizon)

        # Save forecast records
        forecast_date = datetime.utcnow()
        for i, prediction in enumerate(forecast_result.predictions):
            target_date = forecast_date + timedelta(days=i + 1)

            forecast = Forecast(
                simulation_id=simulation.id,
                forecast_date=forecast_date,
                target_date=target_date,
                predicted_value=float(prediction),
                forecast_type=target_col,
                model_version="1.0",
            )

            if forecast_result.confidence_intervals:
                forecast.lower_bound = float(forecast_result.confidence_intervals[0][i])
                forecast.upper_bound = float(forecast_result.confidence_intervals[1][i])

            db.session.add(forecast)

        db.session.commit()

        return {
            "predictions": forecast_result.predictions.tolist(),
            "confidence_intervals": {
                "lower": (
                    forecast_result.confidence_intervals[0].tolist()
                    if forecast_result.confidence_intervals
                    else None
                ),
                "upper": (
                    forecast_result.confidence_intervals[1].tolist()
                    if forecast_result.confidence_intervals
                    else None
                ),
            },
            "metrics": forecast_result.model_metrics,
            "feature_importance": forecast_result.feature_importance,
            "model_type": "ml_forecast",
            "parameters": params,
        }
    except Exception as e:
        raise ValueError(f"ML forecasting failed: {str(e)}")


def calculate_simulation_metrics(results, model_type):
    """Calculate performance metrics for simulation results."""
    metrics = {}

    try:
        if model_type in ["seir", "agent_based", "network"]:
            if "infectious" in results:
                infectious = np.array(results["infectious"])
                if infectious.size > 0:
                    metrics["max_infections"] = float(np.max(infectious))
                    metrics["total_infections"] = float(np.sum(infectious))
                    metrics["peak_day"] = int(np.argmax(infectious))

            if "recovered" in results:
                recovered = np.array(results["recovered"])
                if recovered.size > 0:
                    metrics["final_recovered"] = float(recovered[-1])

            if "r0" in results:
                metrics["r0"] = float(results["r0"])

        elif model_type == "ml_forecast":
            if "metrics" in results:
                metrics.update(results["metrics"])

        metrics["simulation_duration"] = len(results.get("time", []))
        metrics["calculated_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        print(f"Error calculating metrics: {e}")
        metrics["error"] = f"Metrics calculation failed: {str(e)}"

    return metrics


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
def create_simulation():
    """Create and run a new simulation."""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        required_fields = ["name", "model_type"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"{field} is required"}), 400

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

        # Start simulation in background thread
        from flask import current_app

        app_context = current_app.app_context()

        thread = threading.Thread(
            target=run_simulation_async, args=(simulation.id, app_context), daemon=True
        )
        thread.start()

        return (
            jsonify(
                {
                    "message": "Simulation created and started",
                    "simulation": simulation.to_dict(),
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
