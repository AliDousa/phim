"""
Authentication and authorization utilities.
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

from src.models.database import User, db, Dataset, Simulation
from src.security import AuthenticationSecurity


class AuthManager:
    """Authentication and authorization manager."""

    @staticmethod
    def generate_token(user_id: int) -> str:
        """Generate JWT access token for user."""
        # Delegate to the more secure token generator
        auth_sec = AuthenticationSecurity(current_app)
        return auth_sec.generate_secure_token(user_id, token_type="access")

    @staticmethod
    def generate_refresh_token(user_id: int) -> str:
        """Generate JWT refresh token for user."""
        auth_sec = AuthenticationSecurity(current_app)
        return auth_sec.generate_secure_token(user_id, token_type="refresh")

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token and return payload."""
        # Delegate to the more secure token verifier
        auth_sec = AuthenticationSecurity(current_app)
        return auth_sec.verify_secure_token(token)

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
        try:
            auth_sec = AuthenticationSecurity(current_app)

            # Check for brute-force attempts before hitting the DB
            is_blocked = auth_sec.check_failed_logins(username)
            if is_blocked:
                current_app.logger.warning(f"Login blocked for user {username} due to failed attempts")
                return None  # Account is temporarily locked

            # Try to find user by username or email
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()

            if user:
                password_ok = user.check_password(password)
                if password_ok and user.is_active:
                    auth_sec.clear_failed_logins(username)
                    current_app.logger.info(f"Successful login for user {username}")
                    return user
                else:
                    current_app.logger.warning(f"Failed login for user {username}: invalid credentials or inactive account")

            auth_sec.record_failed_login(username)
            return None
        except Exception as e:
            # Log error in production, for now return None
            current_app.logger.error(f"Authentication error for user {username}: {e}")
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
        try:
            payload = AuthManager.verify_token(token)
            if payload:
                user = User.query.get(payload["user_id"])
                if user and user.is_active:
                    return user
            return None
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            current_app.logger.warning(
                f"Token verification failed during get_current_user: {e}"
            )
            return None


def token_required(f):
    """
    Decorator to require valid JWT token for API endpoints.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
            else:
                return jsonify({"error": "Invalid authorization header format"}), 401

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        # Verify token
        payload = AuthManager.verify_token(token)
        if not payload:
            return jsonify({"error": "Token is invalid or expired"}), 401

        # Get current user from payload
        current_user = AuthManager.get_current_user(token)
        if not current_user:
            return jsonify({"error": "User not found or inactive"}), 401

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
        if not hasattr(request, "current_user") or request.current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403

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
            if (
                not hasattr(request, "current_user")
                or request.current_user.role not in allowed_roles
            ):
                return (
                    jsonify(
                        {"error": f"Access denied. Required roles: {allowed_roles}"}
                    ),
                    403,
                )

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
        try:
            if user.role == "admin":
                return True

            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                return False

            # Users can access their own datasets
            return dataset.user_id == user.id
        except Exception as e:
            current_app.logger.error(
                f"Error checking dataset permission for user {user.id} on dataset {dataset_id}: {e}"
            )
            return False

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
        try:
            if user.role == "admin":
                return True

            simulation = Simulation.query.get(simulation_id)
            if not simulation:
                return False

            # Users can access their own simulations
            return simulation.user_id == user.id
        except Exception as e:
            current_app.logger.error(
                f"Error checking simulation permission for user {user.id} on simulation {simulation_id}: {e}"
            )
            return False

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
        try:
            if current_user.role == "admin":
                return True

            # Users can modify themselves
            return current_user.id == target_user_id
        except Exception as e:
            current_app.logger.error(
                f"Error checking user modification permission for user {current_user.id} on target {target_user_id}: {e}"
            )
            return False
