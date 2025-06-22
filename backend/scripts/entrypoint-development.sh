#!/bin/bash

# Development entrypoint script for PHIP Backend
# This script handles development environment setup

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

# Wait for service (simplified for development)
wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts=15
    local attempt=1
    
    log_info "Waiting for $service_name at $host:$port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_info "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    log_warn "$service_name not available, continuing anyway (development mode)"
    return 0
}

# Initialize development environment
initialize_dev_app() {
    log_info "Initializing PHIP Backend (Development Mode)"
    
    # Create necessary directories
    mkdir -p "$LOG_DIR" "$DATA_DIR" /app/uploads
    
    # Wait for dependencies (but don't fail if they're not available)
    if [[ "${DATABASE_URL:-}" == *"postgres"* ]]; then
        db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        if [[ -n "$db_host" && -n "$db_port" ]]; then
            wait_for_service "$db_host" "$db_port" "PostgreSQL"
        fi
    fi
    
    if [[ "${REDIS_URL:-}" == *"redis"* ]]; then
        redis_host=$(echo "$REDIS_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p' | sed 's/.*\/\/\([^:@]*\).*/\1/')
        redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
        
        if [[ -n "$redis_host" && -n "$redis_port" ]]; then
            wait_for_service "$redis_host" "$redis_port" "Redis"
        fi
    fi
}

# Initialize database for development
init_dev_database() {
    log_info "Setting up development database..."
    
    cd "$APP_DIR"
    
    python -c "
import sys
sys.path.insert(0, '/app')

try:
    from src.main import create_app
    from src.models.database import db
    
    app = create_app('development')
    with app.app_context():
        # Create all tables
        db.create_all()
        print('Development database initialized')
        
except Exception as e:
    print(f'Note: Database setup issue (continuing anyway): {e}')
"
}

# Development-specific setup
setup_development() {
    log_info "Setting up development environment..."
    
    # Install development dependencies if requirements-dev.txt exists
    if [[ -f "/app/requirements-dev.txt" ]]; then
        log_info "Installing development dependencies..."
        pip install -r /app/requirements-dev.txt || log_warn "Failed to install dev dependencies"
    fi
    
    # Enable debug mode
    export FLASK_DEBUG=1
    export FLASK_ENV=development
    
    log_info "Development setup completed"
}

# Signal handlers for development
handle_signal() {
    log_info "Shutting down development server..."
    exit 0
}

trap handle_signal SIGTERM SIGINT

# Main function
main() {
    log_info "=== PHIP Backend Development Environment ==="
    log_info "Python version: $(python --version)"
    log_info "Working directory: $(pwd)"
    
    # Initialize development environment
    initialize_dev_app
    setup_development
    init_dev_database
    
    # Show some helpful information
    log_info "Development server starting..."
    log_info "API will be available at: http://localhost:5000"
    log_info "Health check: http://localhost:5000/health"
    log_info ""
    log_info "Available endpoints:"
    log_info "  - POST /api/auth/register (User registration)"
    log_info "  - POST /api/auth/login (User login)"
    log_info "  - GET  /api/datasets (List datasets)"
    log_info "  - POST /api/datasets (Upload dataset)"
    log_info "  - GET  /api/simulations (List simulations)"
    log_info "  - POST /api/simulations (Create simulation)"
    log_info ""
    log_info "Press Ctrl+C to stop the server"
    log_info "================================================="
    
    # Execute the main command
    exec "$@"
}

# Run main function with all arguments
main "$@"