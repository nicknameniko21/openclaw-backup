# 🚀 One-Click Installer Quick Reference

## AI Identity Pro

### Install
```bash
curl -sSL https://aiidentity.pro/install.sh | bash
```

### With Options
```bash
export DOMAIN=ai.example.com
export EMAIL=admin@example.com
export KIMI_API_KEY=sk-your-key
curl -sSL https://aiidentity.pro/install.sh | bash
```

### Update
```bash
curl -sSL https://aiidentity.pro/update.sh | bash
```

### Uninstall
```bash
curl -sSL https://aiidentity.pro/uninstall.sh | bash
```

---

## Meetily Pro

### Install
```bash
curl -sSL https://meetily.pro/install.sh | bash
```

### With Options
```bash
export DOMAIN=meetings.example.com
export EMAIL=admin@example.com
export ORGANIZATION_NAME="Acme Corp"
export KIMI_API_KEY=sk-your-key
curl -sSL https://meetily.pro/install.sh | bash
```

### Update
```bash
curl -sSL https://meetily.pro/update.sh | bash
```

### Uninstall
```bash
curl -sSL https://meetily.pro/uninstall.sh | bash
```

---

## Post-Installation Commands

### View Logs
```bash
cd /opt/ai-identity-pro  # or /opt/meetily-pro
docker compose logs -f
```

### Restart Services
```bash
cd /opt/ai-identity-pro  # or /opt/meetily-pro
docker compose restart
```

### Check Status
```bash
cd /opt/ai-identity-pro  # or /opt/meetily-pro
docker compose ps
```

### Access Admin Credentials
```bash
# AI Identity Pro
cat /opt/ai-identity-pro/.env | grep ADMIN

# Meetily Pro
cat /opt/meetily-pro/.admin-credentials
```

---

## System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 4 GB | 8 GB |
| CPU | 2 cores | 4 cores |
| Disk | 20 GB | 50 GB |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

---

## Access URLs

After installation:

| Service | URL |
|---------|-----|
| Web Interface | `http://your-domain` |
| API Docs | `http://your-domain/docs` |
| Health Check | `http://your-domain/health` |

---

## File Locations

| Path | Description |
|------|-------------|
| `/opt/ai-identity-pro` | AI Identity Pro installation |
| `/opt/meetily-pro` | Meetily Pro installation |
| `.env` | Configuration file |
| `data/` | Persistent data (DB, cache) |
| `logs/` | Application logs |
| `storage/` | Uploaded files (Meetily) |

---

## Support

- **AI Identity Pro**: https://docs.aiidentity.pro
- **Meetily Pro**: https://docs.meetily.pro
