#!/bin/bash
#
# Meetily Pro - Update Script
# Safely updates to the latest version
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="${INSTALL_DIR:-/opt/meetily-pro}"
REPO_URL="${REPO_URL:-https://github.com/meetily/meetily-pro.git}"
BACKUP_DIR="/root/meetily-backup-$(date +%Y%m%d-%H%M%S)"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🔄 Meetily Pro Updater v2.0.0                     ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if installed
check_installation() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "Meetily Pro is not installed at $INSTALL_DIR"
        log_info "To install, run: curl -sSL https://meetily.pro/install.sh | bash"
        exit 1
    fi
    
    if [[ ! -f "$INSTALL_DIR/.env" ]]; then
        log_error "Installation appears incomplete (missing .env file)"
        exit 1
    fi
    
    log_success "Installation found at $INSTALL_DIR"
}

# Create backup
create_backup() {
    log_info "Creating backup before update..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup environment file
    cp "$INSTALL_DIR/.env" "$BACKUP_DIR/"
    
    # Backup admin credentials
    if [[ -f "$INSTALL_DIR/.admin-credentials" ]]; then
        cp "$INSTALL_DIR/.admin-credentials" "$BACKUP_DIR/"
    fi
    
    # Backup database
    log_info "Backing up database..."
    cd "$INSTALL_DIR"
    if docker ps | grep -q "meetily-postgres"; then
        docker exec meetily-postgres pg_dumpall -U postgres > "$BACKUP_DIR/database.sql" 2>/dev/null || {
            log_warn "Database backup failed, continuing anyway..."
        }
    fi
    
    # Backup storage metadata
    if [[ -d "$INSTALL_DIR/storage" ]]; then
        tar czf "$BACKUP_DIR/storage-metadata.tar.gz" -C "$INSTALL_DIR" storage/ 2>/dev/null || true
    fi
    
    log_success "Backup created at $BACKUP_DIR"
}

# Get current version
get_current_version() {
    if [[ -f "$INSTALL_DIR/.version" ]]; then
        cat "$INSTALL_DIR/.version"
    else
        echo "unknown"
    fi
}

# Get latest version
get_latest_version() {
    curl -s https://api.github.com/repos/meetily/meetily-pro/releases/latest | \
        grep '"tag_name":' | \
        sed -E 's/.*"([^"]+)".*/\1/' || \
        echo "latest"
}

# Pull latest code
update_code() {
    log_info "Updating application code..."
    
    cd "$INSTALL_DIR"
    
    # Stash any local changes
    git stash 2>/dev/null || true
    
    # Fetch latest
    git fetch origin
    
    # Get current branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # Pull latest changes
    git pull origin "$BRANCH" || {
        log_error "Failed to pull latest code"
        log_info "You may need to resolve conflicts manually"
        exit 1
    }
    
    log_success "Code updated to latest version"
}

# Update Docker images
update_images() {
    log_info "Pulling latest Docker images..."
    
    cd "$INSTALL_DIR"
    
    docker compose pull 2>/dev/null || docker-compose pull 2>/dev/null || {
        log_warn "Some images could not be pulled, will build from source"
    }
    
    log_success "Images updated"
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$INSTALL_DIR"
    
    # Ensure postgres is running
    if ! docker ps | grep -q "meetily-postgres"; then
        docker compose up -d postgres 2>/dev/null || docker-compose up -d postgres 2>/dev/null
        sleep 5
    fi
    
    # Wait for postgres
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if docker exec meetily-postgres pg_isready -U postgres >/dev/null 2>&1; then
            break
        fi
        sleep 2
        ((retries--))
    done
    
    # Run migrations (if migration script exists)
    if [[ -f "$INSTALL_DIR/backend/migrate.py" ]]; then
        docker compose exec -T backend python migrate.py 2>/dev/null || {
            log_warn "Migration script failed or not found, continuing..."
        }
    fi
    
    log_success "Migrations complete"
}

# Restart services
restart_services() {
    log_info "Restarting services..."
    
    cd "$INSTALL_DIR"
    
    # Rebuild and restart
    docker compose up -d --build 2>/dev/null || docker-compose up -d --build 2>/dev/null
    
    log_success "Services restarted"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    sleep 10
    
    local services=("meetily-postgres" "meetily-redis" "meetily-backend" "meetily-nginx")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker ps | grep -q "$service"; then
            if docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null | grep -q "healthy"; then
                log_success "$service is healthy"
            else
                log_warn "$service status unknown (may still be starting)"
            fi
        else
            log_error "$service is not running"
            all_healthy=false
        fi
    done
    
    if [[ "$all_healthy" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Keep only last 5 backups
    ls -t /root/meetily-backup-* 2>/dev/null | tail -n +6 | xargs -r rm -rf
    
    log_success "Old backups cleaned up"
}

# Print completion
print_completion() {
    local new_version=$(get_latest_version)
    
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           ✅ Update Complete!                                ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log_success "Meetily Pro updated to version $new_version"
    
    echo ""
    log_info "Backup location: $BACKUP_DIR"
    echo ""
    log_info "If you encounter issues, you can restore with:"
    echo "  1. Stop services: cd $INSTALL_DIR && docker compose down"
    echo "  2. Restore database: docker exec -i meetily-postgres psql -U postgres < $BACKUP_DIR/database.sql"
    echo "  3. Restore .env: cp $BACKUP_DIR/.env $INSTALL_DIR/"
    echo "  4. Start services: cd $INSTALL_DIR && docker compose up -d"
}

# Rollback function
rollback() {
    log_error "Update failed! Rolling back..."
    
    cd "$INSTALL_DIR"
    
    # Stop services
    docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
    
    # Restore database
    if [[ -f "$BACKUP_DIR/database.sql" ]]; then
        log_info "Restoring database..."
        docker compose up -d postgres 2>/dev/null || true
        sleep 5
        docker exec -i meetily-postgres psql -U postgres < "$BACKUP_DIR/database.sql" 2>/dev/null || {
            log_warn "Database restore failed"
        }
    fi
    
    # Restore .env
    cp "$BACKUP_DIR/.env" "$INSTALL_DIR/"
    
    # Restore code (git stash pop)
    git stash pop 2>/dev/null || true
    
    # Restart services
    docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
    
    log_warn "Rollback complete. System restored to previous state."
    log_info "Please check the error messages above and try again later."
}

# Main update flow
main() {
    print_banner
    
    # Check root
    if [[ $EUID -ne 0 ]]; then
        log_error "This updater must be run as root (use sudo)"
        exit 1
    fi
    
    check_installation
    
    local current_version=$(get_current_version)
    log_info "Current version: $current_version"
    
    create_backup
    
    # Set trap for rollback on error
    trap rollback ERR
    
    update_code
    update_images
    run_migrations
    restart_services
    
    # Remove trap after successful update
    trap - ERR
    
    if health_check; then
        log_success "All health checks passed"
    else
        log_warn "Some health checks failed"
    fi
    
    cleanup_old_backups
    
    # Save new version
    get_latest_version > "$INSTALL_DIR/.version"
    
    print_completion
}

# Handle command line arguments
case "${1:-}" in
    --version|-v)
        echo "Meetily Pro Updater v2.0.0"
        exit 0
        ;;
    --help|-h)
        echo "Meetily Pro Updater"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --version, -v    Show version"
        echo "  --help, -h       Show this help"
        echo ""
        echo "Environment variables:"
        echo "  INSTALL_DIR      Installation directory (default: /opt/meetily-pro)"
        echo "  REPO_URL         Git repository URL"
        exit 0
        ;;
esac

main "$@"
