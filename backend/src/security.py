"""
Security manager for the Public Health Intelligence Platform.
Handles authentication, authorization, input validation, and security headers.
"""

import os
import hashlib
import hmac
import time
import re
from functools import wraps
from flask import request, jsonify, current_app, g
import magic
import bleach
import json
from werkzeug.utils import secure_filename
import jwt
from datetime import datetime, timedelta

from typing import Dict, Any, List, Optional, Tuple
from src.models.database import User, AuditLog, db


class SecurityManager:
    """Centralized security management for the application."""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize security manager with Flask app."""
        self.app = app

        # Security configuration
        self.max_request_size = app.config.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)
        self.allowed_extensions = app.config.get(
            "ALLOWED_EXTENSIONS", {"csv", "json", "xlsx"}
        )
        self.allowed_mime_types = app.config.get("ALLOWED_MIME_TYPES", {})

        # Rate limiting thresholds
        self.failed_login_threshold = 5
        self.failed_login_window = 900  # 15 minutes

    def apply_security_headers(self):
        """Apply security headers to requests."""
        # This is called in before_request
        pass

    def apply_response_headers(self, response):
        """Apply security headers to responses."""
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS header for HTTPS
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy
        csp = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'"
        response.headers["Content-Security-Policy"] = csp

        # API versioning
        response.headers["X-API-Version"] = current_app.config.get("API_VERSION", "v1")

        return response

    def validate_request(self):
        """Validate incoming requests for security threats."""
        # Check request size
        if request.content_length and request.content_length > self.max_request_size:
            raise SecurityException("Request too large", 413)

        # Check for suspicious patterns in headers
        self._check_suspicious_headers()

        # Validate JSON content if present
        if request.is_json:
            self._validate_json_content()

    def _check_suspicious_headers(self):
        """Check for suspicious headers that might indicate attacks."""
        suspicious_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
        ]

        for header_name, header_value in request.headers:
            for pattern in suspicious_patterns:
                if re.search(pattern, header_value, re.IGNORECASE):
                    self._log_security_event(
                        "suspicious_header",
                        {
                            "header": header_name,
                            "value": header_value[:100],  # Truncate for logging
                            "pattern": pattern,
                        },
                    )

    def _validate_json_content(self):
        """Validate JSON content for potential threats."""
        try:
            data = request.get_json()
            if data:
                self._validate_json_recursively(data)
        except Exception:
            # Let the application handle JSON parsing errors
            pass

    def _validate_json_recursively(self, data, depth=0):
        """Recursively validate JSON data."""
        if depth > 10:  # Prevent deep recursion attacks
            raise SecurityException("JSON structure too deep", 400)

        if isinstance(data, dict):
            for key, value in data.items():
                self._validate_string_content(str(key))
                self._validate_json_recursively(value, depth + 1)
        elif isinstance(data, list):
            for item in data:
                self._validate_json_recursively(item, depth + 1)
        elif isinstance(data, str):
            self._validate_string_content(data)

    def _validate_string_content(self, content):
        """Validate string content for XSS and injection attacks."""
        if len(content) > 10000:  # Prevent extremely long strings
            raise SecurityException("String content too long", 400)

        # Check for XSS patterns
        xss_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"data:text/html",
            r"<iframe.*?>.*?</iframe>",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise SecurityException("Potentially malicious content detected", 400)

    def _log_security_event(self, event_type, details):
        """Log security events for monitoring."""
        try:
            audit_log = AuditLog(
                action=f"security_{event_type}",
                resource_type="security",
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            audit_log.set_details(details)
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to log security event: {e}")


class FileUploadSecurity:
    """Security utilities for file uploads."""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.allowed_mime_types = app.config.get("ALLOWED_MIME_TYPES", {})
            self.max_file_size = app.config.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)
        else:
            self.allowed_mime_types = {
                "text/csv": [".csv"],
                "application/json": [".json"],
                "text/plain": [".txt", ".csv"],  # Allow CSV files detected as text/plain
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
                    ".xlsx"
                ],
            }
            self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.blocked_extensions = {".exe", ".bat", ".cmd", ".scr", ".pif", ".com"}

    def validate_file(self, file):
        """Comprehensive file validation."""
        if not file or not file.filename:
            raise SecurityException("No file provided", 400)

        # Secure filename
        filename = secure_filename(file.filename)
        if not filename:
            raise SecurityException("Invalid filename", 400)

        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > self.max_file_size:
            raise SecurityException(
                f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB",
                413,
            )

        if size == 0:
            raise SecurityException("Empty file not allowed", 400)

        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()

        # Block dangerous extensions
        if file_ext in self.blocked_extensions:
            raise SecurityException(
                f"File type {file_ext} not allowed for security reasons", 400
            )

        # Validate MIME type
        file_content = file.read(1024)  # Read first 1KB
        file.seek(0)

        try:
            mime_type = magic.from_buffer(file_content, mime=True)
        except Exception:
            raise SecurityException("Unable to determine file type", 400)

        if mime_type not in self.allowed_mime_types:
            raise SecurityException(f"File type {mime_type} not allowed", 400)

        allowed_extensions = self.allowed_mime_types[mime_type]
        if file_ext not in allowed_extensions:
            raise SecurityException(
                f"File extension {file_ext} doesn't match file type {mime_type}", 400
            )

        # Scan for malicious content patterns
        self._scan_file_content(file)

        return True

    def _scan_file_content(self, file):
        """Scan file content for malicious patterns."""
        file.seek(0)

        # Read file in chunks to avoid memory issues
        chunk_size = 8192
        malicious_patterns = [
            b"<script",
            b"javascript:",
            b"vbscript:",
            b"data:text/html",
            b"<?php",
            b"<%",
            b"exec(",
            b"eval(",
            b"system(",
        ]

        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break

            chunk_lower = chunk.lower()
            for pattern in malicious_patterns:
                if pattern in chunk_lower:
                    raise SecurityException(
                        "Potentially malicious content detected in file", 400
                    )

        file.seek(0)


class AuthenticationSecurity:
    """Enhanced authentication security features."""

    def __init__(self, app=None):
        self.app = app
        self.redis_client = None
        if app and hasattr(app, "redis"):
            self.redis_client = app.redis

    def check_failed_logins(self, identifier):
        """Check if user has exceeded failed login attempts."""
        if not self.redis_client:
            return False

        key = f"failed_logins:{identifier}"
        try:
            failed_count = self.redis_client.get(key)
            if failed_count and int(failed_count) >= 5:
                return True
        except Exception:
            pass
        return False

    def record_failed_login(self, identifier):
        """Record a failed login attempt."""
        if not self.redis_client:
            return

        key = f"failed_logins:{identifier}"
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 900)  # 15 minutes
            pipe.execute()
        except Exception as e:
            current_app.logger.error(f"Failed to record failed login: {e}")

    def clear_failed_logins(self, identifier):
        """Clear failed login attempts for user."""
        if not self.redis_client:
            return

        key = f"failed_logins:{identifier}"
        try:
            self.redis_client.delete(key)
        except Exception as e:
            current_app.logger.error(f"Failed to clear failed logins: {e}")

    def generate_secure_token(self, user_id, token_type="access"):
        """Generate a secure JWT token with additional claims."""
        now = datetime.utcnow()

        if token_type == "access":
            expiry = now + timedelta(seconds=current_app.config["JWT_EXPIRATION_DELTA"])
        elif token_type == "refresh":
            expiry = now + timedelta(
                seconds=current_app.config.get("JWT_REFRESH_EXPIRATION_DELTA", 86400)
            )
        else:
            raise ValueError("Invalid token type")

        payload = {
            "user_id": user_id,
            "type": token_type,
            "iat": now,
            "exp": expiry,
            "jti": self._generate_jti(),  # JWT ID for revocation
            "iss": current_app.config.get("JWT_ISSUER", "phip-api"),
            "aud": current_app.config.get("JWT_AUDIENCE", "phip-client"),
        }

        token = jwt.encode(
            payload,
            current_app.config["SECRET_KEY"],
            algorithm=current_app.config["JWT_ALGORITHM"],
        )

        # Store token metadata in Redis for revocation
        if self.redis_client:
            token_key = f"token:{payload['jti']}"
            token_data = {
                "user_id": user_id,
                "type": token_type,
                "created_at": now.isoformat(),
            }
            try:
                self.redis_client.setex(
                    token_key,
                    int((expiry - now).total_seconds()),
                    json.dumps(token_data),
                )
            except Exception as e:
                current_app.logger.error(f"Failed to store token metadata: {e}")

        return token

    def verify_secure_token(self, token):
        """Verify JWT token with additional security checks."""
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
                options={
                    "verify_exp": True,
                    "verify_iss": False,  # Disable issuer verification for now
                    "verify_aud": False,  # Disable audience verification for now
                },
            )

            # Check if token is revoked
            if self.redis_client and "jti" in payload:
                token_key = f"token:{payload['jti']}"
                if not self.redis_client.exists(token_key):
                    return None  # Token revoked

            return payload

        except jwt.ExpiredSignatureError:
            current_app.logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            current_app.logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            current_app.logger.error(f"JWT token verification error: {e}")
            return None

    def revoke_token(self, jti):
        """Revoke a specific token."""
        if not self.redis_client:
            return False

        token_key = f"token:{jti}"
        try:
            return self.redis_client.delete(token_key) > 0
        except Exception as e:
            current_app.logger.error(f"Failed to revoke token: {e}")
            return False

    def revoke_all_user_tokens(self, user_id):
        """Revoke all tokens for a specific user."""
        if not self.redis_client:
            return False

        try:
            # Find all tokens for this user
            pattern = "token:*"
            tokens_to_revoke = []

            for key in self.redis_client.scan_iter(match=pattern):
                token_data = self.redis_client.get(key)
                if token_data:
                    try:
                        data = json.loads(token_data)
                        if data.get("user_id") == user_id:
                            tokens_to_revoke.append(key)
                    except json.JSONDecodeError:
                        continue

            # Revoke all found tokens
            if tokens_to_revoke:
                return self.redis_client.delete(*tokens_to_revoke) > 0

            return True

        except Exception as e:
            current_app.logger.error(f"Failed to revoke user tokens: {e}")
            return False

    def _generate_jti(self):
        """Generate a unique JWT ID."""
        return hashlib.sha256(f"{time.time()}{os.urandom(16)}".encode()).hexdigest()[
            :16
        ]


class InputSanitizer:
    """Input sanitization utilities."""

    @staticmethod
    def sanitize_string(value, max_length=None):
        """Sanitize string input."""
        if not isinstance(value, str):
            return value

        # Remove HTML tags and dangerous characters
        cleaned = bleach.clean(value, tags=[], strip=True)

        # Trim whitespace
        cleaned = cleaned.strip()

        # Enforce length limit
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]

        return cleaned

    @staticmethod
    def sanitize_dict(data, string_fields=None, max_length=1000):
        """Sanitize dictionary data."""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        string_fields = string_fields or []

        for key, value in data.items():
            # Sanitize key
            clean_key = InputSanitizer.sanitize_string(str(key), 100)

            # Sanitize value based on type
            if isinstance(value, str) and (not string_fields or key in string_fields):
                clean_value = InputSanitizer.sanitize_string(value, max_length)
            elif isinstance(value, dict):
                clean_value = InputSanitizer.sanitize_dict(
                    value, string_fields, max_length
                )
            elif isinstance(value, list):
                clean_value = [
                    (
                        InputSanitizer.sanitize_string(item, max_length)
                        if isinstance(item, str)
                        else item
                    )
                    for item in value[:100]  # Limit list size
                ]
            else:
                clean_value = value

            sanitized[clean_key] = clean_value

        return sanitized

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format using regex."""
        if not isinstance(email, str):
            return False
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength.

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
            "password",
            "123456",
            "password123",
            "admin",
            "qwerty",
            "letmein",
            "welcome",
            "monkey",
            "1234567890",
        ]
        if password.lower() in weak_passwords:
            return False, "Password is too common and weak"

        return True, "Password is valid"

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username format.

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

        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return (
                False,
                "Username can only contain letters, numbers, underscores, and hyphens",
            )

        if username.startswith(("-", "_")) or username.endswith(("-", "_")):
            return False, "Username cannot start or end with special characters"

        if username.isdigit():
            return False, "Username cannot be all numbers"

        return True, "Username is valid"


