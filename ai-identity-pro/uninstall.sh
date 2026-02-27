#!/bin/bash
#
# AI Identity Pro - Uninstaller
# Safely removes all AI Identity Pro components
#
# Usage: curl -sSL https://aiidentity.pro/uninstall.sh | bash
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="${INSTALL_DIR:-/opt/ai-identity-pro}"
DOCKER_COMPOSE=""

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Print warning
print_warning() {
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ⚠️  WARNING                               ║"
    echo "║                                                              ║"
    echo "║  This will permanently remove AI Identity Pro and ALL data   ║"
    echo "║  including:                                                  ║"
    echo "║    • Application files                                       ║"
    echo "║    • Database (all users, twins, conversations)              ║"
    echo "║    • Configuration files                                     ║"
    echo "║    • SSL certificates                                        ║"
    echo "║    • Log files                                               ║"
    echo "║                                                              ║"
    echo "║  This action CANNOT be undone!                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Detect Docker Compose command
detect_docker_compose() {
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
}

# Confirm uninstallation
confirm_uninstall() {
    echo ""
    read -p "Are you sure you want to uninstall AI Identity Pro? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log_info "Uninstallation cancelled"
        exit 0
    fi
    
    echo ""
    read -p "Type 'DELETE' to confirm permanent data removal: " confirm2
    if [[ "$confirm2" != "DELETE" ]]; then
        log_info "Uninstallation cancelled"
        exit 0
    fi
}

# Backup before uninstall
backup_before_uninstall() {
    log_step "Creating final backup before uninstall..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        BACKUP_DIR="/root/aip-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup .env file
        if [[ -f "$INSTALL_DIR/.env" ]]; then
            cp "$INSTALL_DIR/.env" "$BACKUP_DIR/"
        fi
        
        # Backup database if possible
        if docker ps 2>/dev/null | grep -q "aip-postgres"; then
            log_info "Dumping database..."
            docker exec aip-postgres pg_dumpall -U postgres > "$BACKUP_DIR/database.sql" 2>/dev/null || true
        fi
        
        # Backup data directories
        if [[ -d "$INSTALL_DIR/data" ]]; then
            tar czf "$BACKUP_DIR/data.tar.gz" -C "$INSTALL_DIR" data/ 2>/dev/null || true
        fi
        
        log_warn "Backup created at: $BACKUP_DIR"
    fi
}

# Stop and remove containers
remove_containers() {
    log_step "Stopping and removing containers..."
    
    cd "$INSTALL_DIR" 2>/dev/null || true
    
    # Stop services
    $DOCKER_COMPOSE down --volumes --remove-orphans 2>/dev/null || true
    
    # Remove specific containers
    docker rm -f aip-frontend aip-backend aip-postgres aip-redis aip-weaviate aip-nginx aip-certbot 2>/dev/null || true
    
    log_success "Containers removed"
}

# Remove images
remove_images() {
    log_step "Removing Docker images..."
    
    docker rmi -f ai-identity-pro-frontend ai-identity-pro-backend 2>/dev/null || true
    
    log_success "Images removed"
}

# Remove systemd service
remove_systemd_service() {
    log_step "Removing systemd service..."
    
    if [[ -f /etc/systemd/system/ai-identity-pro.service ]]; then
        systemctl stop ai-identity-pro.service 2>/dev/null || true
        systemctl disable ai-identity-pro.service 2>/dev/null || true
        rm -f /etc/systemd/system/ai-identity-pro.service
        systemctl daemon-reload 2>/dev/null || true
        log_success "Systemd service removed"
    fi
}

# Remove installation directory
remove_installation() {
    log_step "Removing installation directory..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        log_success "Installation directory removed"
    fi
}

# Clean up Docker networks
cleanup_networks() {
    log_step "Cleaning up Docker networks..."
    
    docker network rm ai-identity-network 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
    
    log_success "Networks cleaned up"
}

# Remove firewall rules (optional)
remove_firewall_rules() {
    log_step "Removing firewall rules..."
    
    # UFW
    if command -v ufw >/dev/null 2>&1; then
        ufw delete allow 80/tcp 2>/dev/null || true
        ufw delete allow 443/tcp 2>/dev/null || true
    fi
    
    # Firewalld
    if command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --permanent --remove-service=http 2>/dev/null || true
        firewall-cmd --permanent --remove-service=https 2>/dev/null || true
        firewall-cmd --reload 2>/dev/null || true
    fi
    
    log_success "Firewall rules removed"
}

# Final cleanup
final_cleanup() {
    log_step "Performing final cleanup..."
    
    # Clean up any dangling volumes
    docker volume prune -f 2>/dev/null || true
    
    log_success "Cleanup complete"
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           ✅ AI Identity Pro Uninstalled                     ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log_warn "All data has been permanently deleted"
    
    if [[ -n "${BACKUP_DIR:-}" ]] && [[ -d "$BACKUP_DIR" ]]; then
        echo ""
        log_info "A backup was created at: $BACKUP_DIR"
        log_info "To restore, run the installer and manually restore your data"
    fi
    
    echo ""
    log_info "To reinstall, run:"
    echo "  curl -sSL https://aiidentity.pro/install.sh | bash"
}

# Main uninstall flow
main() {
    print_warning
    confirm_uninstall
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This uninstaller must be run as root (use sudo)"
        exit 1
    fi
    
    detect_docker_compose
    backup_before_uninstall
    remove_containers
    remove_images
    remove_systemd_service
    remove_installation
    cleanup_networks
    remove_firewall_rules
    final_cleanup
    
    print_completion
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "AI Identity Pro Uninstaller"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h       Show this help"
        echo ""
        echo "Environment variables:"
        echo "  INSTALL_DIR      Installation directory (default: /opt/ai-identity-pro)"
        exit 0
        ;;
esac

main "$@"
