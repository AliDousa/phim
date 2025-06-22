#!/bin/bash

# Setup script to create missing files and directories
# Run this before deployment if you encounter missing file errors

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create directories
create_directories() {
    log_info "Creating necessary directories..."
    
    directories=(
        "scripts"
        "config"
        "data"
        "logs"
        "backups"
        "uploads"
        "migrations"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$PROJECT_ROOT/$dir"
        log_info "Created directory: $dir"
    done
}

# Make scripts executable
make_scripts_executable() {
    log_info "Making scripts executable..."
    
    if [[ -d "$SCRIPT_DIR" ]]; then
        find "$SCRIPT_DIR" -name "*.sh" -type f -exec chmod +x {} \;
        log_info "Made all .sh files in scripts/ executable"
    fi
}

# Create basic .gitkeep files for empty directories
create_gitkeep_files() {
    log_info "Creating .gitkeep files for empty directories..."
    
    empty_dirs=(
        "data"
        "logs" 
        "backups"
        "uploads"
    )
    
    for dir in "${empty_dirs[@]}"; do
        touch "$PROJECT_ROOT/$dir/.gitkeep"
        log_info "Created .gitkeep in $dir/"
    done
}

# Create a simple init database migration
create_init_migration() {
    log_info "Creating initial database migration..."
    
    migration_file="$PROJECT_ROOT/migrations/001_initial_schema.sql"
    
    if [[ ! -f "$migration_file" ]]; then
        cat > "$migration_file" << 'EOF'
-- Migration: 001_initial_schema: Initial database schema
-- Created: 2024-01-01T00:00:00Z
-- Description: Create initial database schema for PHIP Backend

-- This migration will be automatically applied when the application starts
-- The actual table creation is handled by SQLAlchemy in the application code

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database schema version tracking
-- This table is created by the migration system itself

-- Application tables are created by SQLAlchemy models
-- See src/models/database.py for the complete schema definition
EOF
        log_info "Created initial migration file"
    else
        log_warn "Initial migration already exists"
    fi
}

# Verify required files exist
verify_required_files() {
    log_info "Verifying required files exist..."
    
    required_files=(
        "requirements.txt"
        "src/main.py"
        "src/config.py"
        "docker-compose.production.yml"
        "scripts/entrypoint-production.sh"
        "scripts/entrypoint-development.sh"
        "scripts/deploy.sh"
        "scripts/backup.sh"
    )
    
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_warn "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        echo ""
        log_warn "Please ensure all required files are created before deployment"
        return 1
    else
        log_info "All required files are present"
        return 0
    fi
}

# Main setup function
main() {
    log_info "Setting up PHIP Backend project structure..."
    log_info "Project root: $PROJECT_ROOT"
    
    # Create directories
    create_directories
    
    # Create .gitkeep files
    create_gitkeep_files
    
    # Create initial migration
    create_init_migration
    
    # Make scripts executable
    make_scripts_executable
    
    # Verify files
    if verify_required_files; then
        log_info "Setup completed successfully!"
        log_info ""
        log_info "Next steps:"
        log_info "1. Copy and configure .env.production"
        log_info "2. Run ./scripts/deploy.sh to deploy"
        log_info "3. Check logs in ./logs/ directory"
    else
        log_warn "Setup completed with warnings - please address missing files"
        exit 1
    fi
}

# Run main function
main "$@"