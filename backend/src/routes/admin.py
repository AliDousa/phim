"""
Admin-only API routes for user and system management.
"""

from flask import Blueprint, request, jsonify, current_app

from src.models.database import User, db, AuditLog
from src.auth import admin_required
from src.security import validate_json_input, InputSanitizer, SecurityException

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """List all users in the system."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        users_paginated = User.query.order_by(User.id).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            "users": [user.to_dict(include_sensitive=True) for user in users_paginated.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": users_paginated.total,
                "pages": users_paginated.pages,
            },
        }), 200
    except Exception as e:
        current_app.logger.error(f"Admin list users failed: {e}")
        return jsonify({"error": "Failed to retrieve users"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user_details(user_id):
    """Get detailed information for a specific user."""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(include_sensitive=True)), 200


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
@validate_json_input(optional_fields=["email", "role", "is_active"])
def update_user_by_admin(user_id):
    """Update a user's details (role, status, etc.)."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        updated_fields = []

        if "email" in data:
            email = InputSanitizer.sanitize_string(data["email"]).lower()
            if not InputSanitizer.validate_email(email):
                raise SecurityException("Invalid email format", 400)
            
            existing = User.query.filter(User.email == email, User.id != user_id).first()
            if existing:
                return jsonify({"error": f"Email '{email}' is already in use."}), 409
            
            user.email = email
            updated_fields.append("email")

        if "role" in data:
            role = InputSanitizer.sanitize_string(data["role"])
            if role not in ["admin", "researcher", "analyst"]:
                raise SecurityException("Invalid role specified", 400)
            user.role = role
            updated_fields.append("role")

        if "is_active" in data:
            if not isinstance(data["is_active"], bool):
                raise SecurityException("is_active must be a boolean", 400)
            user.is_active = data["is_active"]
            updated_fields.append("is_active")

        if not updated_fields:
            return jsonify({"message": "No fields to update"}), 200

        db.session.commit()

        # Audit log
        audit_log = AuditLog(
            user_id=request.current_user.id,
            action="admin_user_update",
            resource_type="user",
            resource_id=user.id,
            ip_address=request.remote_addr,
        )
        audit_log.set_details({"updated_fields": updated_fields, "new_values": data})
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({
            "message": "User updated successfully",
            "user": user.to_dict(include_sensitive=True)
        }), 200

    except SecurityException as se:
        return jsonify({"error": se.message}), se.status_code
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin update user failed: {e}")
        return jsonify({"error": "Failed to update user"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user_by_admin(user_id):
    """Delete a user from the system."""
    user = User.query.get_or_404(user_id)
    # Add logic to prevent self-deletion or deletion of critical accounts
    if user.id == request.current_user.id:
        return jsonify({"error": "Cannot delete your own account via admin API"}), 403
    
    db.session.delete(user)
    db.session.commit()
    return '', 204