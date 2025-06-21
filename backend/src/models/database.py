"""
Database models for the public health intelligence platform.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='analyst')  # analyst, admin, researcher
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    simulations = db.relationship('Simulation', backref='user', lazy=True)
    datasets = db.relationship('Dataset', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class Dataset(db.Model):
    """Dataset model for storing epidemiological data."""
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    data_type = db.Column(db.String(50), nullable=False)  # time_series, cross_sectional, spatial
    source = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500))
    dataset_metadata = db.Column(db.Text)  # JSON string - renamed from metadata
    is_validated = db.Column(db.Boolean, default=False)
    validation_errors = db.Column(db.Text)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    data_points = db.relationship('DataPoint', backref='dataset', lazy=True, cascade='all, delete-orphan')
    simulations = db.relationship('Simulation', backref='dataset', lazy=True)
    
    def set_metadata(self, metadata_dict):
        """Set metadata as JSON string."""
        self.dataset_metadata = json.dumps(metadata_dict)
    
    def get_metadata(self):
        """Get metadata as dictionary."""
        if self.dataset_metadata:
            return json.loads(self.dataset_metadata)
        return {}
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'data_type': self.data_type,
            'source': self.source,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'metadata': self.get_metadata(),
            'is_validated': self.is_validated,
            'validation_errors': self.validation_errors,
            'user_id': self.user_id,
            # Improvement: Add the record count directly to the model's dictionary representation.
            'record_count': len(self.data_points)
        }


class DataPoint(db.Model):
    """Individual data points for time series and spatial data."""
    __tablename__ = 'data_points'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))  # Geographic location
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Epidemiological data fields
    susceptible = db.Column(db.Integer)
    exposed = db.Column(db.Integer)
    infectious = db.Column(db.Integer)
    recovered = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    new_cases = db.Column(db.Integer)
    new_deaths = db.Column(db.Integer)
    
    # Additional metrics
    population = db.Column(db.Integer)
    test_positivity_rate = db.Column(db.Float)
    hospitalization_rate = db.Column(db.Float)
    
    # Custom data fields (JSON)
    custom_data = db.Column(db.Text)
    
    # Foreign keys
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    
    def set_custom_data(self, data_dict):
        """Set custom data as JSON string."""
        self.custom_data = json.dumps(data_dict)
    
    def get_custom_data(self):
        """Get custom data as dictionary."""
        if self.custom_data:
            return json.loads(self.custom_data)
        return {}
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'susceptible': self.susceptible,
            'exposed': self.exposed,
            'infectious': self.infectious,
            'recovered': self.recovered,
            'deaths': self.deaths,
            'new_cases': self.new_cases,
            'new_deaths': self.new_deaths,
            'population': self.population,
            'test_positivity_rate': self.test_positivity_rate,
            'hospitalization_rate': self.hospitalization_rate,
            'custom_data': self.get_custom_data(),
            'dataset_id': self.dataset_id
        }


class Simulation(db.Model):
    """Simulation model for storing model runs and results."""
    __tablename__ = 'simulations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    model_type = db.Column(db.String(50), nullable=False)  # seir, agent_based, network, ml_forecast
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Parameters and results (JSON)
    parameters = db.Column(db.Text)  # Model parameters
    results = db.Column(db.Text)     # Simulation results
    metrics = db.Column(db.Text)     # Performance metrics
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'))
    
    # Relationships
    forecasts = db.relationship('Forecast', backref='simulation', lazy=True, cascade='all, delete-orphan')
    
    def set_parameters(self, params_dict):
        """Set parameters as JSON string."""
        self.parameters = json.dumps(params_dict)
    
    def get_parameters(self):
        """Get parameters as dictionary."""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def set_results(self, results_dict):
        """Set results as JSON string."""
        self.results = json.dumps(results_dict)
    
    def get_results(self):
        """Get results as dictionary."""
        if self.results:
            return json.loads(self.results)
        return {}
    
    def set_metrics(self, metrics_dict):
        """Set metrics as JSON string."""
        self.metrics = json.dumps(metrics_dict)
    
    def get_metrics(self):
        """Get metrics as dictionary."""
        if self.metrics:
            return json.loads(self.metrics)
        return {}
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model_type': self.model_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'parameters': self.get_parameters(),
            'results': self.get_results(),
            'metrics': self.get_metrics(),
            'user_id': self.user_id,
            'dataset_id': self.dataset_id
        }


class Forecast(db.Model):
    """Forecast model for storing prediction results."""
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_date = db.Column(db.DateTime, nullable=False)
    target_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    
    # Forecast values
    predicted_value = db.Column(db.Float, nullable=False)
    lower_bound = db.Column(db.Float)
    upper_bound = db.Column(db.Float)
    confidence_level = db.Column(db.Float, default=0.95)
    
    # Forecast metadata
    forecast_type = db.Column(db.String(50))  # cases, deaths, hospitalizations
    model_version = db.Column(db.String(50))
    
    # Foreign keys
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'location': self.location,
            'predicted_value': self.predicted_value,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'confidence_level': self.confidence_level,
            'forecast_type': self.forecast_type,
            'model_version': self.model_version,
            'simulation_id': self.simulation_id
        }


class ModelComparison(db.Model):
    """Model comparison results for ensemble analysis."""
    __tablename__ = 'model_comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    comparison_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Comparison results (JSON)
    comparison_results = db.Column(db.Text)
    performance_metrics = db.Column(db.Text)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def set_comparison_results(self, results_dict):
        """Set comparison results as JSON string."""
        self.comparison_results = json.dumps(results_dict)
    
    def get_comparison_results(self):
        """Get comparison results as dictionary."""
        if self.comparison_results:
            return json.loads(self.comparison_results)
        return {}
    
    def set_performance_metrics(self, metrics_dict):
        """Set performance metrics as JSON string."""
        self.performance_metrics = json.dumps(metrics_dict)
    
    def get_performance_metrics(self):
        """Get performance metrics as dictionary."""
        if self.performance_metrics:
            return json.loads(self.performance_metrics)
        return {}
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'comparison_name': self.comparison_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'comparison_results': self.get_comparison_results(),
            'performance_metrics': self.get_performance_metrics(),
            'user_id': self.user_id
        }


class AuditLog(db.Model):
    """Audit log for tracking user actions and system events."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    def set_details(self, details_dict):
        """Set details as JSON string."""
        self.details = json.dumps(details_dict)
    
    def get_details(self):
        """Get details as dictionary."""
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.get_details(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }