#!/bin/bash
#
# AI Identity Pro - One-Line Installer
# Usage: curl -sSL https://aiidentity.pro/install.sh | bash
#
# This script installs AI Identity Pro with all dependencies
# Supports: Ubuntu, Debian, CentOS, RHEL, Fedora, macOS
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/opt/ai-identity-pro}"
REPO_URL="${REPO_URL:-https://github.com/aiidentity/ai-identity-pro.git}"
VERSION="${VERSION:-latest}"
DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@localhost}"
DOCKER_COMPOSE=""

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              🤖 AI Identity Pro Installer                   ║"
    echo "║                                                              ║"
    echo "║          Premium Digital Twin Platform - v2.0.0             ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "  One-line installer for AI Identity Pro"
    echo "  Documentation: https://docs.aiidentity.pro"
    echo ""
}

# Check if running as root
check_root() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        if [[ $EUID -ne 0 ]]; then
            log_error "This installer must be run as root (use sudo)"
            log_info "Example: curl -sSL https://aiidentity.pro/install.sh | sudo bash"
            exit 1
        fi
    fi
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "Detected OS: macOS"
    elif [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION_ID=$VERSION_ID
        log_info "Detected OS: $OS $VERSION_ID"
    elif [[ -f /etc/redhat-release ]]; then
        OS="centos"
        log_info "Detected OS: CentOS/RHEL"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
        log_info "Detected OS: Debian"
    else
        OS=$(uname -s)
        log_info "Detected OS: $OS"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker for Linux
install_docker_linux() {
    log_info "Installing Docker..."
    
    case $OS in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq apt-transport-https ca-certificates curl gnupg lsb-release software-properties-common
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update -qq
            apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        centos|rhel|fedora|rocky|almalinux)
            if command_exists dnf; then
                dnf -y install dnf-plugins-core
                dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
            else
                yum install -y yum-utils
                yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            fi
            systemctl start docker
            systemctl enable docker
            ;;
        *)
            log_error "Unsupported OS for automatic Docker installation: $OS"
            log_info "Please install Docker manually: https://docs.docker.com/get-docker/"
            exit 1
            ;;
    esac
    
    # Start and enable Docker
    if command_exists systemctl; then
        systemctl start docker
        systemctl enable docker
    fi
    
    log_success "Docker installed successfully"
}

# Install Docker for macOS
install_docker_macos() {
    log_error "Please install Docker Desktop for Mac manually"
    log_info "Download from: https://docs.docker.com/desktop/install/mac-install/"
    exit 1
}

# Install Docker
install_docker() {
    if [[ "$OS" == "macos" ]]; then
        install_docker_macos
    else
        install_docker_linux
    fi
}

# Install Docker Compose
install_docker_compose() {
    log_info "Installing Docker Compose..."
    
    # Check if docker compose plugin is available
    if docker compose version >/dev/null 2>&1; then
        log_success "Docker Compose plugin already available"
        DOCKER_COMPOSE="docker compose"
        return
    fi
    
    # Install standalone docker-compose
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' | cut -d'"' -f4)
    if [[ -z "$COMPOSE_VERSION" ]]; then
        COMPOSE_VERSION="v2.23.0"
    fi
    
    curl -sL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose 2>/dev/null || true
    
    DOCKER_COMPOSE="docker-compose"
    log_success "Docker Compose installed successfully"
}

