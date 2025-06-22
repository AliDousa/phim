#!/bin/bash

# Rollback script for PHIP Backend
# This script handles rollback to previous versions

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"

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

# Show available backups
show_available_backups() {
    log_info "Available backups:"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_warn "No backup directory found at: $BACKUP_DIR"
        return 1
    fi
    
    # Find backup directories
    local backups=($(find "$BACKUP_DIR" -name "backup_*" -type d | sort -r))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        log_warn "No backups found in: $BACKUP_DIR"
        return 1
    fi
    
    echo ""
    echo "Index | Backup Name                | Date Created"
    echo "------|----------------------------|------------------"
    
    local index=1
    for backup in "${backups[@]}"; do
        local backup_name=$(basename "$backup")
        local backup_date="N/A"
        
        # Try to get date from manifest
        if [[ -f "$backup/manifest.json" ]]; then
            backup_date=$(jq -r '.timestamp // "N/A"' "$backup/manifest.json" 2>/dev/null || echo "N/A")
        fi
        
        printf "%5s | %-26s | %s\n" "$index" "$backup_name" "$backup_date"
        ((index++))
    done
    
    echo ""
    return 0
}

# Get backup by index
get_backup_by_index() {
    local index="$1"
    local backups=($(find "$BACKUP_DIR" -name "backup_*" -type d | sort -r))
    
    if [[ $index -lt 1 || $index -gt ${#backups[@]} ]]; then
        log_error "Invalid backup index: $index"
        return 1
    fi
    
    echo "${backups[$((index-1))]}"
}

# Get backup by name
get_backup_by_name() {
    local backup_name="$1"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup not found: $backup_name"
        return 1
    fi
    
    echo "$backup_path"
}

# Show backup details
show_backup_details() {
    local backup_path="$1"
    
    log_info "Backup details for: $(basename "$backup_path")"
    
    if [[ -f "$backup_path/manifest.json" ]]; then
        echo ""
        echo "Manifest:"
        jq '.' "$backup_path/manifest.json" 2>/dev/null || cat "$backup_path/manifest.json"
    fi
    
    echo ""
    echo "Contents:"
    ls -la "$backup_path"
    echo ""
}

# Rollback database
rollback_database() {
    local backup_path="$1"
    local db_backup="$backup_path/database.sql"
    
    if [[ ! -f "$db_backup" ]]; then
        log_warn "No database backup found, skipping database rollback"
        return 0
    fi
    
    log_info "Rolling back database..."
    
    # Load environment variables
    if [[ -f "${PROJECT_ROOT}/.env.production" ]]; then
        set -a
        source "${PROJECT_ROOT}/.env.production"
        set +a
    fi
    
    # Restore database using Docker
    if docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" ps postgres | grep -q "Up"; then
        log_info "Restoring database from backup..."
        
        # Create a temporary backup of current state
        local temp_backup="/tmp/rollback_safety_backup_$(date +%s).sql"
        docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T postgres \
            pg_dump -U "${POSTGRES_USER:-phip_user}" "${POSTGRES_DB:-phip_db}" > "$temp_backup"
        
        log_info "Current database backed up to: $temp_backup"
        
        # Restore from backup
        if docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T postgres \
           psql -U "${POSTGRES_USER:-phip_user}" -d "${POSTGRES_DB:-phip_db}" < "$db_backup"; then
            log_info "Database restoration completed successfully"
            rm -f "$temp_backup"
        else
            log_error "Database restoration failed!"
            log_info "Emergency: Restoring current state from: $temp_backup"
            docker-compose -f "${PROJECT_ROOT}/docker-compose.production.yml" exec -T postgres \
                psql -U "${POSTGRES_USER:-phip_user}" -d "${POSTGRES_DB:-phip_db}" < "$temp_backup"
            rm -f "$temp_backup"
            return 1
        fi
    else
        log_error "PostgreSQL container is not running"
        return 1
    fi
}

# Rollback application data
rollback_app_data() {
    local backup_path="$1"
    local data_backup="$backup_path/app_data.tar.gz"
    
    if [[ ! -f "$data_backup" ]]; then
        log_warn "No application data backup found, skipping"
        return 0
    fi
    
    log_info "Rolling back application data..."
    
    # Backup current data
    if [[ -d "${PROJECT_ROOT}/data" ]]; then
        local temp_backup="/tmp/current_data_backup_$(date +%s).tar.gz"
        tar -czf "$temp_backup" -C "${PROJECT_ROOT}" data/
        log_info "Current data backed up to: $temp_backup"
    fi
    
    # Restore data
    tar -xzf "$data_backup" -C "${PROJECT_ROOT}"
    log_info "Application data restored"
}

# Rollback uploads
rollback_uploads() {
    local backup_path="$1"
    local uploads_backup="$backup_path/uploads.tar.gz"
    
    if [[ ! -f "$uploads_backup" ]]; then
        log_warn "No uploads backup found, skipping"
        return 0
    fi
    
    log_info "Rolling back uploads..."
    
    # Backup current uploads
    if [[ -d "${PROJECT_ROOT}/uploads" ]]; then
        local temp_backup="/tmp/current_uploads_backup_$(date +%s).tar.gz"
        tar -czf "$temp_backup" -C "${PROJECT_ROOT}" uploads/
        log_info "Current uploads backed up to: $temp_backup"
    fi
    
    # Restore uploads
    tar -xzf "$uploads_backup" -C "${PROJECT_ROOT}"
    log_info "Uploads restored"
}

# Restart services after rollback
restart_services() {
    log_info "Restarting services after rollback..."
    
    cd "${PROJECT_ROOT}"
    
    # Restart application services
    docker-compose -f docker-compose.production.yml restart phip-backend celery-worker celery-beat
    
    # Wait for services to be ready
    sleep 10
    
    # Health check
    if curl -f -s "http://localhost:5000/health" > /dev/null; then
        log_info "Services restarted successfully"
        return 0
    else
        log_error "Health check failed after restart"
        return 1
    fi
}

# Interactive rollback selection
interactive_rollback() {
    if ! show_available_backups; then
        log_error "No backups available for rollback"
        exit 1
    fi
    
    echo "Select a backup to rollback to:"
    read -p "Enter backup index (or 'q' to quit): " selection
    
    if [[ "$selection" == "q" ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    if ! [[ "$selection" =~ ^[0-9]+$ ]]; then
        log_error "Invalid selection: $selection"
        exit 1
    fi
    
    local backup_path
    backup_path=$(get_backup_by_index "$selection")
    
    if [[ $? -ne 0 ]]; then
        exit 1
    fi
    
    show_backup_details "$backup_path"
    
    echo ""
    read -p "Are you sure you want to rollback to this backup? [y/N]: " confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    perform_rollback "$backup_path"
}

# Perform the actual rollback
perform_rollback() {
    local backup_path="$1"
    
    log_info "Starting rollback to: $(basename "$backup_path")"
    
    # Perform rollback steps
    rollback_database "$backup_path" || {
        log_error "Database rollback failed"
        exit 1
    }
    
    rollback_app_data "$backup_path" || {
        log_error "Application data rollback failed"
        exit 1
    }
    
    rollback_uploads "$backup_path" || {
        log_error "Uploads rollback failed"
        exit 1
    }
    
    # Restart services
    restart_services || {
        log_error "Service restart failed"
        exit 1
    }
    
    log_info "Rollback completed successfully!"
    log_info ""
    log_info "Application URLs:"
    log_info "  Main API: http://localhost:5000"
    log_info "  Health Check: http://localhost:5000/health"
}

# Main function
main() {
    log_info "PHIP Backend Rollback Tool"
    
    case "${1:-interactive}" in
        list)
            show_available_backups
            ;;
        interactive)
            interactive_rollback
            ;;
        *)
            backup_identifier="$1"
            
            # Check if it's a number (index) or name
            if [[ "$backup_identifier" =~ ^[0-9]+$ ]]; then
                backup_path=$(get_backup_by_index "$backup_identifier")
            else
                backup_path=$(get_backup_by_name "$backup_identifier")
            fi
            
            if [[ $? -ne 0 ]]; then
                log_error "Invalid backup: $backup_identifier"
                show_available_backups
                exit 1
            fi
            
            show_backup_details "$backup_path"
            perform_rollback "$backup_path"
            ;;
    esac
}

# Handle command line arguments
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [backup_index|backup_name|list|interactive]"
    echo ""
    echo "Commands:"
    echo "  list                    - List available backups"
    echo "  interactive (default)   - Interactive rollback selection"
    echo "  <backup_index>          - Rollback to backup by index"
    echo "  <backup_name>           - Rollback to backup by name"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 1"
    echo "  $0 backup_20240101_120000"
    exit 0
fi

# Run main function
main "$@"