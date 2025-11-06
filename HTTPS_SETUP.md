# HTTPS Setup for micmoe.ddns.net

## Quick Setup Steps

### 1. Ensure Domain Points to VPS

Make sure `micmoe.ddns.net` DNS points to your VPS IP address:
```bash
# Check current DNS
dig micmoe.ddns.net

# Should return your VPS IP
```

### 2. Install Nginx and Certbot

```bash
apt update
apt install nginx certbot python3-certbot-nginx -y
```

### 3. Copy Nginx Configuration

```bash
cd /opt/easymeal/easymeal_reboot
cp nginx.conf /etc/nginx/sites-available/micmoe
ln -s /etc/nginx/sites-available/micmoe /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
```

### 4. Get SSL Certificate

```bash
certbot --nginx -d micmoe.ddns.net
```

Follow prompts:
- Email: enter your email
- Terms: agree
- Redirect: Yes (redirect HTTP to HTTPS)

### 5. Update Docker Compose (if not already done)

Make sure `docker-compose.prod.yml` binds to localhost:
```yaml
ports:
  - "127.0.0.1:8000:8000"
```

Then restart:
```bash
cd /opt/easymeal/easymeal_reboot
docker compose -f docker-compose.prod.yml up -d
```

### 6. Test Nginx Configuration

```bash
nginx -t
systemctl reload nginx
```

### 7. Access Your Sites

- Main page: `https://micmoe.ddns.net`
- EasyMeal app: `https://micmoe.ddns.net/easymeal/`

## Verify SSL Certificate

Check certificate status:
```bash
certbot certificates
```

## Auto-Renewal

Certbot automatically sets up renewal. Test it:
```bash
certbot renew --dry-run
```

Certificates auto-renew via cron job at `/etc/cron.d/certbot`.

## Troubleshooting

### Certificate not issued
- Ensure DNS points to your VPS IP
- Check firewall allows ports 80 and 443
- Verify Nginx can bind to port 80

### 502 Bad Gateway
- Check Docker container is running: `docker ps`
- Check container logs: `docker compose logs api`
- Verify Nginx can reach localhost:8000

### Mixed Content Warnings
- Ensure app uses HTTPS URLs
- Check browser console for HTTP resources

