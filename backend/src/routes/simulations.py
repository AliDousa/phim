"""
Simulation management API routes.
"""

from flask import Blueprint, request, jsonify
from src.models.database import Simulation, Dataset, Forecast, User, db, AuditLog
from src.models.epidemiological import create_seir_model, create_agent_based_model, create_network_model
from src.models.ml_forecasting import create_forecaster, create_parameter_estimator
from src.auth import token_required, PermissionManager
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import threading
import time

simulations_bp = Blueprint('simulations', __name__)


def run_simulation_async(simulation_id):
    """Run simulation asynchronously in background."""
    from src.main import app
    
    with app.app_context():
        try:
            simulation = Simulation.query.get(simulation_id)
            if not simulation:
                return
            
            # Update status to running
            simulation.status = 'running'
            simulation.started_at = datetime.utcnow()
            db.session.commit()
            
            # Get parameters
            params = simulation.get_parameters()
            model_type = simulation.model_type
            
            # Run the appropriate model
            if model_type == 'seir':
                results = run_seir_simulation(simulation, params)
            elif model_type == 'agent_based':
                results = run_agent_based_simulation(simulation, params)
            elif model_type == 'network':
                results = run_network_simulation(simulation, params)
            elif model_type == 'ml_forecast':
                results = run_ml_forecast_simulation(simulation, params)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Save results
            simulation.set_results(results)
            simulation.status = 'completed'
            simulation.completed_at = datetime.utcnow()
            
            # Calculate and save metrics
            metrics = calculate_simulation_metrics(results, model_type)
            simulation.set_metrics(metrics)
            
            db.session.commit()
            
        except Exception as e:
            # Update status to failed
            simulation.status = 'failed'
            simulation.completed_at = datetime.utcnow()
            error_results = {'error': str(e), 'traceback': str(e)}
            simulation.set_results(error_results)
            db.session.commit()


def run_seir_simulation(simulation, params):
    """Run SEIR model simulation."""
    # Create SEIR model
    model = create_seir_model(params)
    
    # Set up simulation parameters
    time_points = np.linspace(0, params.get('time_horizon', 365), params.get('time_steps', 365))
    initial_conditions = params.get('initial_conditions', {
        'S': params.get('population', 100000) - 1,
        'E': 0,
        'I': 1,
        'R': 0
    })
    
    # Run simulation
    results = model.simulate(initial_conditions, time_points)
    
    # Calculate additional metrics
    r0 = model.calculate_r0()
    peak_time, peak_infections = model.calculate_peak_infection(initial_conditions)
    
    return {
        'time': results.time.tolist(),
        'susceptible': results.susceptible.tolist(),
        'exposed': results.exposed.tolist(),
        'infectious': results.infectious.tolist(),
        'recovered': results.recovered.tolist(),
        'r0': r0,
        'peak_time': peak_time,
        'peak_infections': peak_infections,
        'model_type': 'seir',
        'parameters': results.parameters
    }


def run_agent_based_simulation(simulation, params):
    """Run agent-based model simulation."""
    # Create agent-based model
    model = create_agent_based_model(params)
    
    # Run simulation
    time_steps = params.get('time_steps', 100)
    results = model.simulate(time_steps)
    
    return {
        'time': results['time'],
        'susceptible': results['S'],
        'exposed': results['E'],
        'infectious': results['I'],
        'recovered': results['R'],
        'model_type': 'agent_based',
        'parameters': params
    }


def run_network_simulation(simulation, params):
    """Run network-based model simulation."""
    # Create network model
    model = create_network_model(params)
    
    # Create network
    num_nodes = params.get('population_size', 1000)
    model.create_network(num_nodes)
    
    # Run simulation
    time_steps = params.get('time_steps', 100)
    transmission_rate = params.get('transmission_rate', 0.1)
    recovery_rate = params.get('recovery_rate', 0.1)
    
    results = model.simulate_transmission(transmission_rate, recovery_rate, time_steps)
    
    return {
        'time': results['time'],
        'susceptible': results['S'],
        'infectious': results['I'],
        'recovered': results['R'],
        'model_type': 'network',
        'parameters': params
    }


