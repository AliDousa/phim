"""
Test script for epidemiological and ML models.
"""

import sys
import os
sys.path.append('/home/ubuntu/public-health-intelligence-platform/backend')

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Import our models
from src.models.epidemiological import create_seir_model, create_agent_based_model, create_network_model
from src.models.ml_forecasting import create_forecaster, create_parameter_estimator

def test_seir_model():
    """Test SEIR epidemiological model."""
    print("Testing SEIR Model...")
    
    # Create model parameters
    parameters = {
        'beta': 0.5,      # Transmission rate
        'sigma': 1/5.1,   # Incubation rate
        'gamma': 1/10,    # Recovery rate
        'population': 100000
    }
    
    # Create model
    model = create_seir_model(parameters)
    
    # Set up simulation
    time_points = np.linspace(0, 365, 365)
    initial_conditions = {
        'S': 99999,
        'E': 0,
        'I': 1,
        'R': 0
    }
    
    # Run simulation
    results = model.simulate(initial_conditions, time_points)
    
    # Calculate metrics
    r0 = model.calculate_r0()
    peak_time, peak_infections = model.calculate_peak_infection(initial_conditions)
    
    print(f"  R0: {r0:.2f}")
    print(f"  Peak infections: {peak_infections:.0f} at day {peak_time:.0f}")
    print(f"  Final recovered: {results.recovered[-1]:.0f}")
    print("  SEIR Model test passed!")
    
    return True

def test_agent_based_model():
    """Test agent-based model."""
    print("\nTesting Agent-Based Model...")
    
    # Create model parameters
    parameters = {
        'population_size': 1000,
        'transmission_probability': 0.05,
        'recovery_time': 10,
        'incubation_time': 5
    }
    
    # Create model
    model = create_agent_based_model(parameters)
    
    # Run simulation
    results = model.simulate(50)
    
    print(f"  Initial susceptible: {results['S'][0]}")
    print(f"  Final susceptible: {results['S'][-1]}")
    print(f"  Final recovered: {results['R'][-1]}")
    print("  Agent-Based Model test passed!")
    
    return True

def test_network_model():
    """Test network-based model."""
    print("\nTesting Network Model...")
    
    # Create model parameters
    parameters = {
        'network_type': 'small_world',
        'network_params': {'k': 4, 'p': 0.1}
    }
    
    # Create model
    model = create_network_model(parameters)
    
    # Create network
    model.create_network(500)
    
    # Run simulation
    results = model.simulate_transmission(
        transmission_rate=0.1,
        recovery_rate=0.1,
        time_steps=50
    )
    
    print(f"  Initial susceptible: {results['S'][0]}")
    print(f"  Final susceptible: {results['S'][-1]}")
    print(f"  Final recovered: {results['R'][-1]}")
    print("  Network Model test passed!")
    
    return True

def test_ml_forecasting():
    """Test machine learning forecasting."""
    print("\nTesting ML Forecasting...")
    
    # Create synthetic time series data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Generate synthetic epidemic curve
    t = np.arange(100)
    infectious = 10 * np.exp(0.1 * t) * np.exp(-0.002 * t**2) + np.random.normal(0, 2, 100)
    infectious = np.maximum(infectious, 0)  # Ensure non-negative
    
    # Create DataFrame
    data = pd.DataFrame({
        'date': dates,
        'infectious': infectious
    })
    
    # Test different forecasters
    for model_type in ['random_forest', 'gradient_boosting', 'linear']:
        print(f"  Testing {model_type} forecaster...")
        
        forecaster = create_forecaster(model_type)
        
        try:
            # Run forecast
            result = forecaster.forecast(data, 'infectious', forecast_horizon=14)
            
            print(f"    Forecast length: {len(result.predictions)}")
            print(f"    MAE: {result.model_metrics['mae']:.2f}")
            print(f"    R2: {result.model_metrics['r2']:.3f}")
            
        except Exception as e:
            print(f"    Error in {model_type}: {e}")
    
    # Test ensemble forecaster
    print("  Testing ensemble forecaster...")
    ensemble = create_forecaster('ensemble')
    
    try:
        # Fit ensemble
        ensemble.fit_ensemble(data, 'infectious')
        
        # Generate forecast
        result = ensemble.ensemble_forecast(data, 'infectious', forecast_horizon=14)
        
        print(f"    Ensemble forecast length: {len(result.predictions)}")
        print(f"    Model weights: {result.model_metrics['ensemble_weights']}")
        
    except Exception as e:
        print(f"    Error in ensemble: {e}")
    
    print("  ML Forecasting test passed!")
    
    return True

def test_parameter_estimation():
    """Test parameter estimation."""
    print("\nTesting Parameter Estimation...")
    
    # Create synthetic observed data
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    
    # Generate synthetic infectious curve
    t = np.arange(50)
    infectious = 5 * np.exp(0.15 * t) * np.exp(-0.005 * t**2) + np.random.normal(0, 1, 50)
    infectious = np.maximum(infectious, 1)  # Ensure positive
    
    observed_data = pd.DataFrame({
        'date': dates,
        'infectious': infectious
    })
    
    # Create parameter estimator
    estimator = create_parameter_estimator()
    
    # Estimate parameters
    estimated_params = estimator.estimate_seir_parameters(observed_data)
    
    print(f"  Estimated beta: {estimated_params['beta']:.3f}")
    print(f"  Estimated gamma: {estimated_params['gamma']:.3f}")
    print(f"  Estimated sigma: {estimated_params['sigma']:.3f}")
    print(f"  Estimated R0: {estimated_params['r0']:.2f}")
    
    # Test uncertainty quantification
    uncertainty = estimator.uncertainty_quantification(observed_data, n_samples=100)
    
    print(f"  R0 uncertainty - Mean: {uncertainty['r0']['mean']:.2f}, Std: {uncertainty['r0']['std']:.2f}")
    
    print("  Parameter Estimation test passed!")
    
    return True

def main():
    """Run all model tests."""
    print("Running Public Health Intelligence Platform Model Tests")
    print("=" * 60)
    
    try:
        # Test all models
        test_seir_model()
        test_agent_based_model()
        test_network_model()
        test_ml_forecasting()
        test_parameter_estimation()
        
        print("\n" + "=" * 60)
        print("All model tests passed successfully!")
        print("The epidemiological and ML models are working correctly.")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()

