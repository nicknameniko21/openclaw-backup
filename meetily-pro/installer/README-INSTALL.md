# Meetily Pro - Installation Guide

One-line installer for Meetily Pro - Enterprise Meeting Intelligence Platform.

## 🚀 Quick Start

### Standard Installation

```bash
curl -sSL https://meetily.pro/install.sh | bash
```

### With Custom Domain

```bash
export DOMAIN=your-domain.com
export EMAIL=admin@your-domain.com
export ORGANIZATION_NAME="Your Company"
curl -sSL https://meetily.pro/install.sh | bash
```

### With API Keys

```bash
export KIMI_API_KEY=your_kimi_key
export OPENAI_API_KEY=your_openai_key
curl -sSL https://meetily.pro/install.sh | bash
```

## 📋 Requirements

### Minimum Requirements

- **OS**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or compatible
- **RAM**: 4GB minimum (8GB recommended for transcription)
- **CPU**: 2 cores minimum (4 cores with AVX support recommended)
- **Disk**: 50GB free space (for recordings)
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
| `INSTALL_DIR` | Installation directory | `/opt/meetily-pro` |
| `DOMAIN` | Domain name | `localhost` |
| `EMAIL` | Admin email | `admin@localhost` |
| `ORGANIZATION_NAME` | Organization name | `My Organization` |
| `KIMI_API_KEY` | Kimi API key | (required for summaries) |
| `OPENAI_API_KEY` | OpenAI API key | (alternative for summaries) |

### Example: Full Custom Installation

```bash
# Set all options
export INSTALL_DIR=/var/www/meetily
export DOMAIN=meetings.example.com
export EMAIL=admin@example.com
export ORGANIZATION_NAME="Acme Corp"
export KIMI_API_KEY=sk-your-kimi-key
export SLACK_CLIENT_ID=your-slack-client-id
export ZOOM_CLIENT_ID=your-zoom-client-id

# Run installer
curl -sSL https://meetily.pro/install.sh | bash
```

## 📁 Directory Structure

After installation, the following structure is created:

```
/opt/meetily-pro/
├── .env                    # Environment configuration
├── .version                # Installed version
├── .admin-credentials      # Admin login (keep secure!)
├── docker-compose.yml      # Docker configuration
├── backend/                # Backend source
├── storage/                # Meeting recordings & files
│   ├── recordings/        # Audio/video files
│   └── transcripts/       # Generated transcripts
├── data/                   # Persistent data
│   ├── postgres/          # Database files
│   ├── redis/             # Cache files
│   ├── minio/             # Object storage
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
   curl -sSL https://meetily.pro/install.sh | bash
   ```

### Manual SSL Certificates

To use your own certificates:

```bash
# Place certificates in the SSL directory
sudo cp your-cert.pem /opt/meetily-pro/data/ssl/fullchain.pem
sudo cp your-key.pem /opt/meetily-pro/data/ssl/privkey.pem
sudo chmod 600 /opt/meetily-pro/data/ssl/privkey.pem

# Restart nginx
sudo docker compose -C /opt/meetily-pro restart nginx
```

### Self-Signed (Development)

For local development, self-signed certificates are automatically generated.

## 🔄 Updating

### Automatic Update

```bash
curl -sSL https://meetily.pro/update.sh | bash
```

### Manual Update

```bash
cd /opt/meetily-pro
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
cd /opt/meetily-pro
sudo ./backup.sh
```

### Manual Backup

```bash
# Backup database
docker exec meetily-postgres pg_dumpall -U postgres > backup.sql

# Backup environment
cp /opt/meetily-pro/.env .env.backup

# Backup storage
tar czf storage-backup.tar.gz /opt/meetily-pro/storage

# Backup data
tar czf data-backup.tar.gz /opt/meetily-pro/data
```

### Restore from Backup

```bash
# Restore database
docker exec -i meetily-postgres psql -U postgres < backup.sql

# Restore environment
sudo cp .env.backup /opt/meetily-pro/.env

# Restore storage
sudo tar xzf storage-backup.tar.gz -C /

# Restart services
cd /opt/meetily-pro
sudo docker compose restart
```

## 🗑️ Uninstallation

### Complete Removal

⚠️ **Warning**: This will permanently delete all data including meeting recordings!

```bash
curl -sSL https://meetily.pro/uninstall.sh | bash
```

### Manual Uninstallation

```bash
cd /opt/meetily-pro
sudo ./installer/uninstall.sh
```

## 🐛 Troubleshooting

### Check Service Status

```bash
cd /opt/meetily-pro
sudo docker compose ps
```

### View Logs

```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f backend
sudo docker compose logs -f postgres
sudo docker compose logs -f nginx
```

### Restart Services

```bash
cd /opt/meetily-pro
sudo docker compose restart
```

### Reset Database

⚠️ **Warning**: This deletes all data!

```bash
cd /opt/meetily-pro
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
sudo chown -R root:root /opt/meetily-pro
sudo chmod -R 755 /opt/meetily-pro
```

#### Docker Not Running

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

#### Transcription Not Working

```bash
# Check Whisper model is downloaded
sudo docker compose exec backend ls -la /app/models/

# Check GPU support (if applicable)
nvidia-smi
```

## 🔧 Configuration

### Environment Variables

Edit `/opt/meetily-pro/.env` to customize:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/meetily_pro
POSTGRES_PASSWORD=your-secure-password

# Security
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key

# API Keys
KIMI_API_KEY=your-kimi-api-key
OPENAI_API_KEY=your-openai-key

# Transcription
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_DEVICE=cpu  # cpu or cuda

# Storage
STORAGE_TYPE=local  # local or s3
AWS_S3_BUCKET=your-bucket

# Compliance
ENABLE_AUDIT_LOG=true
DATA_RETENTION_DAYS=365
GDPR_COMPLIANT=true
```

### Port Configuration

To use different ports, edit `.env`:

```bash
BACKEND_PORT=8001
POSTGRES_PORT=5433
REDIS_PORT=6380
MINIO_PORT=9000
NGINX_HTTP_PORT=8080
NGINX_HTTPS_PORT=8443
```

Then restart:

```bash
cd /opt/meetily-pro
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

## 🔗 Integrations

### Slack

1. Create a Slack app at https://api.slack.com/apps
2. Add to `.env`:
   ```bash
   SLACK_CLIENT_ID=your-client-id
   SLACK_CLIENT_SECRET=your-client-secret
   ```
3. Restart: `sudo docker compose restart`

### Zoom

1. Create a Zoom app at https://marketplace.zoom.us/
2. Add to `.env`:
   ```bash
   ZOOM_CLIENT_ID=your-client-id
   ZOOM_CLIENT_SECRET=your-client-secret
   ```

### Google Calendar

1. Create OAuth credentials at https://console.cloud.google.com/
2. Add to `.env`:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

## 🆘 Support

- **Documentation**: https://docs.meetily.pro
- **API Reference**: https://api.meetily.pro/docs
- **Support Email**: support@meetily.pro
- **Enterprise**: enterprise@meetily.pro

## 📜 License

Commercial License - All rights reserved.

---

**Meetily Pro** - Enterprise Meeting Intelligence Platform  
*Built with 🔒 by the Meetily Pro Team*
