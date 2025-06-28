"""
Authentication API routes.
"""

from flask import Blueprint, request, jsonify
import re  # Keep re import

# Import with fallback for different execution contexts
from src.models.database import User, db, AuditLog
from src.auth import AuthManager
from src.validators import (
    validate_json_input,
    validate_email_format,
    validate_password_strength,
    validate_username_format,
)
from src.auth import token_required

auth_bp = Blueprint("auth", __name__)


# Validation functions moved to src/validators.py
# Keep aliases for backward compatibility with original interface
def validate_email(email):
    """Validate email format - original interface."""
    return validate_email_format(email)


def validate_password(password):
    """Validate password strength - original interface."""
    return validate_password_strength(password)


def validate_username(username):
    """Validate username format - original interface."""
    return validate_username_format(username)


@auth_bp.route("/register", methods=["POST"])
@validate_json_input(
    required_fields=["username", "email", "password"], optional_fields=["role"]
)
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"{field} is required"}), 400

        username = data["username"].strip()
        email = data["email"].strip().lower()
        password = data["password"]
        role = data.get("role", "analyst")

        # Validate input
        is_valid_username, username_message = validate_username(username)
        if not is_valid_username:
            return jsonify({"error": username_message}), 400

        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({"error": password_message}), 400

        # Validate role
        valid_roles = ["analyst", "researcher", "admin"]
        if role not in valid_roles:
            return (
                jsonify(
                    {"error": f'Invalid role. Must be one of: {", ".join(valid_roles)}'}
                ),
                400,
            )

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                return jsonify({"error": "Username already exists"}), 409
            else:
                return jsonify({"error": "Email already exists"}), 409

        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Log registration
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="user_registered",
                resource_type="user",
                resource_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            audit_log.set_details({"username": username, "email": email, "role": role})
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:  # Catch specific exceptions if possible
            # Log the audit failure, but don't prevent user registration
            from flask import (
                current_app,
            )  # Import current_app here to avoid circular dependency if not already imported

            current_app.logger.error(f"Audit logging failed for user registration: {e}")

        # Generate token
        token = AuthManager.generate_token(user.id)

        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "user": user.to_dict(),
                    "token": token,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
@validate_json_input(required_fields=["username", "password"])
def login():
    """Authenticate user and return token."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        if not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400

        username = data["username"].strip()
        password = data["password"]

        # Rate limiting could be added here

        # Authenticate user
        user = AuthManager.authenticate_user(username, password)

        if not user:
            # Log failed login attempt
            try:
                audit_log = AuditLog(
                    action="login_failed",
                    resource_type="user",
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent"),
                )
                audit_log.set_details({"username": username})
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:  # Catch specific exceptions if possible
                from flask import current_app

                current_app.logger.error(
                    f"Audit logging failed for failed login attempt: {e}"
                )

            return jsonify({"error": "Invalid credentials"}), 401

        # Generate token
        token = AuthManager.generate_token(user.id)

        # Log successful login
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="login_success",
                resource_type="user",
                resource_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:  # Catch specific exceptions if possible
            from flask import current_app

            current_app.logger.error(f"Audit logging failed for successful login: {e}")

        return (
            jsonify(
                {"message": "Login successful", "user": user.to_dict(), "token": token}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """Refresh JWT token."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        old_token = data.get("token")

        if not old_token:
            return jsonify({"error": "Token is required"}), 400

        # Verify old token
        payload = AuthManager.verify_token(old_token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Get user
        user = User.query.get(payload["user_id"])
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 401

        # Generate new token
        new_token = AuthManager.generate_token(user.id)

        return (
            jsonify(
                {
                    "message": "Token refreshed successfully",
                    "token": new_token,
                    "user": user.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500


@auth_bp.route("/verify", methods=["POST"])
def verify_token():
    """Verify JWT token and return user info."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        token = data.get("token")

        if not token:
            return jsonify({"error": "Token is required"}), 400

        # Verify token
        user = AuthManager.get_current_user(token)

        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401

        return jsonify({"message": "Token is valid", "user": user.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout user (client-side token removal)."""
    try:
        # In a JWT-based system, logout is typically handled client-side
        # by removing the token. We can log the logout event for audit purposes.

        data = request.get_json()
        token = data.get("token") if data else None

        if token:
            user = AuthManager.get_current_user(token)
            if user:
                try:
                    # Log logout
                    audit_log = AuditLog(
                        user_id=user.id,
                        action="logout",
                        resource_type="user",
                        resource_id=user.id,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get("User-Agent"),
                    )
                    db.session.add(audit_log)
                    db.session.commit()
                except Exception as e:  # Catch specific exceptions if possible
                    from flask import current_app

                    current_app.logger.error(f"Audit logging failed for logout: {e}")

        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        token = data.get("token")
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        # Validate required fields
        if not all([token, current_password, new_password]):
            return (
                jsonify(
                    {"error": "Token, current password, and new password are required"}
                ),
                400,
            )

        # Get current user
        user = AuthManager.get_current_user(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Verify current password
        if not user.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 400

        # Validate new password
        is_valid, password_message = validate_password(new_password)
        if not is_valid:
            return jsonify({"error": password_message}), 400

        # Check if new password is different from current
        if user.check_password(new_password):
            return (
                jsonify(
                    {"error": "New password must be different from current password"}
                ),
                400,
            )

        # Update password
        user.set_password(new_password)
        db.session.commit()

        # Log password change
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="password_changed",
                resource_type="user",
                resource_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:  # Catch specific exceptions if possible
            from flask import current_app

            current_app.logger.error(f"Audit logging failed for password change: {e}")

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Password change failed: {str(e)}"}), 500


@auth_bp.route("/profile", methods=["GET"])  # Re-apply previous diff
@token_required
def get_profile():
    """Get current user profile."""
    try:
        # The decorator has already set request.current_user
        user = request.current_user
        return jsonify({"user": user.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get profile: {str(e)}"}), 500


@auth_bp.route("/profile", methods=["PUT"])  # Re-apply previous diff
@token_required
def update_profile():
    """Update current user profile."""
    try:
        # The decorator has already set request.current_user
        user = request.current_user

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Update allowed fields
        if "email" in data:
            new_email = data["email"].strip().lower()
            if not validate_email(new_email):
                return jsonify({"error": "Invalid email format"}), 400

            # Check if email is already taken by another user
            existing_user = User.query.filter(
                User.email == new_email, User.id != user.id
            ).first()

            if existing_user:
                return jsonify({"error": "Email already taken"}), 409

            user.email = new_email

        # Note: Username and role changes might require admin approval in a real system

        db.session.commit()

        # Log profile update
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="profile_updated",
                resource_type="user",
                resource_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            audit_log.set_details({"updated_fields": list(data.keys())})
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:  # Catch specific exceptions if possible
            from flask import current_app

            current_app.logger.error(f"Audit logging failed for profile update: {e}")

        return (
            jsonify(
                {"message": "Profile updated successfully", "user": user.to_dict()}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Profile update failed: {str(e)}"}), 500
