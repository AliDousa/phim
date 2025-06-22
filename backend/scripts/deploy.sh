#!/bin/bash

# Production Deployment Script for Public Health Intelligence Platform
# This script handles complete production deployment with zero-downtime

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_ENV="${DEPLOY_ENV:-production}"
VERSION="${VERSION:-$(date +%Y%m%d_%H%M%S)}"
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-30}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-10}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Error handling
cleanup() {
    local exit_code=$?
    log_info "Cleaning up..."
    
    # Restore from backup if deployment failed
    if [[ $exit_code -ne 0 && "${BACKUP_ENABLED}" == "true" ]]; then
        log_warn "Deployment failed, attempting to restore from backup..."
        restore_from_backup || log_error "Backup restoration failed"
    fi
    
    exit $exit_code
}

trap cleanup EXIT

# Utility functions
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f "${PROJECT_ROOT}/.env.${DEPLOY_ENV}" ]]; then
        log_error "Environment file .env.${DEPLOY_ENV} not found"
        exit 1
    fi
    
    # Check if required directories exist
    mkdir -p "${PROJECT_ROOT}/data" "${PROJECT_ROOT}/logs" "${PROJECT_ROOT}/backups"
    
    log_info "Prerequisites check passed"
}

load_environment() {
    log_info "Loading environment configuration..."
    
    # Load environment variables
    set -a
    source "${PROJECT_ROOT}/.env.${DEPLOY_ENV}"
    set +a
    
    # Validate required environment variables
    required_vars=(
        "SECRET_KEY"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "DATABASE_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_info "Environment configuration loaded"
}

create_backup() {
    if [[ "${BACKUP_ENABLED}" != "true" ]]; then
        log_info "Backup is disabled, skipping..."
        return 0
    fi
    
    log_info "Creating backup before deployment..."
    
    local backup_dir="${PROJECT_ROOT}/backups/backup_${VERSION}"
    mkdir -p "$backup_dir"
    
    # Backup database
    if docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" ps postgres | grep -q "Up"; then
        log_info "Backing up database..."
        docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T postgres \
            pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "${backup_dir}/database.sql"
        
        if [[ $? -eq 0 ]]; then
            log_info "Database backup created successfully"
        else
            log_error "Database backup failed"
            return 1
        fi
    else
        log_warn "Database container is not running, skipping database backup"
    fi
    
    # Backup application data
    if [[ -d "${PROJECT_ROOT}/data" ]]; then
        log_info "Backing up application data..."
        tar -czf "${backup_dir}/app_data.tar.gz" -C "${PROJECT_ROOT}" data/
        log_info "Application data backup created"
    fi
    
    # Backup uploads
    if [[ -d "${PROJECT_ROOT}/uploads" ]]; then
        log_info "Backing up uploads..."
        tar -czf "${backup_dir}/uploads.tar.gz" -C "${PROJECT_ROOT}" uploads/
        log_info "Uploads backup created"
    fi
    
    # Create backup manifest
    cat > "${backup_dir}/manifest.json" << EOF
{
    "version": "${VERSION}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "${DEPLOY_ENV}",
    "components": {
        "database": $([ -f "${backup_dir}/database.sql" ] && echo "true" || echo "false"),
        "app_data": $([ -f "${backup_dir}/app_data.tar.gz" ] && echo "true" || echo "false"),
        "uploads": $([ -f "${backup_dir}/uploads.tar.gz" ] && echo "true" || echo "false")
    }
}
EOF
    
    log_info "Backup created successfully at ${backup_dir}"
}

restore_from_backup() {
    local latest_backup=$(find "${PROJECT_ROOT}/backups" -name "backup_*" -type d | sort -r | head -n1)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found for restoration"
        return 1
    fi
    
    log_info "Restoring from backup: $latest_backup"
    
    # Restore database
    if [[ -f "${latest_backup}/database.sql" ]]; then
        log_info "Restoring database..."
        docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T postgres \
            psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "${latest_backup}/database.sql"
    fi
    
    # Restore application data
    if [[ -f "${latest_backup}/app_data.tar.gz" ]]; then
        log_info "Restoring application data..."
        tar -xzf "${latest_backup}/app_data.tar.gz" -C "${PROJECT_ROOT}"
    fi
    
    # Restore uploads
    if [[ -f "${latest_backup}/uploads.tar.gz" ]]; then
        log_info "Restoring uploads..."
        tar -xzf "${latest_backup}/uploads.tar.gz" -C "${PROJECT_ROOT}"
    fi
    
    log_info "Backup restoration completed"
}

build_images() {
    log_info "Building Docker images..."
    
    cd "${PROJECT_ROOT}"
    
    # Build with build arguments
    docker-compose -f docker-compose.production.yml build \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        --build-arg VERSION="${VERSION}" \
        --parallel
    
    if [[ $? -eq 0 ]]; then
        log_info "Docker images built successfully"
    else
        log_error "Docker image build failed"
        exit 1
    fi
}

run_database_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    wait_for_service "postgres" "5432"
    
    # Run migrations
    docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T phip-backend \
        python -c "
from src.main import create_app
from src.models.database import db

app = create_app('production')
with app.app_context():
    db.create_all()
    print('Database migrations completed successfully')
"
    
    if [[ $? -eq 0 ]]; then
        log_info "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

wait_for_service() {
    local service_name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for $service_name to be ready..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T "$service_name" \
           nc -z localhost "$port" 2>/dev/null; then
            log_info "$service_name is ready"
            return 0
        fi
        
        log_debug "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    log_error "$service_name failed to become ready within expected time"
    return 1
}

deploy_services() {
    log_info "Deploying services..."
    
    cd "${PROJECT_ROOT}"
    
    # Start infrastructure services first
    log_info "Starting infrastructure services..."
    docker-compose -f docker-compose.production.yml up -d postgres redis
    
    # Wait for infrastructure to be ready
    wait_for_service "postgres" "5432"
    wait_for_service "redis" "6379"
    
    # Run database migrations
    run_database_migrations
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f docker-compose.production.yml up -d phip-backend celery-worker celery-beat
    
    # Wait for application to be ready
    wait_for_service "phip-backend" "5000"
    
    # Start supporting services
    log_info "Starting supporting services..."
    docker-compose -f docker-compose.production.yml up -d nginx flower prometheus grafana
    
    log_info "All services deployed successfully"
}

run_health_checks() {
    log_info "Running health checks..."
    
    local services=("phip-backend" "postgres" "redis" "celery-worker")
    local failed_services=()
    
    for service in "${services[@]}"; do
        log_info "Checking health of $service..."
        
        if docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" ps "$service" | grep -q "Up"; then
            log_info "$service is running"
            
            # Additional health checks for specific services
            case "$service" in
                "phip-backend")
                    if curl -f -s "http://localhost:5000/health" > /dev/null; then
                        log_info "$service health check passed"
                    else
                        log_error "$service health check failed"
                        failed_services+=("$service")
                    fi
                    ;;
                "postgres")
                    if docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T "$service" \
                       pg_isready -U "${POSTGRES_USER}" > /dev/null; then
                        log_info "$service health check passed"
                    else
                        log_error "$service health check failed"
                        failed_services+=("$service")
                    fi
                    ;;
                "redis")
                    if docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T "$service" \
                       redis-cli --no-auth-warning -a "${REDIS_PASSWORD}" ping | grep -q "PONG"; then
                        log_info "$service health check passed"
                    else
                        log_error "$service health check failed"
                        failed_services+=("$service")
                    fi
                    ;;
            esac
        else
            log_error "$service is not running"
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_info "All health checks passed"
        return 0
    else
        log_error "Health checks failed for services: ${failed_services[*]}"
        return 1
    fi
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test API endpoints
    local endpoints=(
        "/"
        "/health"
        "/api/auth/register"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Testing endpoint: $endpoint"
        
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000$endpoint")
        
        if [[ "$response_code" =~ ^[2-4][0-9][0-9]$ ]]; then
            log_info "Endpoint $endpoint responded with code $response_code"
        else
            log_error "Endpoint $endpoint failed with code $response_code"
            return 1
        fi
    done
    
    log_info "All smoke tests passed"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old application images (keep last 3 versions)
    local old_images=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | \
                      grep "phip" | sort -k2 -r | tail -n +4 | awk '{print $1}')
    
    if [[ -n "$old_images" ]]; then
        echo "$old_images" | xargs -r docker rmi -f
        log_info "Old images cleaned up"
    else
        log_info "No old images to clean up"
    fi
}

