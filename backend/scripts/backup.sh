#!/bin/bash

# Database backup script for PHIP Backend
# This script creates automated backups of the PostgreSQL database

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="phip_backup_${DATE}.sql"

# Database configuration
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-phip_db}"
POSTGRES_USER="${POSTGRES_USER:-phip_user}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to create database backup
create_backup() {
    log_info "Starting database backup..."
    log_info "Database: $POSTGRES_DB"
    log_info "Host: $POSTGRES_HOST"
    log_info "Backup file: $BACKUP_FILE"
    
    # Create backup
    if pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$BACKUP_DIR/$BACKUP_FILE"; then
        # Compress backup
        gzip "$BACKUP_DIR/$BACKUP_FILE"
        log_info "Backup created successfully: $BACKUP_DIR/${BACKUP_FILE}.gz"
        
        # Get backup size
        backup_size=$(du -h "$BACKUP_DIR/${BACKUP_FILE}.gz" | cut -f1)
        log_info "Backup size: $backup_size"
        
        return 0
    else
        log_error "Backup failed!"
        return 1
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Find and delete old backups
    old_backups=$(find "$BACKUP_DIR" -name "phip_backup_*.sql.gz" -mtime +$RETENTION_DAYS)
    
    if [[ -n "$old_backups" ]]; then
        echo "$old_backups" | while read -r backup; do
            log_info "Removing old backup: $(basename "$backup")"
            rm -f "$backup"
        done
    else
        log_info "No old backups to clean up"
    fi
}

# Function to verify backup
verify_backup() {
    local backup_file="$BACKUP_DIR/${BACKUP_FILE}.gz"
    
    log_info "Verifying backup integrity..."
    
    # Check if file exists and is not empty
    if [[ -f "$backup_file" && -s "$backup_file" ]]; then
        # Test gzip integrity
        if gzip -t "$backup_file"; then
            log_info "Backup verification successful"
            return 0
        else
            log_error "Backup file is corrupted"
            return 1
        fi
    else
        log_error "Backup file is missing or empty"
        return 1
    fi
}

# Function to send notification (if configured)
send_notification() {
    local status="$1"
    local message="$2"
    
    # Send to webhook if configured
    if [[ -n "${BACKUP_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$BACKUP_WEBHOOK_URL" \
             -H "Content-Type: application/json" \
             -d "{\"text\":\"PHIP Backup $status: $message\"}" || true
    fi
    
    # Send email if configured
    if [[ -n "${BACKUP_EMAIL:-}" ]] && command -v mail >/dev/null; then
        echo "$message" | mail -s "PHIP Backup $status" "$BACKUP_EMAIL" || true
    fi
}

# Main backup process
main() {
    log_info "PHIP Database Backup Started"
    log_info "Timestamp: $(date)"
    
    # Check if PostgreSQL is available
    if ! pg_isready -h "$POSTGRES_HOST" -U "$POSTGRES_USER" >/dev/null 2>&1; then
        log_error "PostgreSQL is not available at $POSTGRES_HOST"
        send_notification "FAILED" "PostgreSQL not available"
        exit 1
    fi
    
    # Create backup
    if create_backup; then
        # Verify backup
        if verify_backup; then
            # Clean old backups
            cleanup_old_backups
            
            log_info "Backup process completed successfully"
            send_notification "SUCCESS" "Backup completed: ${BACKUP_FILE}.gz"
        else
            log_error "Backup verification failed"
            send_notification "FAILED" "Backup verification failed"
            exit 1
        fi
    else
        log_error "Backup creation failed"
        send_notification "FAILED" "Backup creation failed"
        exit 1
    fi
}

# Handle signals
trap 'log_info "Backup interrupted"; exit 1' SIGINT SIGTERM

# Run main function
main "$@"