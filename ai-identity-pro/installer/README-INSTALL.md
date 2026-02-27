# AI Identity Pro - Installation Guide

One-line installer for AI Identity Pro - Premium Digital Twin Platform.

## 🚀 Quick Start

### Standard Installation

```bash
curl -sSL https://aiidentity.pro/install.sh | bash
```

### With Custom Domain

```bash
export DOMAIN=your-domain.com
export EMAIL=admin@your-domain.com
curl -sSL https://aiidentity.pro/install.sh | bash
```

### With API Keys

```bash
export KIMI_API_KEY=your_kimi_key
export STRIPE_API_KEY=your_stripe_key
curl -sSL https://aiidentity.pro/install.sh | bash
```

## 📋 Requirements

### Minimum Requirements

- **OS**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or compatible
- **RAM**: 4GB minimum (8GB recommended)
- **CPU**: 2 cores minimum (4 cores recommended)
- **Disk**: 20GB free space
- **Network**: Internet connection for installation

### Supported Operating Systems

| OS | Version | Status |
|----|---------|--------|
| Ubuntu | 20.04, 22.04, 24.04 | ✅ Fully Supported |
| Debian | 11, 12 | ✅ Fully Supported |
| CentOS | 8, 9 | ✅ Fully Supported |
| RHEL | 8, 9 | ✅ Fully Supported |
| Fedora | 38+ | ✅ Supported |
| Amazon Linux | 2, 2023 | ⚠️ Best Effort |

## 🔧 Installation Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INSTALL_DIR` | Installation directory | `/opt/ai-identity-pro` |
| `DOMAIN` | Domain name | `localhost` |
| `EMAIL` | Admin email | `admin@localhost` |
| `KIMI_API_KEY` | Kimi API key | (required for AI features) |
| `STRIPE_API_KEY` | Stripe API key | (required for billing) |
| `VERSION` | Version to install | `latest` |

### Example: Full Custom Installation

```bash
# Set all options
export INSTALL_DIR=/var/www/ai-identity
export DOMAIN=ai.example.com
export EMAIL=admin@example.com
export KIMI_API_KEY=sk-your-kimi-key
export STRIPE_API_KEY=sk_live_your_stripe_key

# Run installer
curl -sSL https://aiidentity.pro/install.sh | bash
```

## 📁 Directory Structure

After installation, the following structure is created:

```
/opt/ai-identity-pro/
├── .env                    # Environment configuration
├── .version                # Installed version
├── docker-compose.yml      # Docker configuration
├── frontend/               # Frontend source
├── backend/                # Backend source
├── data/                   # Persistent data
│   ├── postgres/          # Database files
│   ├── redis/             # Cache files
│   ├── weaviate/          # Vector database
│   └── ssl/               # SSL certificates
├── logs/                   # Application logs
├── backups/                # Backup storage
└── installer/             # Installer files
    ├── install.sh
    ├── uninstall.sh
    ├── update.sh
    ├── docker-compose.yml
    └── nginx/
```

## 🔐 SSL Configuration

### Automatic Let's Encrypt (Production)

The installer automatically configures Let's Encrypt for production domains:

1. Ensure your domain points to the server IP
2. Run the installer with your domain:
   ```bash
   export DOMAIN=your-domain.com
   curl -sSL https://aiidentity.pro/install.sh | bash
   ```

### Manual SSL Certificates

To use your own certificates:

```bash
# Place certificates in the SSL directory
sudo cp your-cert.pem /opt/ai-identity-pro/data/ssl/fullchain.pem
sudo cp your-key.pem /opt/ai-identity-pro/data/ssl/privkey.pem
sudo chmod 600 /opt/ai-identity-pro/data/ssl/privkey.pem

# Restart nginx
sudo docker compose -C /opt/ai-identity-pro restart nginx
```

### Self-Signed (Development)

For local development, self-signed certificates are automatically generated.

## 🔄 Updating

### Automatic Update

```bash
curl -sSL https://aiidentity.pro/update.sh | bash
```

### Manual Update

```bash
cd /opt/ai-identity-pro
sudo ./installer/update.sh
```

### Update Process

1. Creates backup of current installation
2. Pulls latest code from repository
3. Updates Docker images
4. Runs database migrations
5. Restarts services
6. Performs health checks

## 💾 Backup & Restore

### Create Backup

```bash
cd /opt/ai-identity-pro
sudo ./backup.sh
```

### Manual Backup

```bash
# Backup database
docker exec aip-postgres pg_dumpall -U postgres > backup.sql

# Backup environment
cp /opt/ai-identity-pro/.env .env.backup

# Backup data
tar czf data-backup.tar.gz /opt/ai-identity-pro/data
```

### Restore from Backup

```bash
# Restore database
docker exec -i aip-postgres psql -U postgres < backup.sql

# Restore environment
sudo cp .env.backup /opt/ai-identity-pro/.env

# Restart services
cd /opt/ai-identity-pro
sudo docker compose restart
```

## 🗑️ Uninstallation

### Complete Removal

⚠️ **Warning**: This will permanently delete all data!

```bash
curl -sSL https://aiidentity.pro/uninstall.sh | bash
```

### Manual Uninstallation

```bash
cd /opt/ai-identity-pro
sudo ./installer/uninstall.sh
```

## 🐛 Troubleshooting

### Check Service Status

```bash
cd /opt/ai-identity-pro
sudo docker compose ps
```

### View Logs

```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f backend
sudo docker compose logs -f frontend
sudo docker compose logs -f postgres
```

### Restart Services

```bash
cd /opt/ai-identity-pro
sudo docker compose restart
```

### Reset Database

⚠️ **Warning**: This deletes all data!

```bash
cd /opt/ai-identity-pro
sudo docker compose down -v
sudo rm -rf data/postgres/*
sudo docker compose up -d
```

### Common Issues

#### Port Already in Use

```bash
# Check what's using port 80/443
sudo netstat -tlnp | grep -E ':(80|443)'

# Stop conflicting service or change ports in .env
```

#### Permission Denied

```bash
# Fix permissions
sudo chown -R root:root /opt/ai-identity-pro
sudo chmod -R 755 /opt/ai-identity-pro
```

#### Docker Not Running

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

## 🔧 Configuration

### Environment Variables

Edit `/opt/ai-identity-pro/.env` to customize:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_identity
POSTGRES_PASSWORD=your-secure-password

# Security
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key

# API Keys
KIMI_API_KEY=your-kimi-api-key
STRIPE_API_KEY=your-stripe-key

# Email
SENDGRID_API_KEY=your-sendgrid-key
EMAIL_FROM=noreply@your-domain.com
```

### Port Configuration

To use different ports, edit `.env`:

```bash
FRONTEND_PORT=3000
BACKEND_PORT=8000
POSTGRES_PORT=5432
NGINX_HTTP_PORT=8080
NGINX_HTTPS_PORT=8443
```

Then restart:

```bash
cd /opt/ai-identity-pro
sudo docker compose restart
```

## 📊 Monitoring

### Health Check

```bash
curl http://localhost/health
curl http://localhost/api/health
```

### Resource Usage

```bash
# Docker stats
sudo docker stats

# System resources
htop
```

## 🆘 Support

- **Documentation**: https://docs.aiidentity.pro
- **API Reference**: https://api.aiidentity.pro/docs
- **Support Email**: support@aiidentity.pro
- **Discord**: https://discord.gg/aiidentity

## 📜 License

Commercial License - All rights reserved.

---

**AI Identity Pro** - Premium Digital Twin Platform  
*Built with ❤️ by the AI Identity Pro Team*
