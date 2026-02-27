#!/bin/bash
#
# Meetily Pro - One-Line Installer
# Usage: curl -sSL https://meetily.pro/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/opt/meetily-pro}"
REPO_URL="${REPO_URL:-https://github.com/meetily/meetily-pro.git}"
VERSION="${VERSION:-latest}"
DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@localhost}"
ORGANIZATION_NAME="${ORGANIZATION_NAME:-My Organization}"

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
    echo "║           🎤 Meetily Pro Installer v2.0.0                   ║"
    echo "║                                                              ║"
    echo "║     Enterprise Meeting Intelligence Platform                 ║"
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
    local admin_password=$(generate_secret | cut -c1-16)
    
    cat > "$INSTALL_DIR/.env" << EOF
# Meetily Pro - Environment Configuration
# Generated on $(date)

# Application Settings
APP_NAME=Meetily Pro
APP_VERSION=2.0.0
APP_ENV=production
APP_DEBUG=false
DOMAIN=$DOMAIN
ORGANIZATION_NAME="$ORGANIZATION_NAME"

# Database Configuration
DATABASE_URL=postgresql://postgres:$(generate_secret)@postgres:5432/meetily_pro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(generate_secret)
POSTGRES_DB=meetily_pro

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=$(generate_secret)

# Security
JWT_SECRET=$jwt_secret
ENCRYPTION_KEY=$encryption_key

# Admin User (created on first run)
ADMIN_EMAIL=$EMAIL
ADMIN_PASSWORD=$admin_password

# API Keys (Update these with your actual keys)
KIMI_API_KEY=${KIMI_API_KEY:-your_kimi_api_key_here}
OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_api_key_here}

# Transcription Service
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# Integrations (Optional)
SLACK_CLIENT_ID=${SLACK_CLIENT_ID:-}
SLACK_CLIENT_SECRET=${SLACK_CLIENT_SECRET:-}
ZOOM_CLIENT_ID=${ZOOM_CLIENT_ID:-}
ZOOM_CLIENT_SECRET=${ZOOM_CLIENT_SECRET:-}
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-}
MICROSOFT_CLIENT_ID=${MICROSOFT_CLIENT_ID:-}
MICROSOFT_CLIENT_SECRET=${MICROSOFT_CLIENT_SECRET:-}

# Email Configuration (Optional)
SENDGRID_API_KEY=${SENDGRID_API_KEY:-}
EMAIL_FROM=${EMAIL_FROM:-noreply@$DOMAIN}
EMAIL_SMTP_HOST=${EMAIL_SMTP_HOST:-}
EMAIL_SMTP_PORT=${EMAIL_SMTP_PORT:-587}
EMAIL_SMTP_USER=${EMAIL_SMTP_USER:-}
EMAIL_SMTP_PASS=${EMAIL_SMTP_PASS:-}

# Storage Configuration
STORAGE_TYPE=local
STORAGE_PATH=/app/storage
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}
AWS_S3_BUCKET=${AWS_S3_BUCKET:-}
AWS_REGION=${AWS_REGION:-us-east-1}

# Monitoring (Optional)
SENTRY_DSN=${SENTRY_DSN:-}

# Compliance
ENABLE_AUDIT_LOG=true
DATA_RETENTION_DAYS=365
GDPR_COMPLIANT=true

# Ports (change if needed)
BACKEND_PORT=8001
POSTGRES_PORT=5433
REDIS_PORT=6380
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# WebSocket
WS_PORT=8002
EOF

    chmod 600 "$INSTALL_DIR/.env"
    
    # Save admin credentials
    cat > "$INSTALL_DIR/.admin-credentials" << EOF
# Meetily Pro Admin Credentials
# Generated on $(date)
# KEEP THIS FILE SECURE!

Admin Email: $EMAIL
Admin Password: $admin_password

