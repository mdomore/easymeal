# CORS Configuration Guide

## What is CORS?

CORS (Cross-Origin Resource Sharing) controls which domains can access your API. By default, browsers block requests from different origins for security.

## When Do You Need CORS_ORIGINS?

### ✅ You DON'T need to set CORS_ORIGINS if:

1. **Same-origin deployment**: Your frontend and backend are on the same domain
   - Example: Frontend at `https://example.com` and API at `https://example.com/api`
   - The browser considers this the same origin

2. **Local development**: Using default localhost origins
   - Defaults include: `http://localhost:8000` and `http://localhost:3000`
   - These work out of the box

3. **Reverse proxy setup**: Using nginx/traefik to serve everything on one domain
   - Example: Frontend and API both served through `https://example.com`
   - No CORS needed since it's the same origin

### ⚠️ You DO need to set CORS_ORIGINS if:

1. **Different domains**: Frontend and API on different domains
   - Example: Frontend at `https://myapp.com` and API at `https://api.myapp.com`
   - Set: `CORS_ORIGINS=https://myapp.com`

2. **Multiple frontend domains**: Serving frontend from multiple domains
   - Example: `https://myapp.com` and `https://www.myapp.com`
   - Set: `CORS_ORIGINS=https://myapp.com,https://www.myapp.com`

3. **Development with different ports**: Using non-standard ports
   - Example: Frontend on `http://localhost:5173` (Vite default)
   - Set: `CORS_ORIGINS=http://localhost:5173`

## How to Configure

### Option 1: Environment Variable (Recommended)

Add to your `.env` file:

```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Option 2: Docker Compose

Add to `docker-compose.yml`:

```yaml
environment:
  - CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Option 3: System Environment Variable

```bash
export CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Current Configuration

The app includes these defaults (no configuration needed):

- `http://localhost:8000` - Default FastAPI port
- `http://localhost:3000` - Common frontend dev port

Additional origins from `CORS_ORIGINS` are added to this list.

## Troubleshooting

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Cause:** Your frontend domain is not in the allowed origins list.

**Solution:** Add your domain to `CORS_ORIGINS`:

```bash
CORS_ORIGINS=https://yourdomain.com
```

### Error: "Credentials flag is true, but 'Access-Control-Allow-Credentials' header is ''"

**Cause:** CORS is configured but credentials aren't being sent properly.

**Solution:** The app already sets `allow_credentials=True`. Make sure:
1. Your frontend sends credentials: `fetch(url, { credentials: 'include' })`
2. Your domain is in `CORS_ORIGINS`

### Still having issues?

1. Check browser console for the exact error
2. Verify your domain matches exactly (including `http://` vs `https://`)
3. Check that `CORS_ORIGINS` is set correctly (no extra spaces, correct format)
4. Restart the application after changing environment variables

## Security Note

⚠️ **Never use wildcards** like `*` in production. Always specify exact domains:

```bash
# ❌ BAD - Allows any domain
CORS_ORIGINS=*

# ✅ GOOD - Specific domains only
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```
