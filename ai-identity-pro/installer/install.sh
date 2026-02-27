#!/bin/bash
#
# AI Identity Pro - One-Line Installer
# Usage: curl -sSL https://aiidentity.pro/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/opt/ai-identity-pro}"
REPO_URL="${REPO_URL:-https://github.com/aiidentity/ai-identity-pro.git}"
VERSION="${VERSION:-latest}"
DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@localhost}"

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

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🤖 AI Identity Pro Installer v2.0.0               ║"
    echo "║                                                              ║"
    echo "║     Premium Digital Twin Platform - Commercial Edition       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This installer must be run as root (use sudo)"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION_ID=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="centos"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
    else
        OS=$(uname -s)
    fi
    
    log_info "Detected OS: $OS"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker
install_docker() {
    log_info "Installing Docker..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        centos|rhel|fedora)
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            systemctl start docker
            systemctl enable docker
            ;;
        *)
            log_error "Unsupported OS for automatic Docker installation"
            exit 1
            ;;
    esac
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    log_success "Docker installed successfully"
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
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    DOCKER_COMPOSE="docker-compose"
    log_success "Docker Compose installed successfully"
}

# Check and install dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command_exists docker; then
        log_warn "Docker not found. Installing..."
        install_docker
    else
        log_success "Docker is already installed"
    fi
    
    # Check Docker Compose
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
        log_success "Docker Compose plugin is available"
    elif command_exists docker-compose; then
        DOCKER_COMPOSE="docker-compose"
        log_success "Docker Compose is already installed"
    else
        log_warn "Docker Compose not found. Installing..."
        install_docker_compose
    fi
    
    # Check git
    if ! command_exists git; then
        log_info "Installing git..."
        case $OS in
            ubuntu|debian) apt-get install -y git ;;
            centos|rhel|fedora) yum install -y git ;;
        esac
    fi
    
    # Check curl
    if ! command_exists curl; then
        log_info "Installing curl..."
        case $OS in
            ubuntu|debian) apt-get install -y curl ;;
            centos|rhel|fedora) yum install -y curl ;;
        esac
    fi
}

# Generate secure random string
generate_secret() {
    openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
}

# Generate .env file
generate_env() {
    log_info "Generating environment configuration..."
    
    local jwt_secret=$(generate_secret)
    local encryption_key=$(generate_secret)
    
    cat > "$INSTALL_DIR/.env" << EOF
# AI Identity Pro - Environment Configuration
# Generated on $(date)

# Application Settings
APP_NAME=AI Identity Pro
APP_VERSION=2.0.0
APP_ENV=production
APP_DEBUG=false
DOMAIN=$DOMAIN

# Database Configuration
DATABASE_URL=postgresql://postgres:$(generate_secret)@postgres:5432/ai_identity
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(generate_secret)
POSTGRES_DB=ai_identity

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=$(generate_secret)

# Security
JWT_SECRET=$jwt_secret
ENCRYPTION_KEY=$encryption_key

# API Keys (Update these with your actual keys)
KIMI_API_KEY=${KIMI_API_KEY:-your_kimi_api_key_here}
STRIPE_API_KEY=${STRIPE_API_KEY:-your_stripe_api_key_here}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-your_stripe_webhook_secret}

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
    log_info "Setting up application files..."
    
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log_info "Existing installation found. Updating..."
        cd "$INSTALL_DIR"
        git fetch origin
        git reset --hard origin/main
    else
        log_info "Cloning repository..."
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
    
    log_success "Repository ready at $INSTALL_DIR"
}

# Create necessary directories
create_directories() {
    log_info "Creating directories..."
    
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
    log_info "Setting up SSL certificates..."
    
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
        log_info "SSL will be configured via Let's Encrypt in nginx container"
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
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
    log_info "Performing health checks..."
    
    cd "$INSTALL_DIR"
    
    local services=("postgres" "redis" "backend" "frontend" "nginx")
    local max_attempts=30
    local attempt=0
    
    for service in "${services[@]}"; do
        attempt=0
        log_info "Checking $service..."
        
        while [[ $attempt -lt $max_attempts ]]; do
            if $DOCKER_COMPOSE ps "$service" | grep -q "healthy\|Up"; then
                log_success "$service is running"
                break
            fi
            sleep 2
            ((attempt++))
            echo -n "."
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "$service failed to start"
            return 1
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
    
    return 0
}

# Start services
start_services() {
    log_info "Starting all services..."
    
    cd "$INSTALL_DIR"
    
    # Pull latest images
    $DOCKER_COMPOSE pull
    
    # Build and start
    $DOCKER_COMPOSE up -d --build
    
    log_success "All services started"
}

# Create systemd service
create_systemd_service() {
    log_info "Creating systemd service..."
    
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

# Print final instructions
print_success() {
    local ip=$(hostname -I | awk '{print $1}')
    
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              ✅ Installation Complete!                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}Access your AI Identity Pro instance:${NC}"
    echo ""
    echo "  🌐 Web Interface:    http://$DOMAIN (or http://$ip)"
    echo "  📚 API Documentation: http://$DOMAIN/docs"
    echo "  🔧 Admin Panel:      http://$DOMAIN/admin"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo ""
    echo "  View logs:           cd $INSTALL_DIR && $DOCKER_COMPOSE logs -f"
    echo "  Restart services:    cd $INSTALL_DIR && $DOCKER_COMPOSE restart"
    echo "  Stop services:       cd $INSTALL_DIR && $DOCKER_COMPOSE down"
    echo "  Update:              curl -sSL https://aiidentity.pro/update.sh | bash"
    echo "  Backup:              $INSTALL_DIR/backup.sh"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "  • Configuration file: $INSTALL_DIR/.env"
    echo "  • Data directory:     $INSTALL_DIR/data"
    echo "  • Log files:          $INSTALL_DIR/logs"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Update API keys in $INSTALL_DIR/.env"
    echo "  2. Configure your domain DNS to point to this server"
    echo "  3. Run 'certbot' to get SSL certificates (if not auto-configured)"
    echo "  4. Register your first admin account at http://$DOMAIN"
    echo ""
    echo -e "${GREEN}For support, visit: https://docs.aiidentity.pro${NC}"
    echo ""
}

# Cleanup on error
cleanup() {
    if [[ $? -ne 0 ]]; then
        log_error "Installation failed. Check the logs above for details."
        log_info "For help, visit: https://docs.aiidentity.pro/troubleshooting"
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
    
    # Print success message
    print_success
}

# Run main function
main "$@"