def run_ml_forecast_simulation(simulation, params):
    """Run machine learning forecasting simulation."""
    # Get dataset if specified
    dataset_id = simulation.dataset_id
    if not dataset_id:
        raise ValueError("ML forecasting requires a dataset")
    
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        raise ValueError("Dataset not found")
    
    # Get data points and convert to DataFrame
    from src.models.database import DataPoint
    data_points = DataPoint.query.filter_by(dataset_id=dataset_id).order_by(DataPoint.timestamp).all()
    
    if not data_points:
        raise ValueError("Dataset contains no data points")
    
    # Convert to DataFrame
    data_list = []
    for dp in data_points:
        data_list.append({
            'date': dp.timestamp,
            'infectious': dp.infectious or 0,
            'new_cases': dp.new_cases or 0,
            'deaths': dp.deaths or 0
        })
    
    df = pd.DataFrame(data_list)
    
    # Create forecaster
    model_type = params.get('ml_model_type', 'ensemble')
    forecaster = create_forecaster(model_type)
    
    # Run forecast
    target_col = params.get('target_column', 'infectious')
    forecast_horizon = params.get('forecast_horizon', 30)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")
    
    forecast_result = forecaster.forecast(df, target_col, forecast_horizon)
    
    # Save forecasts to database
    forecast_date = datetime.utcnow()
    for i, prediction in enumerate(forecast_result.predictions):
        target_date = forecast_date + timedelta(days=i+1)
        
        forecast = Forecast(
            simulation_id=simulation.id,
            forecast_date=forecast_date,
            target_date=target_date,
            predicted_value=float(prediction),
            forecast_type=target_col,
            model_version='1.0'
        )
        
        if forecast_result.confidence_intervals:
            forecast.lower_bound = float(forecast_result.confidence_intervals[0][i])
            forecast.upper_bound = float(forecast_result.confidence_intervals[1][i])
        
        db.session.add(forecast)
    
    db.session.commit()
    
    return {
        'predictions': forecast_result.predictions.tolist(),
        'confidence_intervals': {
            'lower': forecast_result.confidence_intervals[0].tolist() if forecast_result.confidence_intervals else None,
            'upper': forecast_result.confidence_intervals[1].tolist() if forecast_result.confidence_intervals else None
        },
        'metrics': forecast_result.model_metrics,
        'feature_importance': forecast_result.feature_importance,
        'model_type': 'ml_forecast',
        'parameters': params
    }


def calculate_simulation_metrics(results, model_type):
    """Calculate performance metrics for simulation results."""
    metrics = {}
    
    if model_type in ['seir', 'agent_based', 'network']:
        # Calculate basic epidemiological metrics
        if 'infectious' in results:
            infectious = np.array(results['infectious'])
            metrics['max_infections'] = float(np.max(infectious))
            metrics['total_infections'] = float(np.sum(infectious))
            metrics['peak_day'] = int(np.argmax(infectious))
        
        if 'recovered' in results:
            recovered = np.array(results['recovered'])
            metrics['final_recovered'] = float(recovered[-1]) if len(recovered) > 0 else 0
        
        if 'r0' in results:
            metrics['r0'] = results['r0']
    
    elif model_type == 'ml_forecast':
        # ML-specific metrics are already included in results
        if 'metrics' in results:
            metrics.update(results['metrics'])
    
    metrics['simulation_duration'] = len(results.get('time', []))
    metrics['calculated_at'] = datetime.utcnow().isoformat()
    
    return metrics


