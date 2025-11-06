#!/bin/bash

# Deployment script for OVH VPS
# Usage: ./deploy.sh [user@host] [path]
# Examples:
#   ./deploy.sh
#   ./deploy.sh debian@vps-72277d08.vps.ovh.net
#   ./deploy.sh debian@vps-72277d08.vps.ovh.net /opt/easymeal/easymeal_reboot

set -e

# Parse arguments
if [ -z "$1" ]; then
    # No arguments - use defaults
    VPS_HOST="root@vps-72277d08.vps.ovh.net"
    APP_DIR="/opt/easymeal/easymeal_reboot"
elif [[ "$1" == *":"* ]]; then
    # Format: user@host:path
    VPS_HOST="${1%%:*}"
    APP_DIR="${1#*:}"
elif [[ "$1" == *"@"* ]]; then
    # Format: user@host (path as second arg or default)
    VPS_HOST="$1"
    APP_DIR="${2:-/opt/easymeal/easymeal_reboot}"
else
    # Just hostname
    VPS_HOST="$1"
    APP_DIR="${2:-/opt/easymeal/easymeal_reboot}"
fi

echo "🚀 Deploying EasyMeal to ${VPS_HOST}..."

# Check if .env exists locally
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating one..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -hex 32)
    echo "SECRET_KEY=${SECRET_KEY}" > .env
    echo "✅ Created .env file with random SECRET_KEY"
fi

echo "⚠️  IMPORTANT: This deployment will NOT copy the data directory to protect your production database."

# Create directory on VPS and check for rsync
echo "📁 Creating directory on VPS..."
ssh ${VPS_HOST} "mkdir -p ${APP_DIR}"

# Check if rsync is available on remote server
if ssh ${VPS_HOST} "command -v rsync > /dev/null 2>&1"; then
    echo "✅ rsync found on remote server"
    USE_RSYNC=true
else
    echo "⚠️  rsync not found on remote server, using tar method instead"
    USE_RSYNC=false
fi

# Copy files to VPS (excluding data, git, and sensitive files)
echo "📤 Copying files to VPS..."
if [ "$USE_RSYNC" = true ]; then
    rsync -avz --progress \
        --exclude 'data' \
        --exclude 'data/' \
        --exclude '*/data' \
        --exclude '.git' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.env' \
        --exclude '*.db' \
        --exclude '*.sqlite' \
        --exclude '*.sqlite3' \
        ./ ${VPS_HOST}:${APP_DIR}/
else
    # Use tar method as fallback
    echo "📦 Using tar method to transfer files..."
    tar --exclude='data' \
        --exclude='data/' \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='*.db' \
        --exclude='*.sqlite' \
        --exclude='*.sqlite3' \
        -czf - . | ssh ${VPS_HOST} "mkdir -p ${APP_DIR} && cd ${APP_DIR} && tar -xzf -"
fi

# Copy .env file separately
echo "🔐 Copying .env file..."
scp .env ${VPS_HOST}:${APP_DIR}/.env

# Build and start on VPS
echo "🔨 Building and starting application..."
ssh ${VPS_HOST} << EOF
cd ${APP_DIR}
docker compose -f docker-compose.prod.yml pull || true
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
EOF

echo "✅ Deployment complete!"
echo "🌐 Access your app at: https://easymeal.ddns.net"
echo "📝 App directory on VPS: ${APP_DIR}"

