"""
Authentication API routes.
"""

from flask import Blueprint, request, jsonify
from ..models.database import User, db, AuditLog
from ..auth import AuthManager
import re

auth_bp = Blueprint('auth', __name__)


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is valid"


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        role = data.get('role', 'analyst')
        
        # Validate input
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        is_valid, password_message = validate_password(password)
        if not is_valid:
            return jsonify({'error': password_message}), 400
        
        if role not in ['analyst', 'researcher', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username already exists'}), 409
            else:
                return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user
        user = User(
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log registration
        audit_log = AuditLog(
            user_id=user.id,
            action='user_registered',
            resource_type='user',
            resource_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        audit_log.set_details({'username': username, 'email': email, 'role': role})
        db.session.add(audit_log)
        db.session.commit()
        
        # Generate token
        token = AuthManager.generate_token(user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return token."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Authenticate user
        user = AuthManager.authenticate_user(username, password)
        
        if not user:
            # Log failed login attempt
            audit_log = AuditLog(
                action='login_failed',
                resource_type='user',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            audit_log.set_details({'username': username})
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate token
        token = AuthManager.generate_token(user.id)
        
        # Log successful login
        audit_log = AuditLog(
            user_id=user.id,
            action='login_success',
            resource_type='user',
            resource_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh JWT token."""
    try:
        data = request.get_json()
        old_token = data.get('token')
        
        if not old_token:
            return jsonify({'error': 'Token is required'}), 400
        
        # Verify old token
        payload = AuthManager.verify_token(old_token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Generate new token
        new_token = AuthManager.generate_token(user.id)
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'token': new_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Token refresh failed: {str(e)}'}), 500


@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """Verify JWT token and return user info."""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        # Verify token
        user = AuthManager.get_current_user(token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        return jsonify({
            'message': 'Token is valid',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Token verification failed: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (client-side token removal)."""
    try:
        # In a JWT-based system, logout is typically handled client-side
        # by removing the token. We can log the logout event for audit purposes.
        
        data = request.get_json()
        token = data.get('token')
        
        if token:
            user = AuthManager.get_current_user(token)
            if user:
                # Log logout
                audit_log = AuditLog(
                    user_id=user.id,
                    action='logout',
                    resource_type='user',
                    resource_id=user.id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                db.session.commit()
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        token = data.get('token')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Validate required fields
        if not all([token, current_password, new_password]):
            return jsonify({'error': 'Token, current password, and new password are required'}), 400
        
        # Get current user
        user = AuthManager.get_current_user(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        is_valid, password_message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': password_message}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Log password change
        audit_log = AuditLog(
            user_id=user.id,
            action='password_changed',
            resource_type='user',
            resource_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Password change failed: {str(e)}'}), 500

