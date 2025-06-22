#!/bin/bash

# Production entrypoint script for PHIP Backend
# This script handles application initialization and startup

set -euo pipefail

# Configuration
APP_DIR="/app"
LOG_DIR="/app/logs"
DATA_DIR="/app/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for a service to become available
wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for $service_name to be available at $host:$port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_info "$service_name is available"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        ((attempt++))
    done
    
    log_error "$service_name failed to become available within expected time"
    return 1
}

# Initialize application
initialize_app() {
    log_info "Initializing PHIP Backend application..."
    
    # Create necessary directories
    mkdir -p "$LOG_DIR" "$DATA_DIR" /app/uploads
    
    # Set correct permissions
    chown -R appuser:appgroup "$LOG_DIR" "$DATA_DIR" /app/uploads 2>/dev/null || true
    
    # Wait for external dependencies
    if [[ "${DATABASE_URL:-}" == *"postgres"* ]]; then
        # Extract host and port from DATABASE_URL
        db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        if [[ -n "$db_host" && -n "$db_port" ]]; then
            wait_for_service "$db_host" "$db_port" "PostgreSQL"
        fi
    fi
    
    if [[ "${REDIS_URL:-}" == *"redis"* ]]; then
        # Extract host and port from REDIS_URL
        redis_host=$(echo "$REDIS_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p' | sed 's/.*\/\/\([^:@]*\).*/\1/')
        redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
        
        if [[ -n "$redis_host" && -n "$redis_port" ]]; then
            wait_for_service "$redis_host" "$redis_port" "Redis"
        fi
    fi
    
    log_info "Application initialization completed"
}

# Database initialization
init_database() {
    log_info "Initializing database..."
    
    cd "$APP_DIR"
    
    # Run database initialization
    python -c "
import sys
sys.path.insert(0, '/app')

try:
    from src.main import create_app
    from src.models.database import db
    
    app = create_app('production')
    with app.app_context():
        # Create all tables
        db.create_all()
        print('Database tables created successfully')
        
        # Test database connection
        from sqlalchemy import text
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        print('Database connection verified')
        
except Exception as e:
    print(f'Database initialization failed: {e}')
    sys.exit(1)
"
    
    if [[ $? -eq 0 ]]; then
        log_info "Database initialization completed successfully"
    else
        log_error "Database initialization failed"
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Running health check..."
    
    # Basic application health check
    python -c "
import sys
sys.path.insert(0, '/app')

try:
    from src.main import create_app
    app = create_app('production')
    
    with app.test_client() as client:
        # Test application startup
        with app.app_context():
            print('Application context created successfully')
    
    print('Health check passed')
except Exception as e:
    print(f'Health check failed: {e}')
    sys.exit(1)
"
    
    if [[ $? -eq 0 ]]; then
        log_info "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Signal handlers
handle_sigterm() {
    log_info "Received SIGTERM, shutting down gracefully..."
    # Kill background processes
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

handle_sigint() {
    log_info "Received SIGINT, shutting down gracefully..."
    # Kill background processes
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap handle_sigterm SIGTERM
trap handle_sigint SIGINT

# Main execution
main() {
    log_info "Starting PHIP Backend (Production Mode)"
    log_info "Python version: $(python --version)"
    log_info "Working directory: $(pwd)"
    log_info "User: $(whoami)"
    
    # Environment validation
    if [[ -z "${SECRET_KEY:-}" ]]; then
        log_error "SECRET_KEY environment variable is required"
        exit 1
    fi
    
    if [[ -z "${DATABASE_URL:-}" ]]; then
        log_error "DATABASE_URL environment variable is required"
        exit 1
    fi
    
    # Initialize application
    initialize_app
    
    # Initialize database (only for main app, not workers)
    if [[ "${CONTAINER_ROLE:-app}" == "app" ]]; then
        init_database
    fi
    
    # Run health check
    health_check
    
    log_info "Starting application with command: $*"
    
    # Execute the main command
    exec "$@"
}

# Check if running as root and switch to appuser if needed
if [[ $(id -u) -eq 0 ]]; then
    log_info "Running as root, switching to appuser..."
    
    # Ensure correct ownership
    chown -R appuser:appgroup /app
    
    # Execute as appuser
    exec gosu appuser "$0" "$@"
fi

# Run main function with all arguments
main "$@"