show_deployment_status() {
    log_info "Deployment Status:"
    echo "===================="
    
    # Show running services
    docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" ps
    
    echo ""
    log_info "Application URLs:"
    echo "  Main API: https://$(hostname):443"
    echo "  Health Check: https://$(hostname):443/health"
    echo "  Flower Monitoring: https://$(hostname):5555"
    echo "  Grafana Dashboard: https://$(hostname):3000"
    echo "  Prometheus: https://$(hostname):9090"
    
    echo ""
    log_info "Useful Commands:"
    echo "  View logs: docker-compose -f docker-compose.production.yml logs -f [service]"
    echo "  Scale workers: docker-compose -f docker-compose.production.yml up -d --scale celery-worker=N"
    echo "  Update: ./scripts/deploy.sh"
    echo "  Rollback: ./scripts/rollback.sh"
}

# Main deployment flow
main() {
    log_info "Starting deployment of PHIP Backend (Version: $VERSION)"
    log_info "Environment: $DEPLOY_ENV"
    
    # Pre-deployment steps
    check_prerequisites
    load_environment
    create_backup
    
    # Build and deploy
    build_images
    deploy_services
    
    # Post-deployment validation
    run_health_checks
    run_smoke_tests
    
    # Cleanup
    cleanup_old_images
    
    # Show status
    show_deployment_status
    
    log_info "Deployment completed successfully!"
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    backup)
        check_prerequisites
        load_environment
        create_backup
        ;;
    restore)
        check_prerequisites
        load_environment
        restore_from_backup
        ;;
    health)
        check_prerequisites
        load_environment
        run_health_checks
        ;;
    status)
        show_deployment_status
        ;;
    *)
        echo "Usage: $0 {deploy|backup|restore|health|status}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  backup  - Create backup only"
        echo "  restore - Restore from latest backup"
        echo "  health  - Run health checks"
        echo "  status  - Show deployment status"
        exit 1
        ;;
esac