class SecurityException(Exception):
    """Custom exception for security-related errors."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# --- Validation Decorators (migrated from validators.py) ---


def validate_json_input(
    required_fields: List[str] = None, optional_fields: List[str] = None
):
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
                raise SecurityException("Content-Type must be application/json", 415)

            try:
                data = request.get_json()
            except json.JSONDecodeError:
                raise SecurityException("Invalid JSON format", 400)

            if data is None:
                raise SecurityException("No JSON data provided", 400)

            if not isinstance(data, dict):
                raise SecurityException("JSON data must be an object", 400)

            # Check required fields
            if required_fields:
                missing_fields = [
                    field for field in required_fields if field not in data
                ]
                if missing_fields:
                    raise SecurityException(
                        f"Missing required fields: {', '.join(missing_fields)}", 400
                    )

            # Check for empty required fields
            if required_fields:
                empty_fields = [
                    field
                    for field in required_fields
                    if field in data and (data[field] is None or data[field] == "")
                ]
                if empty_fields:
                    raise SecurityException(
                        f"Required fields cannot be empty: {', '.join(empty_fields)}",
                        400,
                    )

            # Check for unexpected fields
            all_allowed_fields = (required_fields or []) + (optional_fields or [])
            if all_allowed_fields:
                unexpected_fields = [
                    field for field in data.keys() if field not in all_allowed_fields
                ]
                if unexpected_fields:
                    raise SecurityException(
                        f"Unexpected fields: {', '.join(unexpected_fields)}", 400
                    )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_query_params(
    allowed_params: List[str] = None, required_params: List[str] = None
):
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
                missing_params = [
                    param for param in required_params if param not in request.args
                ]
                if missing_params:
                    raise SecurityException(
                        f"Missing required query parameters: {', '.join(missing_params)}",
                        400,
                    )

            # Check for unexpected parameters
            if allowed_params:
                unexpected_params = [
                    param
                    for param in request.args.keys()
                    if param not in allowed_params
                ]
                if unexpected_params:
                    raise SecurityException(
                        f"Unexpected query parameters: {', '.join(unexpected_params)}",
                        400,
                    )

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
                page = request.args.get("page", 1, type=int)
                per_page = request.args.get("per_page", 20, type=int)

                if page < 1:
                    raise SecurityException("Page number must be positive", 400)
                if per_page < 1:
                    raise SecurityException("Items per page must be positive", 400)
                if per_page > max_per_page:
                    raise SecurityException(
                        f"Items per page cannot exceed {max_per_page}", 400
                    )
            except (ValueError, TypeError):
                raise SecurityException("Page and per_page must be valid integers", 400)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def security_required(f):
    """Decorator to apply additional security checks."""

    @wraps(f)
    def decorated(*args, **kwargs):
        # Additional security checks can be added here
        return f(*args, **kwargs)

    return decorated


def admin_only(f):
    """Decorator to restrict access to admin users only."""

    @wraps(f)
    def decorated(*args, **kwargs):
        # This should be used in combination with token_required
        if not hasattr(request, "current_user"):
            return jsonify({"error": "Authentication required"}), 401

        if request.current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403

        return f(*args, **kwargs)

    return decorated


def audit_action(action_type):
    """Decorator to automatically audit specific actions."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Execute the function
            result = f(*args, **kwargs)

            # Create audit log
            try:
                user_id = getattr(request, "current_user", None)
                user_id = user_id.id if user_id else None

                audit_log = AuditLog(
                    user_id=user_id,
                    action=action_type,
                    resource_type=f.__module__.split(".")[-1],
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent"),
                )

                # Add request details
                details = {
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "args": dict(request.args),
                }
                audit_log.set_details(details)

                db.session.add(audit_log)
                db.session.commit()

            except Exception as e:
                current_app.logger.error(f"Failed to create audit log: {e}")

            return result

        return decorated

    return decorator
