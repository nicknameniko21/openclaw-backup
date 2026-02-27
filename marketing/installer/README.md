# AI Identity Pro & Meetily Pro - Installation Guide

Production-ready one-click installers for AI Identity Pro and Meetily Pro platforms.

---

## 📦 Products

### AI Identity Pro
Premium Digital Twin Platform - Create AI-powered digital twins for your business.

### Meetily Pro
Enterprise Meeting Intelligence Platform - Transcribe, analyze, and extract insights from meetings.

---

## 🚀 Quick Start

### AI Identity Pro - One-Line Installation

```bash
curl -sSL https://aiidentity.pro/install.sh | sudo bash
```

With custom domain:
```bash
curl -sSL https://aiidentity.pro/install.sh | sudo DOMAIN=yourdomain.com EMAIL=admin@yourdomain.com bash
```

### Meetily Pro - One-Line Installation

```bash
curl -sSL https://meetily.pro/install.sh | sudo bash
```

With custom domain and organization:
```bash
curl -sSL https://meetily.pro/install.sh | sudo DOMAIN=yourdomain.com EMAIL=admin@yourdomain.com ORGANIZATION_NAME="My Company" bash
```

---

## 📋 System Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+, Fedora 34+, or macOS 12+
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB free space
- **Network**: Internet connection for installation

### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS or Debian 12
- **CPU**: 4+ cores
- **RAM**: 8 GB+
- **Storage**: 50 GB+ SSD
- **Network**: Static IP address, domain name configured

### Dependencies (Auto-Installed)
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- curl
- openssl

---

## 🔧 Installation Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INSTALL_DIR` | Installation directory | `/opt/ai-identity-pro` or `/opt/meetily-pro` |
| `DOMAIN` | Domain name | `localhost` |
| `EMAIL` | Admin email | `admin@localhost` |
| `REPO_URL` | Git repository URL | GitHub repo |
| `ORGANIZATION_NAME` | Organization name (Meetily) | `My Organization` |

### Example: Custom Installation

```bash
# AI Identity Pro with custom settings
sudo INSTALL_DIR=/var/www/ai-identity DOMAIN=ai.example.com EMAIL=admin@example.com bash install.sh

# Meetily Pro with custom settings
sudo INSTALL_DIR=/var/www/meetily DOMAIN=meetings.example.com EMAIL=admin@example.com ORGANIZATION_NAME="Acme Corp" bash install.sh
```

---

## 📁 Installation Structure

After installation, you'll find:

```
/opt/[product]/
├── .env                    # Environment configuration
├── .admin-credentials      # Admin credentials (Meetily only)
├── docker-compose.yml      # Docker Compose configuration
├── data/                   # Persistent data
│   ├── postgres/          # Database files
│   ├── redis/             # Cache files
│   ├── weaviate/          # Vector DB files (AI Identity)
│   ├── minio/             # Object storage (Meetily)
│   └── ssl/               # SSL certificates
├── logs/                  # Application logs
├── backups/               # Backup directory
└── storage/               # File storage (Meetily)
```

---

## 🔐 SSL Configuration

### Option 1: Let's Encrypt (Recommended for Production)

The installer creates a self-signed certificate initially. To use Let's Encrypt:

```bash
# Run certbot container
cd /opt/[product]
docker compose -f docker-compose.yml --profile ssl up -d certbot

# Or manually obtain certificates
certbot certonly --standalone -d yourdomain.com
```

### Option 2: Custom Certificates

Place your certificates in:
```
/opt/[product]/data/ssl/
├── fullchain.pem
└── privkey.pem
```

Then restart:
```bash
cd /opt/[product] && docker compose restart nginx
```

---

## 🔄 Updating

### Automatic Update

```bash
# AI Identity Pro
curl -sSL https://aiidentity.pro/update.sh | sudo bash

# Meetily Pro
curl -sSL https://meetily.pro/update.sh | sudo bash
```

### Manual Update

```bash
cd /opt/[product]
git pull
docker compose pull
docker compose up -d --build
```

---

## 🗑️ Uninstallation

### Automatic Uninstall

