"""
Gunicorn configuration for production deployment.
Public Health Intelligence Platform Backend
"""

import os
import multiprocessing
from pathlib import Path

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")
worker_connections = int(os.environ.get("GUNICORN_WORKER_CONNECTIONS", 1000))
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 100))
worker_tmp_dir = "/dev/shm"

# Timeouts
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 300))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 2))
graceful_timeout = 30

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if terminating SSL at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = ssl.PROTOCOL_TLSv1_2
# ciphers = "TLSv1.2"

# Logging
log_dir = Path("/app/logs")
log_dir.mkdir(exist_ok=True)

accesslog = str(log_dir / "gunicorn_access.log")
errorlog = str(log_dir / "gunicorn_error.log")
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "phip_backend"

# Server mechanics
preload_app = True
daemon = False
user = "appuser"
group = "appgroup"
tmp_upload_dir = "/app/uploads"

# Environment
raw_env = [
    "FLASK_ENV=production",
]

# Performance tuning
enable_stdio_inheritance = True

# Worker recycling
max_requests = 1000
max_requests_jitter = 50

# Memory management
worker_memory_usage_threshold = 500 * 1024 * 1024  # 500MB


def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker %s spawned (pid: %s)", worker.age, worker.pid)


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    # Initialize any worker-specific resources here
    # For example, database connections, caches, etc.


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug("%s %s", req.method, req.path)


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    # Log additional metrics here if needed
    pass


def child_exit(server, worker):
    """Called just after a worker has been reaped."""
    server.log.info("Worker %s (pid: %s) exited", worker.age, worker.pid)


def worker_exit(server, worker):
    """Called just after a worker has been reaped."""
    server.log.info(
        "Worker %s (pid: %s) exited with code %s",
        worker.age,
        worker.pid,
        worker.exitcode,
    )


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info("Number of workers changed from %s to %s", old_value, new_value)


def on_exit(server):
    """Called just before exiting."""
    server.log.info("Shutting down: Master")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading workers")


# Custom application factory
def app_factory():
    """Custom application factory for gunicorn."""
    from src.main import create_app

    # Create application with production config
    app = create_app("production")

    # Initialize any production-specific setup
    with app.app_context():
        # Database initialization
        from src.models.database import db

        db.create_all()

        # Any other initialization

    return app


# Environment-specific configurations
if os.environ.get("FLASK_ENV") == "development":
    # Development overrides
    workers = 1
    reload = True
    timeout = 0
    loglevel = "debug"
    accesslog = "-"
    errorlog = "-"

elif os.environ.get("FLASK_ENV") == "testing":
    # Testing overrides
    workers = 1
    timeout = 30
    loglevel = "warning"

# Docker-specific settings
if os.path.exists("/.dockerenv"):
    # Running in Docker
    user = None  # Don't change user in Docker
    group = None

    # Use environment variables for configuration
    bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"


# Performance monitoring
def monitor_worker_memory():
    """Monitor worker memory usage."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    if memory_info.rss > worker_memory_usage_threshold:
        print(
            f"Worker {os.getpid()} memory usage: {memory_info.rss / 1024 / 1024:.1f}MB"
        )
        return True
    return False


# Graceful shutdown handling
def handle_shutdown(signum, frame):
    """Handle graceful shutdown."""
    import signal
    import sys

    print(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


# Signal handlers
import signal

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


# Health check configuration
def health_check():
    """Simple health check for the application."""
    try:
        # You can add custom health checks here
        # For example, database connectivity, external services, etc.
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


# Prometheus metrics integration (optional)
try:
    from prometheus_client import multiprocess
    from prometheus_client import generate_latest
    from prometheus_client import CONTENT_TYPE_LATEST

    def prometheus_metrics():
        """Generate Prometheus metrics."""
        registry = multiprocess.MultiProcessCollector(multiprocess.registry)
        return generate_latest(registry)

except ImportError:
    # Prometheus client not available
    prometheus_metrics = None


# Custom error handling
def handle_error(req, client, addr, exc):
    """Custom error handler for gunicorn."""
    import traceback

    error_msg = f"Error processing request from {addr}: {exc}"
    print(error_msg)
    print(traceback.format_exc())

    # You could send this to a logging service, Sentry, etc.


# Rate limiting (basic implementation)
from collections import defaultdict
import time

request_counts = defaultdict(list)


def rate_limit_check(client_ip, limit=100, window=60):
    """Basic rate limiting check."""
    now = time.time()

    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] if now - req_time < window
    ]

    # Check limit
    if len(request_counts[client_ip]) >= limit:
        return False

    # Record this request
    request_counts[client_ip].append(now)
    return True


# Security headers
def add_security_headers(resp):
    """Add security headers to response."""
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp


# Configuration validation
def validate_config():
    """Validate configuration settings."""
    required_env_vars = ["SECRET_KEY", "DATABASE_URL"]

    for var in required_env_vars:
        if not os.environ.get(var):
            raise ValueError(f"Required environment variable {var} is not set")

    if len(os.environ.get("SECRET_KEY", "")) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")


# Run validation on startup
try:
    validate_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    exit(1)
