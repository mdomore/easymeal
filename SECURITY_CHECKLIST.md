# Security Checklist for GitHub Sharing

Use this checklist before pushing your code to GitHub to ensure no sensitive information is exposed.

## ✅ Pre-Push Security Checks

### 1. Environment Files
- [ ] `.env` file is NOT tracked (check with `git ls-files | grep .env`)
- [ ] `.env.example` exists with placeholder values only
- [ ] No real API keys, passwords, or secrets in `.env.example`

### 2. Configuration Files
- [ ] `nginx.conf` is in `.gitignore` (contains personal domain/server info)
- [ ] `nginx.conf.example` exists with placeholder values
- [ ] No hardcoded domains in code (use environment variables)
- [ ] CORS origins use environment variables, not hardcoded domains

### 3. Secrets & API Keys
- [ ] No Supabase service role keys in code
- [ ] No JWT secrets in code
- [ ] No database passwords in code
- [ ] No API keys or tokens in code
- [ ] Run: `grep -r "eyJ[A-Za-z0-9_-]+\.eyJ" --exclude-dir=.git .` (should return nothing)

### 4. Personal Information
- [ ] No personal domains hardcoded (e.g., `micmoe.ddns.net`)
- [ ] No personal email addresses
- [ ] No server IPs or internal paths
- [ ] No SSL certificate paths with real domains

### 5. Database & Storage
- [ ] No database connection strings with real credentials
- [ ] No storage bucket names with personal identifiers
- [ ] No backup files committed

### 6. Code Review
- [ ] Check for commented-out code with secrets
- [ ] Review all `.py`, `.js`, `.yml`, `.yaml`, `.json` files
- [ ] Check `docker-compose.yml` for hardcoded values
- [ ] Verify all secrets use environment variables

## 🔍 Quick Security Scan Commands

```bash
# Check if .env is tracked
git ls-files | grep .env

# Search for JWT tokens (should return nothing)
grep -r "eyJ[A-Za-z0-9_-]+\.eyJ" --exclude-dir=.git --exclude="*.example" .

# Search for common secret patterns
grep -ri "password.*=" --exclude-dir=.git --exclude="*.example" .
grep -ri "api.*key" --exclude-dir=.git --exclude="*.example" .
grep -ri "secret" --exclude-dir=.git --exclude="*.example" . | grep -v "get_required_env\|get_optional_env\|description"

# Check for hardcoded domains (update with your domain)
grep -ri "micmoe\.ddns\.net" --exclude-dir=.git --exclude="*.md" .

# List all files that will be committed
git status
git diff --cached --name-only
```

## 📝 Files to Review

### Must Check:
- [ ] `app/config.py` - CORS origins, no hardcoded domains
- [ ] `docker-compose.yml` - Environment variable references only
- [ ] `static/app.js` - No hardcoded API endpoints with personal domains
- [ ] `nginx.conf` - Should be in `.gitignore`
- [ ] `.env` - Should be in `.gitignore`

### Should Create:
- [ ] `.env.example` - Template with placeholders
- [ ] `nginx.conf.example` - Template with placeholders
- [ ] `SECURITY_CHECKLIST.md` - This file

## 🚨 If You Find Secrets

If you accidentally committed secrets:

1. **Immediately rotate/revoke the exposed secrets**
2. **Remove from git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/file" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push (if already on GitHub, rotate secrets first!):**
   ```bash
   git push origin --force --all
   ```

## ✅ Final Verification

Before pushing:
```bash
# See what will be committed
git status
git diff --cached

# Verify .gitignore is working
git check-ignore -v .env nginx.conf

# Should show:
# .env:30:.gitignore
# nginx.conf:73:.gitignore
```

## 📚 Additional Resources

- [GitHub's guide on removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Git secrets scanning](https://github.com/awslabs/git-secrets)
