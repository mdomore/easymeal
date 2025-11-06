# Deployment Guide for OVH VPS

## Prerequisites

1. SSH access to your VPS: `vps-72277d08.vps.ovh.net`
2. Docker and Docker Compose installed on the VPS
3. Domain name (optional, for HTTPS)

## Step 1: Install Docker on VPS (if not already installed)

SSH into your VPS:
```bash
ssh root@vps-72277d08.vps.ovh.net
```

Install Docker and Docker Compose:
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

## Step 2: Transfer Project Files to VPS

### Option A: Using SCP (from your local machine)
```bash
# From your local machine
scp -r /Users/michaelmoreliere/Dev/easymeal_reboot root@vps-72277d08.vps.ovh.net:/opt/easymeal
```

### Option B: Using Git (recommended)
On the VPS:
```bash
# Install git if needed
apt install git -y

# Clone your repository (if you have one)
cd /opt
git clone <your-repo-url> easymeal
cd easymeal
```

### Option C: Using rsync
```bash
rsync -avz --exclude 'data' --exclude '.git' /Users/michaelmoreliere/Dev/easymeal_reboot/ root@vps-72277d08.vps.ovh.net:/opt/easymeal/
```

## Step 3: Configure Production Settings

Create a `.env` file on the VPS:
```bash
cd /opt/easymeal
nano .env
```

Add:
```
SECRET_KEY=your-very-secure-random-secret-key-here-change-this
DB_PATH=/app/data/meals.db
```

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Update docker-compose.yml for Production

Create `docker-compose.prod.yml`:
```yaml
services:
  api:
    build: .
    ports:
      - "127.0.0.1:8000:8000"  # Only listen on localhost
    volumes:
      - ./data:/app/data
    environment:
      - DB_PATH=/app/data/meals.db
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

## Step 5: Build and Run

```bash
cd /opt/easymeal
docker compose -f docker-compose.prod.yml up -d --build
```

Check status:
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

## Step 6: Set Up Nginx Reverse Proxy

Install Nginx:
```bash
apt install nginx -y
```

Copy Nginx configuration:
```bash
# From your project directory
cp nginx.conf /etc/nginx/sites-available/easymeal
```

Or create it manually:
```bash
nano /etc/nginx/sites-available/easymeal
```

Paste the configuration from `nginx.conf` in the project.

Enable site:
```bash
ln -s /etc/nginx/sites-available/easymeal /etc/nginx/sites-enabled/
# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default
nginx -t
```

## Step 7: Set Up HTTPS with Let's Encrypt

Install Certbot:
```bash
apt install certbot python3-certbot-nginx -y
```

**Important:** Make sure your domain `easymeal.ddns.net` points to your VPS IP before proceeding.

Get SSL certificate:
```bash
certbot --nginx -d easymeal.ddns.net
```

Follow the prompts:
- Enter your email address
- Agree to terms
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

Certbot will automatically update the Nginx configuration with SSL certificates.

Reload Nginx:
```bash
systemctl reload nginx
```

## Step 8: Update Docker Compose for Localhost Binding

Since we're using Nginx as reverse proxy, update `docker-compose.prod.yml` to bind only to localhost:

```yaml
ports:
  - "127.0.0.1:8000:8000"
```

This is more secure as the app is only accessible through Nginx.

## Access Your App

- With HTTPS: `https://easymeal.ddns.net`
- Direct (not recommended): `http://vps-72277d08.vps.ovh.net:8000`

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart service
docker compose -f docker-compose.prod.yml restart

# Stop service
docker compose -f docker-compose.prod.yml down

# Update application
cd /opt/easymeal
git pull  # if using git
docker compose -f docker-compose.prod.yml up -d --build
```

