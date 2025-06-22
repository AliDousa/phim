"""
Models package for the Public Health Intelligence Platform.

This package contains:
- database.py: Database models and schemas
- epidemiological.py: Disease spread simulation models
- ml_forecasting.py: Machine learning forecasting models
"""

# Import main database models for easy access
try:
    from .database import (
        db,
        User,
        Dataset,
        DataPoint,
        Simulation,
        Forecast,
        ModelComparison,
        AuditLog,
    )

    from .epidemiological import (
        SEIRModel,
        AgentBasedModel,
        NetworkModel,
        create_seir_model,
        create_agent_based_model,
        create_network_model,
    )

    from .ml_forecasting import (
        TimeSeriesForecaster,
        EnsembleForecaster,
        ParameterEstimator,
        create_forecaster,
        create_parameter_estimator,
    )

    __all__ = [
        # Database models
        "db",
        "User",
        "Dataset",
        "DataPoint",
        "Simulation",
        "Forecast",
        "ModelComparison",
        "AuditLog",
        # Epidemiological models
        "SEIRModel",
        "AgentBasedModel",
        "NetworkModel",
        "create_seir_model",
        "create_agent_based_model",
        "create_network_model",
        # ML models
        "TimeSeriesForecaster",
        "EnsembleForecaster",
        "ParameterEstimator",
        "create_forecaster",
        "create_parameter_estimator",
    ]

except ImportError as e:
    # Handle import errors gracefully during development
    print(f"Warning: Could not import all models: {e}")
    __all__ = []
