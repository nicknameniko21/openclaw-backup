#!/bin/bash
# Quick deploy script for AI Identity Pro

set -e

cd /root/.openclaw/workspace/ai-identity-pro

# Create a simple docker-compose for production
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET=prod-secret-change-me
      - DATABASE_URL=sqlite:///./data/app.db
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/public:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
    depends_on:
      - backend
EOF

# Create backend Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create requirements.txt
cat > backend/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
PyJWT==2.8.0
python-multipart==0.0.6
EOF

# Create nginx config
cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Create data directory
mkdir -p data

echo "✅ AI Identity Pro deployment files created"