@simulations_bp.route('/', methods=['GET'])
@token_required
def get_simulations():
    """Get all simulations for the current user."""
    try:
        user = request.current_user
        
        # Admin can see all simulations, others see only their own
        if user.role == 'admin':
            simulations = Simulation.query.all()
        else:
            simulations = Simulation.query.filter_by(user_id=user.id).all()
        
        return jsonify({
            'simulations': [sim.to_dict() for sim in simulations]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve simulations: {str(e)}'}), 500


@simulations_bp.route('/<int:simulation_id>', methods=['GET'])
@token_required
def get_simulation(simulation_id):
    """Get specific simulation by ID."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_simulation(user, simulation_id):
            return jsonify({'error': 'Access denied'}), 403
        
        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return jsonify({'error': 'Simulation not found'}), 404
        
        return jsonify({'simulation': simulation.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve simulation: {str(e)}'}), 500


@simulations_bp.route('/', methods=['POST'])
@token_required
def create_simulation():
    """Create and run a new simulation."""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'model_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate model_type
        valid_model_types = ['seir', 'agent_based', 'network', 'ml_forecast']
        if data['model_type'] not in valid_model_types:
            return jsonify({'error': f'model_type must be one of: {valid_model_types}'}), 400
        
        # Validate dataset access if specified
        dataset_id = data.get('dataset_id')
        if dataset_id:
            if not PermissionManager.can_access_dataset(user, dataset_id):
                return jsonify({'error': 'Access denied to specified dataset'}), 403
        
        # Create simulation
        simulation = Simulation(
            name=data['name'],
            description=data.get('description', ''),
            model_type=data['model_type'],
            user_id=user.id,
            dataset_id=dataset_id
        )
        
        # Set parameters
        parameters = data.get('parameters', {})
        simulation.set_parameters(parameters)
        
        db.session.add(simulation)
        db.session.commit()
        
        # Log simulation creation
        audit_log = AuditLog(
            user_id=user.id,
            action='simulation_created',
            resource_type='simulation',
            resource_id=simulation.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        audit_log.set_details({
            'simulation_name': simulation.name,
            'model_type': simulation.model_type
        })
        db.session.add(audit_log)
        db.session.commit()
        
        # Start simulation in background thread
        thread = threading.Thread(target=run_simulation_async, args=(simulation.id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Simulation created and started',
            'simulation': simulation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create simulation: {str(e)}'}), 500


@simulations_bp.route('/<int:simulation_id>', methods=['DELETE'])
@token_required
def delete_simulation(simulation_id):
    """Delete simulation and all associated data."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_simulation(user, simulation_id):
            return jsonify({'error': 'Access denied'}), 403
        
        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return jsonify({'error': 'Simulation not found'}), 404
        
        # Don't allow deletion of running simulations
        if simulation.status == 'running':
            return jsonify({'error': 'Cannot delete running simulation'}), 400
        
        # Log simulation deletion before deleting
        audit_log = AuditLog(
            user_id=user.id,
            action='simulation_deleted',
            resource_type='simulation',
            resource_id=simulation.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        audit_log.set_details({'simulation_name': simulation.name})
        db.session.add(audit_log)
        
        # Delete simulation (cascade will delete forecasts)
        db.session.delete(simulation)
        db.session.commit()
        
        return jsonify({'message': 'Simulation deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete simulation: {str(e)}'}), 500


@simulations_bp.route('/<int:simulation_id>/forecasts', methods=['GET'])
@token_required
def get_simulation_forecasts(simulation_id):
    """Get forecasts for a simulation."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_simulation(user, simulation_id):
            return jsonify({'error': 'Access denied'}), 403
        
        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return jsonify({'error': 'Simulation not found'}), 404
        
        # Get forecasts
        forecasts = Forecast.query.filter_by(simulation_id=simulation_id).order_by(Forecast.target_date).all()
        
        return jsonify({
            'forecasts': [forecast.to_dict() for forecast in forecasts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve forecasts: {str(e)}'}), 500


@simulations_bp.route('/compare', methods=['POST'])
@token_required
def compare_simulations():
    """Compare multiple simulations."""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        if 'simulation_ids' not in data or not isinstance(data['simulation_ids'], list):
            return jsonify({'error': 'simulation_ids array is required'}), 400
        
        simulation_ids = data['simulation_ids']
        if len(simulation_ids) < 2:
            return jsonify({'error': 'At least 2 simulations required for comparison'}), 400
        
        # Check permissions for all simulations
        simulations = []
        for sim_id in simulation_ids:
            if not PermissionManager.can_access_simulation(user, sim_id):
                return jsonify({'error': f'Access denied to simulation {sim_id}'}), 403
            
            simulation = Simulation.query.get(sim_id)
            if not simulation:
                return jsonify({'error': f'Simulation {sim_id} not found'}), 404
            
            if simulation.status != 'completed':
                return jsonify({'error': f'Simulation {sim_id} is not completed'}), 400
            
            simulations.append(simulation)
        
        # Perform comparison
        comparison_results = {}
        
        for simulation in simulations:
            results = simulation.get_results()
            metrics = simulation.get_metrics()
            
            comparison_results[simulation.id] = {
                'name': simulation.name,
                'model_type': simulation.model_type,
                'results': results,
                'metrics': metrics
            }
        
        # Calculate comparative metrics
        comparative_metrics = {}
        
        # Compare peak infections if available
        peak_infections = {}
        for sim_id, data in comparison_results.items():
            if 'max_infections' in data['metrics']:
                peak_infections[sim_id] = data['metrics']['max_infections']
        
        if peak_infections:
            comparative_metrics['peak_infections'] = peak_infections
            comparative_metrics['highest_peak'] = max(peak_infections, key=peak_infections.get)
            comparative_metrics['lowest_peak'] = min(peak_infections, key=peak_infections.get)
        
        # Compare R0 values if available
        r0_values = {}
        for sim_id, data in comparison_results.items():
            if 'r0' in data['metrics']:
                r0_values[sim_id] = data['metrics']['r0']
        
        if r0_values:
            comparative_metrics['r0_values'] = r0_values
        
        return jsonify({
            'comparison_results': comparison_results,
            'comparative_metrics': comparative_metrics,
            'compared_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Comparison failed: {str(e)}'}), 500

