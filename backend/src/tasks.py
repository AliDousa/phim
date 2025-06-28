"""
Celery tasks for the Public Health Intelligence Platform.
"""

import os
import time
from celery import Celery
from flask import Flask


def make_celery(app: Flask = None) -> Celery:
    """
    Create and configure Celery instance for Flask application.

    Args:
        app: Flask application instance

    Returns:
        Configured Celery instance
    """
    celery = Celery(
        app.import_name if app else "phip-backend",
        backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    )

    # Configure Celery
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
    )

    if app:
        # Update task base class to work with Flask app context
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context."""

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

        # Store app instance
        celery.app = app

    return celery


# Create a default Celery instance for importing tasks
celery = make_celery()


@celery.task(bind=True)
def run_simulation_task(self, simulation_id):
    """
    Background task to run epidemiological simulations.

    Args:
        simulation_id: ID of the simulation to run
    """
    try:
        # Import here to avoid circular imports
        from src.models.database import Simulation, db
        from src.models.epidemiological import (
            create_seir_model,
            create_agent_based_model,
            create_network_model,
        )
        from src.models.ml_forecasting import create_forecaster
        import pandas as pd
        import numpy as np
        from datetime import datetime

        # Get simulation
        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        # Update status
        simulation.status = "running"
        simulation.started_at = datetime.utcnow()
        db.session.commit()

        # Get parameters
        params = simulation.get_parameters()
        model_type = simulation.model_type

        # Run simulation based on type
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

        # Calculate execution time
        simulation.calculate_execution_time()

        db.session.commit()

        return {
            "status": "completed",
            "simulation_id": simulation_id,
            "results": results,
        }

    except Exception as e:
        # Update simulation status on failure
        try:
            simulation = Simulation.query.get(simulation_id)
            if simulation:
                simulation.status = "failed"
                simulation.completed_at = datetime.utcnow()
                error_results = {"error": str(e), "task_id": self.request.id}
                simulation.set_results(error_results)
                db.session.commit()
        except Exception:
            pass  # Don't fail on cleanup

        # Re-raise the original exception
        raise


@celery.task(bind=True)
def process_dataset_task(self, dataset_id):
    """
    Background task to process uploaded datasets.

    Args:
        dataset_id: ID of the dataset to process
    """
    try:
        from src.models.database import Dataset, DataPoint, db
        import pandas as pd
        from datetime import datetime

        # Get dataset
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        # Update status
        dataset.processing_status = "processing"
        dataset.processing_started_at = datetime.utcnow()
        db.session.commit()

        # Process the dataset (this is a placeholder for actual processing)
        # In a real implementation, you'd read the file and process it

        # Update statistics
        dataset.update_statistics()

        # Mark as completed
        dataset.processing_status = "completed"
        dataset.processing_completed_at = datetime.utcnow()
        dataset.is_validated = True

        db.session.commit()

        return {
            "status": "completed",
            "dataset_id": dataset_id,
            "total_records": dataset.total_records,
        }

    except Exception as e:
        # Update dataset status on failure
        try:
            dataset = Dataset.query.get(dataset_id)
            if dataset:
                dataset.processing_status = "failed"
                dataset.processing_completed_at = datetime.utcnow()
                dataset.validation_errors = str(e)
                db.session.commit()
        except Exception:
            pass

        raise


def run_seir_simulation(simulation, params):
    """Run SEIR model simulation."""
    try:
        from src.models.epidemiological import create_seir_model
        import numpy as np

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
        from src.models.epidemiological import create_agent_based_model

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
        from src.models.epidemiological import create_network_model

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
        from src.models.database import Dataset, DataPoint, Forecast
        from src.models.ml_forecasting import create_forecaster
        import pandas as pd
        from datetime import datetime, timedelta

        dataset_id = simulation.dataset_id
        if not dataset_id:
            raise ValueError("ML forecasting requires a dataset")

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")

        # Get data points
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
            if dp.exposed is not None:
                row["exposed"] = dp.exposed
            if dp.recovered is not None:
                row["recovered"] = dp.recovered
            if dp.susceptible is not None:
                row["susceptible"] = dp.susceptible

            data_list.append(row)

        df = pd.DataFrame(data_list)

        if df.empty:
            raise ValueError("No valid data found for forecasting")

        model_type = params.get("ml_model_type", "ensemble")
        forecaster = create_forecaster(model_type)

        target_col = params.get("target_column", "new_cases")
        forecast_horizon = params.get("forecast_horizon", 30)

        if target_col not in df.columns:
            available_cols = list(df.columns)
            raise ValueError(
                f"Target column '{target_col}' not found. Available: {available_cols}"
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


# Periodic tasks
@celery.task
def cleanup_old_simulations():
    """Clean up old completed simulations."""
    try:
        from src.models.database import Simulation, db
        from datetime import datetime, timedelta

        # Delete simulations older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_simulations = Simulation.query.filter(
            Simulation.created_at < cutoff_date,
            Simulation.status.in_(["completed", "failed"]),
        ).all()

        count = 0
        for sim in old_simulations:
            db.session.delete(sim)
            count += 1

        db.session.commit()

        return f"Cleaned up {count} old simulations"

    except Exception as e:
        return f"Cleanup failed: {str(e)}"


@celery.task
def health_check_task():
    """Periodic health check task."""
    try:
        from src.models.database import db
        from sqlalchemy import text

        # Test database connection
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


# Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    "cleanup-old-simulations": {
        "task": "src.tasks.cleanup_old_simulations",
        "schedule": 86400.0,  # Daily
    },
    "health-check": {
        "task": "src.tasks.health_check_task",
        "schedule": 300.0,  # Every 5 minutes
    },
}

celery.conf.timezone = "UTC"
