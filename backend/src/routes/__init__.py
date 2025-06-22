"""
Routes package for the Public Health Intelligence Platform API.

This package contains:
- auth.py: Authentication and user management endpoints
- datasets.py: Dataset upload and management endpoints
- simulations.py: Simulation creation and management endpoints
"""

try:
    from .auth import auth_bp
    from .datasets import datasets_bp
    from .simulations import simulations_bp

    __all__ = ["auth_bp", "datasets_bp", "simulations_bp"]

except ImportError as e:
    print(f"Warning: Could not import all routes: {e}")
    __all__ = []
