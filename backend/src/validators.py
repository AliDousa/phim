"""
Input validation decorators and utilities for the Public Health Intelligence Platform.
"""

import json
import re
from functools import wraps
from flask import request, jsonify
from typing import Dict, Any, List, Optional


def validate_json_input(required_fields: List[str] = None, optional_fields: List[str] = None):
    """
    Decorator to validate JSON input for API endpoints.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            try:
                data = request.get_json()
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON format"}), 400
            
            if data is None:
                return jsonify({"error": "No JSON data provided"}), 400
            
            if not isinstance(data, dict):
                return jsonify({"error": "JSON data must be an object"}), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        "error": f"Missing required fields: {', '.join(missing_fields)}"
                    }), 400
            
            # Check for empty required fields
            if required_fields:
                empty_fields = [
                    field for field in required_fields 
                    if field in data and (data[field] is None or data[field] == "")
                ]
                if empty_fields:
                    return jsonify({
                        "error": f"Required fields cannot be empty: {', '.join(empty_fields)}"
                    }), 400
            
            # Check for unexpected fields
            all_allowed_fields = (required_fields or []) + (optional_fields or [])
            if all_allowed_fields:
                unexpected_fields = [field for field in data.keys() if field not in all_allowed_fields]
                if unexpected_fields:
                    return jsonify({
                        "error": f"Unexpected fields: {', '.join(unexpected_fields)}"
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_query_params(allowed_params: List[str] = None, required_params: List[str] = None):
    """
    Decorator to validate query parameters.
    
    Args:
        allowed_params: List of allowed parameter names
        required_params: List of required parameter names
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check required parameters
            if required_params:
                missing_params = [param for param in required_params if param not in request.args]
                if missing_params:
                    return jsonify({
                        "error": f"Missing required query parameters: {', '.join(missing_params)}"
                    }), 400
            
            # Check for unexpected parameters
            if allowed_params:
                unexpected_params = [param for param in request.args.keys() if param not in allowed_params]
                if unexpected_params:
                    return jsonify({
                        "error": f"Unexpected query parameters: {', '.join(unexpected_params)}"
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_pagination_params(max_per_page: int = 100):
    """
    Decorator to validate pagination parameters.
    
    Args:
        max_per_page: Maximum allowed items per page
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 20, type=int)
                
                if page < 1:
                    return jsonify({"error": "Page number must be positive"}), 400
                
                if per_page < 1:
                    return jsonify({"error": "Items per page must be positive"}), 400
                
                if per_page > max_per_page:
                    return jsonify({
                        "error": f"Items per page cannot exceed {max_per_page}"
                    }), 400
                
            except ValueError:
                return jsonify({"error": "Page and per_page must be valid integers"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_email_format(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    # Check for common weak passwords
    weak_passwords = [
        "password", "123456", "password123", "admin", "qwerty",
        "letmein", "welcome", "monkey", "1234567890"
    ]
    if password.lower() in weak_passwords:
        return False, "Password is too common and weak"
    
    return True, "Password is valid"


def validate_username_format(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 80:
        return False, "Username must be less than 80 characters"
    
    # Allow letters, numbers, underscores, and hyphens
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    # Username cannot start or end with special characters
    if username.startswith(('-', '_')) or username.endswith(('-', '_')):
        return False, "Username cannot start or end with special characters"
    
    # Username cannot be all numbers
    if username.isdigit():
        return False, "Username cannot be all numbers"
    
    return True, "Username is valid"


def sanitize_string_input(input_string: str, max_length: int = 1000) -> str:
    """
    Sanitize string input by removing dangerous characters and limiting length.
    
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(input_string, str):
        return ""
    
    # Remove null bytes and control characters
    sanitized = input_string.replace('\x00', '').replace('\r', '').replace('\n', ' ')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    return sanitized


def validate_file_upload(allowed_extensions: set = None, max_size: int = None):
    """
    Decorator to validate file uploads.
    
    Args:
        allowed_extensions: Set of allowed file extensions
        max_size: Maximum file size in bytes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files['file']
            
            if not file or not file.filename:
                return jsonify({"error": "No file selected"}), 400
            
            # Check file extension
            if allowed_extensions:
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if not file_ext or file_ext not in allowed_extensions:
                    return jsonify({
                        "error": f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
                    }), 400
            
            # Check file size
            if max_size and hasattr(file, 'content_length') and file.content_length:
                if file.content_length > max_size:
                    return jsonify({
                        "error": f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB"
                    }), 413
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code