"""
Authentication and authorization utilities.
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from src.models.database import User, db


class AuthManager:
    """Authentication and authorization manager."""
    
    @staticmethod
    def generate_token(user_id: int, expires_in: int = 3600) -> str:
        """
        Generate JWT token for user.
        
        Args:
            user_id: User ID
            expires_in: Token expiration time in seconds
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> User:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            User object if authenticated, None otherwise
        """
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password) and user.is_active:
            return user
        
        return None
    
    @staticmethod
    def get_current_user(token: str) -> User:
        """
        Get current user from token.
        
        Args:
            token: JWT token
            
        Returns:
            User object or None
        """
        payload = AuthManager.verify_token(token)
        if payload:
            user = User.query.get(payload['user_id'])
            if user and user.is_active:
                return user
        
        return None


def token_required(f):
    """
    Decorator to require valid JWT token for API endpoints.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Verify token
        payload = AuthManager.verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Get current user
        current_user = User.query.get(payload['user_id'])
        if not current_user or not current_user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Add current user to request context
        request.current_user = current_user
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator to require admin role for API endpoints.
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated


def role_required(allowed_roles):
    """
    Decorator to require specific roles for API endpoints.
    
    Args:
        allowed_roles: List of allowed roles
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.current_user.role not in allowed_roles:
                return jsonify({'error': f'Access denied. Required roles: {allowed_roles}'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


class PermissionManager:
    """Permission management for resources."""
    
    @staticmethod
    def can_access_dataset(user: User, dataset_id: int) -> bool:
        """
        Check if user can access dataset.
        
        Args:
            user: User object
            dataset_id: Dataset ID
            
        Returns:
            True if user can access dataset
        """
        from src.models.database import Dataset
        
        if user.role == 'admin':
            return True
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return False
        
        # Users can access their own datasets
        return dataset.user_id == user.id
    
    @staticmethod
    def can_access_simulation(user: User, simulation_id: int) -> bool:
        """
        Check if user can access simulation.
        
        Args:
            user: User object
            simulation_id: Simulation ID
            
        Returns:
            True if user can access simulation
        """
        from src.models.database import Simulation
        
        if user.role == 'admin':
            return True
        
        simulation = Simulation.query.get(simulation_id)
        if not simulation:
            return False
        
        # Users can access their own simulations
        return simulation.user_id == user.id
    
    @staticmethod
    def can_modify_user(current_user: User, target_user_id: int) -> bool:
        """
        Check if user can modify another user.
        
        Args:
            current_user: Current user
            target_user_id: Target user ID
            
        Returns:
            True if user can modify target user
        """
        if current_user.role == 'admin':
            return True
        
        # Users can modify themselves
        return current_user.id == target_user_id