```bash
# AI Identity Pro
curl -sSL https://aiidentity.pro/uninstall.sh | sudo bash

# Meetily Pro
curl -sSL https://meetily.pro/uninstall.sh | sudo bash
```

### Manual Uninstall

```bash
cd /opt/[product]
docker compose down -v
sudo rm -rf /opt/[product]
sudo rm -f /etc/systemd/system/[product].service
```

**⚠️ Warning**: Uninstallation permanently deletes all data. A backup is created before removal.

---

## 🔧 Configuration

### Environment Variables (.env)

Key configuration options in `/opt/[product]/.env`:

#### AI Identity Pro
```bash
# Application
APP_NAME=AI Identity Pro
DOMAIN=yourdomain.com

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_identity
POSTGRES_PASSWORD=your_secure_password

# Security
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key

# API Keys
KIMI_API_KEY=your_kimi_key
STRIPE_API_KEY=your_stripe_key

# Email
SENDGRID_API_KEY=your_sendgrid_key
EMAIL_FROM=noreply@yourdomain.com
```

#### Meetily Pro
```bash
# Application
APP_NAME=Meetily Pro
DOMAIN=yourdomain.com
ORGANIZATION_NAME=Your Company

# Admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your_admin_password

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/meetily_pro

# Integrations
SLACK_CLIENT_ID=your_slack_id
ZOOM_CLIENT_ID=your_zoom_id
GOOGLE_CLIENT_ID=your_google_id

# Storage
STORAGE_TYPE=local
# Or AWS S3:
# STORAGE_TYPE=s3
# AWS_ACCESS_KEY_ID=your_key
# AWS_S3_BUCKET=your_bucket
```

### Restart After Configuration Changes

```bash
cd /opt/[product]
docker compose restart
```

---

## 🛠️ Troubleshooting

### Installation Issues

#### Docker Not Found
```bash
# Install Docker manually
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

#### Port Conflicts
If ports 80/443 are in use:
```bash
# Edit .env to use different ports
NGINX_HTTP_PORT=8080
NGINX_HTTPS_PORT=8443
```

#### Permission Denied
```bash
# Ensure you're running as root or with sudo
sudo bash install.sh
```

### Service Issues

#### Check Service Status
```bash
cd /opt/[product]
docker compose ps
docker compose logs
```

#### Restart Services
```bash
cd /opt/[product]
docker compose restart
```

#### Reset Database
```bash
cd /opt/[product]
docker compose down -v
docker compose up -d
```

### Common Errors

#### "Database connection failed"
- Check if postgres container is running: `docker ps | grep postgres`
- Check logs: `docker compose logs postgres`
- Verify DATABASE_URL in .env

#### "SSL certificate error"
- Check certificate files exist in `data/ssl/`
- Verify file permissions (600 for private key)
- Check nginx logs: `docker compose logs nginx`

#### "502 Bad Gateway"
- Backend may not be ready yet (wait 30 seconds)
- Check backend logs: `docker compose logs backend`
- Verify backend health: `curl http://localhost:8000/health`

---

## 📊 Monitoring

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f postgres
```

### Resource Usage
```bash
docker stats
```

### Health Checks
```bash
# AI Identity Pro
curl http://localhost:8000/health

# Meetily Pro
curl http://localhost:8001/health
```

---

## 🔒 Security Best Practices

1. **Change Default Passwords**: Update all generated secrets in `.env`
2. **Use HTTPS**: Configure SSL certificates for production
3. **Firewall**: Only open ports 80 and 443 (done automatically)
4. **Regular Updates**: Keep the system updated
5. **Backups**: Regularly backup your data directory
6. **API Keys**: Store API keys securely, rotate regularly

---

## 📞 Support

- **Documentation**: https://docs.aiidentity.pro or https://docs.meetily.pro
- **Issues**: GitHub Issues page
- **Email**: support@aiidentity.pro or support@meetily.pro

---

## 📄 License

These installers are provided as part of the AI Identity Pro and Meetily Pro commercial licenses.

---

## 🙏 Credits

Built with:
- Docker & Docker Compose
- Nginx
- PostgreSQL
- Redis
- Let's Encrypt (Certbot)