Login URL: https://$DOMAIN/login
EOF
    
    chmod 600 "$INSTALL_DIR/.admin-credentials"
    
    log_success "Environment file created at $INSTALL_DIR/.env"
    log_warn "Admin credentials saved to $INSTALL_DIR/.admin-credentials"
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
    mkdir -p "$INSTALL_DIR/data/minio"
    mkdir -p "$INSTALL_DIR/data/ssl"
    mkdir -p "$INSTALL_DIR/storage/recordings"
    mkdir -p "$INSTALL_DIR/storage/transcripts"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/backups"
    
    chmod 755 "$INSTALL_DIR/data"
    chmod 755 "$INSTALL_DIR/storage"
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

# Initialize organization
initialize_organization() {
    log_info "Initializing organization..."
    
    # This will be done by the backend on first startup
    log_info "Organization will be created on first admin login"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    cd "$INSTALL_DIR"
    
    local services=("postgres" "redis" "backend" "nginx")
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
    if curl -s http://localhost:8001/health >/dev/null 2>&1 || \
       curl -s http://localhost:8001/ >/dev/null 2>&1; then
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
    
    cat > /etc/systemd/system/meetily-pro.service << EOF
[Unit]
Description=Meetily Pro
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
    systemctl enable meetily-pro.service
    
    log_success "Systemd service created and enabled"
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    # UFW (Ubuntu/Debian)
    if command_exists ufw; then
        ufw allow 80/tcp
        ufw allow 443/tcp
        log_success "UFW rules added"
    fi
    
    # Firewalld (CentOS/RHEL)
    if command_exists firewall-cmd; then
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        log_success "Firewalld rules added"
    fi
}

# Print final instructions
print_success() {
    local ip=$(hostname -I | awk '{print $1}')
    
    # Read admin credentials
    local admin_email="$EMAIL"
    local admin_pass=""
    if [[ -f "$INSTALL_DIR/.admin-credentials" ]]; then
        admin_pass=$(grep "Admin Password:" "$INSTALL_DIR/.admin-credentials" | cut -d: -f2 | xargs)
    fi
    
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              ✅ Installation Complete!                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}Access your Meetily Pro instance:${NC}"
    echo ""
    echo "  🌐 Web Interface:    http://$DOMAIN (or http://$ip)"
    echo "  📚 API Documentation: http://$DOMAIN/docs"
    echo "  🔧 Admin Login:      http://$DOMAIN/login"
    echo ""
    
    if [[ -n "$admin_pass" ]]; then
        echo -e "${YELLOW}Admin Credentials:${NC}"
        echo "  Email:    $admin_email"
        echo "  Password: $admin_pass"
        echo ""
        echo -e "${RED}⚠️  IMPORTANT: Save these credentials! They won't be shown again.${NC}"
        echo "   Location: $INSTALL_DIR/.admin-credentials"
        echo ""
    fi
    
    echo -e "${BLUE}Useful commands:${NC}"
    echo ""
    echo "  View logs:           cd $INSTALL_DIR && $DOCKER_COMPOSE logs -f"
    echo "  Restart services:    cd $INSTALL_DIR && $DOCKER_COMPOSE restart"
    echo "  Stop services:       cd $INSTALL_DIR && $DOCKER_COMPOSE down"
    echo "  Update:              curl -sSL https://meetily.pro/update.sh | bash"
    echo "  Backup:              $INSTALL_DIR/backup.sh"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "  • Configuration file: $INSTALL_DIR/.env"
    echo "  • Data directory:     $INSTALL_DIR/data"
    echo "  • Log files:          $INSTALL_DIR/logs"
    echo "  • Recordings:         $INSTALL_DIR/storage/recordings"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Update API keys in $INSTALL_DIR/.env"
    echo "  2. Configure your domain DNS to point to this server"
    echo "  3. Run 'certbot' to get SSL certificates (if not auto-configured)"
    echo "  4. Login with admin credentials and complete setup"
    echo "  5. Invite team members and configure integrations"
    echo ""
    echo -e "${GREEN}For support, visit: https://docs.meetily.pro${NC}"
    echo ""
}

# Cleanup on error
cleanup() {
    if [[ $? -ne 0 ]]; then
        log_error "Installation failed. Check the logs above for details."
        log_info "For help, visit: https://docs.meetily.pro/troubleshooting"
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
    
    # Initialize organization
    initialize_organization
    
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

# Run main function
main "$@"