# Check and install dependencies
check_dependencies() {
    log_step "Checking dependencies..."
    
    # Check Docker
    if ! command_exists docker; then
        log_warn "Docker not found. Installing..."
        install_docker
    else
        log_success "Docker is already installed ($(docker --version))"
    fi
    
    # Check Docker Compose
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
        log_success "Docker Compose plugin is available"
    elif command_exists docker-compose; then
        DOCKER_COMPOSE="docker-compose"
        log_success "Docker Compose is already installed ($(docker-compose --version))"
    else
        log_warn "Docker Compose not found. Installing..."
        install_docker_compose
    fi
    
    # Check git
    if ! command_exists git; then
        log_info "Installing git..."
        case $OS in
            ubuntu|debian) apt-get install -y -qq git ;;
            centos|rhel|fedora|rocky|almalinux) 
                if command_exists dnf; then dnf -y install git; else yum -y install git; fi ;;
            macos) brew install git ;;
        esac
    fi
    
    # Check curl
    if ! command_exists curl; then
        log_info "Installing curl..."
        case $OS in
            ubuntu|debian) apt-get install -y -qq curl ;;
            centos|rhel|fedora|rocky|almalinux) 
                if command_exists dnf; then dnf -y install curl; else yum -y install curl; fi ;;
            macos) brew install curl ;;
        esac
    fi
    
    # Check openssl
    if ! command_exists openssl; then
        log_info "Installing openssl..."
        case $OS in
            ubuntu|debian) apt-get install -y -qq openssl ;;
            centos|rhel|fedora|rocky|almalinux) 
                if command_exists dnf; then dnf -y install openssl; else yum -y install openssl; fi ;;
            macos) brew install openssl ;;
        esac
    fi
}

# Generate secure random string
generate_secret() {
    openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
}

# Generate .env file
generate_env() {
    log_step "Generating environment configuration..."
    
    local jwt_secret=$(generate_secret)
    local encryption_key=$(generate_secret)
    local postgres_password=$(generate_secret)
    local redis_password=$(generate_secret)
    
    cat > "$INSTALL_DIR/.env" << EOF
# AI Identity Pro - Environment Configuration
# Generated on $(date)
# ============================================

# Application Settings
APP_NAME=AI Identity Pro
APP_VERSION=2.0.0
APP_ENV=production
APP_DEBUG=false
DOMAIN=$DOMAIN

# Database Configuration
DATABASE_URL=postgresql://postgres:${postgres_password}@postgres:5432/ai_identity
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${postgres_password}
POSTGRES_DB=ai_identity

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=${redis_password}

# Security (KEEP THESE SECRET!)
JWT_SECRET=${jwt_secret}
ENCRYPTION_KEY=${encryption_key}

# API Keys (Update these with your actual keys)
KIMI_API_KEY=${KIMI_API_KEY:-}
STRIPE_API_KEY=${STRIPE_API_KEY:-}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-}

# Email Configuration (Optional)
SENDGRID_API_KEY=${SENDGRID_API_KEY:-}
EMAIL_FROM=${EMAIL_FROM:-noreply@$DOMAIN}

# Monitoring (Optional)
SENTRY_DSN=${SENTRY_DSN:-}

# Frontend URL
NEXT_PUBLIC_API_URL=https://$DOMAIN/api

# Ports (change if needed)
FRONTEND_PORT=3000
BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379
WEAVIATE_PORT=8080
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
EOF

    chmod 600 "$INSTALL_DIR/.env"
    log_success "Environment file created at $INSTALL_DIR/.env"
}

# Clone or update repository
clone_repository() {
    log_step "Setting up application files..."
    
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log_info "Existing installation found. Updating..."
        cd "$INSTALL_DIR"
        git fetch origin
        git reset --hard origin/main
    else
        log_info "Cloning repository..."
        rm -rf "$INSTALL_DIR"
        git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    fi
    
    log_success "Repository ready at $INSTALL_DIR"
}

# Create necessary directories
create_directories() {
    log_step "Creating directories..."
    
    mkdir -p "$INSTALL_DIR/data/postgres"
    mkdir -p "$INSTALL_DIR/data/redis"
    mkdir -p "$INSTALL_DIR/data/weaviate"
    mkdir -p "$INSTALL_DIR/data/ssl"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/backups"
    
    chmod 755 "$INSTALL_DIR/data"
    log_success "Directories created"
}

