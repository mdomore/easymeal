#!/bin/bash

# Deployment script for OVH VPS
# Usage: ./deploy.sh user@vps-72277d08.vps.ovh.net

set -e

VPS_HOST="${1:-root@vps-72277d08.vps.ovh.net}"
APP_DIR="/opt/easymeal"

echo "🚀 Deploying EasyMeal to ${VPS_HOST}..."

# Check if .env exists locally
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating one..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -hex 32)
    echo "SECRET_KEY=${SECRET_KEY}" > .env
    echo "✅ Created .env file with random SECRET_KEY"
fi

# Create directory on VPS
echo "📁 Creating directory on VPS..."
ssh ${VPS_HOST} "mkdir -p ${APP_DIR}"

# Copy files to VPS (excluding data and git)
echo "📤 Copying files to VPS..."
rsync -avz --progress \
    --exclude 'data' \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    ./ ${VPS_HOST}:${APP_DIR}/

# Copy .env file separately
echo "🔐 Copying .env file..."
scp .env ${VPS_HOST}:${APP_DIR}/.env

# Build and start on VPS
echo "🔨 Building and starting application..."
ssh ${VPS_HOST} << 'EOF'
cd /opt/easymeal
docker compose -f docker-compose.prod.yml pull || true
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
EOF

echo "✅ Deployment complete!"
echo "🌐 Access your app at: http://vps-72277d08.vps.ovh.net:8000"

