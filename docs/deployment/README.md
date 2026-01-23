# Deployment Documentation

This directory contains optional deployment configurations and examples.

## Nginx Reverse Proxy (Optional)

If you're deploying behind an nginx reverse proxy, you can use the example configuration provided.

**Note:** Nginx is NOT required to run EasyMeal. The application can run standalone or behind any reverse proxy.

### When to Use Nginx

- You want to serve multiple applications on the same domain (path-based routing)
- You need SSL/TLS termination
- You want to serve static files efficiently
- You need advanced load balancing or rate limiting

### Setup

1. Copy the example configuration:
   ```bash
   cp docs/deployment/nginx.conf.example /etc/nginx/sites-available/easymeal
   ```

2. Edit the configuration:
   - Replace `YOUR_DOMAIN_HERE` with your actual domain
   - Update SSL certificate paths
   - Adjust proxy_pass port if needed (default: 8000)
   - Customize paths and locations as needed

3. Enable the site:
   ```bash
   ln -s /etc/nginx/sites-available/easymeal /etc/nginx/sites-enabled/
   nginx -t  # Test configuration
   systemctl reload nginx
   ```

4. Set up SSL with Let's Encrypt:
   ```bash
   certbot --nginx -d yourdomain.com
   ```

### Alternative: Run Without Nginx

You can run EasyMeal directly:

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (with gunicorn)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

For production, you may want to:
- Use a process manager (systemd, supervisor, etc.)
- Set up SSL with a reverse proxy or use uvicorn with SSL certificates
- Configure firewall rules

## Docker Deployment

See the main README.md for Docker deployment instructions.

## Environment Variables

All configuration is done via environment variables. See `.env.example` in the project root.