# Setup SSL certificates
setup_ssl() {
    log_step "Setting up SSL certificates..."
    
    if [[ "$DOMAIN" == "localhost" ]] || [[ "$DOMAIN" == "127.0.0.1" ]]; then
        log_warn "Using self-signed certificates for localhost..."
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$INSTALL_DIR/data/ssl/privkey.pem" \
            -out "$INSTALL_DIR/data/ssl/fullchain.pem" \
            -subj "/CN=$DOMAIN" \
            2>/dev/null
        
        chmod 600 "$INSTALL_DIR/data/ssl/privkey.pem"
        log_warn "Self-signed certificate generated. For production, use Let's Encrypt."
    else
        log_info "SSL will be configured via Let's Encrypt or manual certificates"
        # Create placeholder certs for initial startup
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$INSTALL_DIR/data/ssl/privkey.pem" \
            -out "$INSTALL_DIR/data/ssl/fullchain.pem" \
            -subj "/CN=$DOMAIN" \
            2>/dev/null
        chmod 600 "$INSTALL_DIR/data/ssl/privkey.pem"
    fi
}

# Run database migrations
run_migrations() {
    log_step "Running database migrations..."
    
    cd "$INSTALL_DIR"
    
    # Wait for postgres to be ready
    log_info "Waiting for database to be ready..."
    $DOCKER_COMPOSE up -d postgres
    
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if $DOCKER_COMPOSE exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
            break
        fi
        sleep 2
        ((retries--))
        echo -n "."
    done
    echo ""
    
    if [[ $retries -eq 0 ]]; then
        log_error "Database failed to start"
        exit 1
    fi
    
    log_success "Database is ready"
}

# Health check
health_check() {
    log_step "Performing health checks..."
    
    cd "$INSTALL_DIR"
    
    local services=("postgres" "redis" "backend" "nginx")
    local max_attempts=30
    local attempt=0
    local all_healthy=true
    
    for service in "${services[@]}"; do
        attempt=0
        log_info "Checking $service..."
        
        while [[ $attempt -lt $max_attempts ]]; do
            if $DOCKER_COMPOSE ps "$service" 2>/dev/null | grep -q "healthy\|Up"; then
                log_success "$service is running"
                break
            fi
            sleep 2
            ((attempt++))
            echo -n "."
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_warn "$service failed health check"
            all_healthy=false
        fi
    done
    
    # Test API endpoint
    sleep 5
    if curl -s http://localhost:8000/health >/dev/null 2>&1 || \
       curl -s http://localhost:8000/ >/dev/null 2>&1; then
        log_success "API is responding"
    else
        log_warn "API health check inconclusive (may need more time)"
    fi
    
    if [[ "$all_healthy" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Start services
start_services() {
    log_step "Starting all services..."
    
    cd "$INSTALL_DIR"
    
    # Pull latest images
    $DOCKER_COMPOSE pull
    
    # Build and start
    $DOCKER_COMPOSE up -d --build
    
    log_success "All services started"
}

# Create systemd service
create_systemd_service() {
    log_step "Creating systemd service..."
    
    if [[ "$OS" == "macos" ]]; then
        log_warn "Systemd not available on macOS. Skipping service creation."
        return
    fi
    
    cat > /etc/systemd/system/ai-identity-pro.service << EOF
[Unit]
Description=AI Identity Pro
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR
ExecStart=$DOCKER_COMPOSE up -d
ExecStop=$DOCKER_COMPOSE down
ExecReload=$DOCKER_COMPOSE restart
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable ai-identity-pro.service
    
    log_success "Systemd service created and enabled"
}

# Configure firewall
configure_firewall() {
    log_step "Configuring firewall..."
    
    if [[ "$OS" == "macos" ]]; then
        return
    fi
    
    # UFW (Ubuntu/Debian)
    if command_exists ufw; then
        ufw allow 80/tcp >/dev/null 2>&1 || true
        ufw allow 443/tcp >/dev/null 2>&1 || true
        log_success "UFW rules added"
    fi
    
    # Firewalld (CentOS/RHEL)
    if command_exists firewall-cmd; then
        firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
        firewall-cmd --permanent --add-service=https >/dev/null 2>&1 || true
        firewall-cmd --reload >/dev/null 2>&1 || true
        log_success "Firewalld rules added"
    fi
}

# Print final instructions
print_success() {
    local ip
    if [[ "$OS" == "macos" ]]; then
        ip=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
    else
        ip=$(hostname -I | awk '{print $1}')
    fi
    
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              ✅ Installation Complete!                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${CYAN}🌐 Access your AI Identity Pro instance:${NC}"
    echo ""
    echo "   Web Interface:     http://$DOMAIN (or http://$ip)"
    echo "   API Documentation: http://$DOMAIN/docs"
    echo "   Admin Panel:       http://$DOMAIN/admin"
    echo ""
    
    echo -e "${CYAN}📁 Important Files:${NC}"
    echo ""
    echo "   Configuration:     $INSTALL_DIR/.env"
    echo "   Data Directory:    $INSTALL_DIR/data"
    echo "   Log Files:         $INSTALL_DIR/logs"
    echo ""
    
    echo -e "${CYAN}🔧 Useful Commands:${NC}"
    echo ""
    echo "   View logs:         cd $INSTALL_DIR && $DOCKER_COMPOSE logs -f"
    echo "   Restart services:  cd $INSTALL_DIR && $DOCKER_COMPOSE restart"
    echo "   Stop services:     cd $INSTALL_DIR && $DOCKER_COMPOSE down"
    echo "   Update:            curl -sSL https://aiidentity.pro/update.sh | bash"
    echo ""
    
    echo -e "${YELLOW}⚠️  Next Steps:${NC}"
    echo ""
    echo "   1. Update API keys in $INSTALL_DIR/.env"
    echo "   2. Configure your domain DNS to point to this server ($ip)"
    echo "   3. Setup SSL certificates (Let's Encrypt or custom)"
    echo "   4. Register your first admin account at http://$DOMAIN"
    echo ""
    
    echo -e "${GREEN}📚 Documentation: https://docs.aiidentity.pro${NC}"
    echo ""
}

# Cleanup on error
cleanup() {
    if [[ $? -ne 0 ]]; then
        echo ""
        log_error "Installation failed. Check the logs above for details."
        log_info "For help, visit: https://docs.aiidentity.pro/troubleshooting"
        log_info "To retry, run the installer again."
    fi
}

trap cleanup EXIT

# Main installation flow
main() {
    print_banner
    
    # Check root
    check_root
    
    # Detect OS
    detect_os
    
    # Check and install dependencies
    check_dependencies
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Clone repository
    clone_repository
    
    # Create directories
    create_directories
    
    # Generate environment file
    generate_env
    
    # Setup SSL
    setup_ssl
    
    # Run migrations
    run_migrations
    
    # Start services
    start_services
    
    # Health check
    if health_check; then
        log_success "All health checks passed"
    else
        log_warn "Some health checks failed, but installation completed"
    fi
    
    # Create systemd service
    create_systemd_service
    
    # Configure firewall
    configure_firewall
    
    # Print success message
    print_success
}

# Handle command line arguments
case "${1:-}" in
    --version|-v)
        echo "AI Identity Pro Installer v2.0.0"
        exit 0
        ;;
    --help|-h)
        echo "AI Identity Pro Installer"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --version, -v    Show version"
        echo "  --help, -h       Show this help"
        echo ""
        echo "Environment variables:"
        echo "  INSTALL_DIR      Installation directory (default: /opt/ai-identity-pro)"
        echo "  REPO_URL         Git repository URL"
        echo "  DOMAIN           Domain name (default: localhost)"
        echo "  EMAIL            Admin email (default: admin@localhost)"
        echo ""
        echo "Example:"
        echo "  curl -sSL https://aiidentity.pro/install.sh | sudo DOMAIN=mydomain.com bash"
        exit 0
        ;;
esac

# Run main function
main "$@"
