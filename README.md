# EasyMeal Recipe App

A modern, full-stack recipe management application built with FastAPI and vanilla JavaScript. Features user authentication via Supabase, photo uploads with OCR text extraction, and a Progressive Web App (PWA) interface.

## Features

- 🔐 **User Authentication** - Secure registration/login with Supabase Auth and JWT tokens
- 📝 **Recipe Management** - Create, read, update, and delete recipes
- 📷 **Photo Upload** - Upload up to 2 photos per recipe with automatic text extraction (OCR)
- 🌍 **Multi-language** - English and French support
- 📱 **PWA Support** - Installable Progressive Web App with offline capabilities
- 🎨 **Modern UI** - Clean, responsive design with dark mode support
- 🔒 **Security** - CSRF protection, rate limiting, secure headers, and input validation
- 🗄️ **Database** - PostgreSQL with Alembic migrations
- ☁️ **Storage** - Supabase Storage for photo management

## Prerequisites

- Python 3.11+
- PostgreSQL database (or Supabase account)
- Supabase project (for authentication and storage)
- Node.js/npm (optional, for development)

## Project Structure

```
easymeal/
├── app/                    # FastAPI backend
│   ├── routes/            # API route handlers
│   ├── database.py        # Database models and connection
│   ├── auth.py            # Authentication logic
│   ├── storage.py         # Supabase Storage integration
│   └── ...
├── static/                # Frontend files
│   ├── index.html        # Main HTML
│   ├── app.js            # JavaScript application
│   ├── style.css         # Styles
│   └── i18n/             # Translation files
├── alembic/              # Database migrations
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Container definition
└── requirements.txt      # Python dependencies
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/easymeal.git
cd easymeal
```

### 2. Set Up Supabase

1. Create a [Supabase account](https://supabase.com) and create a new project
2. In your Supabase project:
   - Go to **Settings** → **API** to get:
     - `SUPABASE_URL`
     - `SUPABASE_ANON_KEY`
     - `SUPABASE_SERVICE_ROLE_KEY`
   - Go to **Settings** → **Database** to get your PostgreSQL connection string
   - Go to **Storage** and create a bucket named `photos` (or your preferred name)
   - Get your JWT secret from **Settings** → **API** → **JWT Settings**

### 3. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your values:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.supabase.co:5432/postgres
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
SUPABASE_BUCKET=photos
ENVIRONMENT=development
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** EasyOCR requires system dependencies. On Linux, install:
```bash
sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Run the Application

**Development:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production (with Docker):**
```bash
docker compose up -d --build
```

### 7. Access the Application

- Web interface: http://localhost:8000/easymeal/
- API docs: http://localhost:8000/easymeal/docs

## Before Sharing on GitHub

### ✅ Checklist

1. **Remove sensitive files:**
   - Ensure `.env` is in `.gitignore` (already included)
   - Never commit real API keys, secrets, or passwords

2. **Review `.gitignore`:**
   - Verify all sensitive files are excluded
   - Check that database files, logs, and user uploads are ignored

3. **Update configuration:**
   - Remove hardcoded URLs/domains (like `micmoe.ddns.net`) from code
   - Use environment variables for all configuration
   - Update CORS origins in `app/config.py` if needed

4. **Create `.env.example`:**
   - Template file is already created
   - Document all required environment variables

5. **Review code for:**
   - Any hardcoded credentials or secrets
   - Personal information or internal URLs
   - Debug/development code that shouldn't be public

6. **Update README:**
   - Add clear setup instructions
   - Document all prerequisites
   - Include environment variable documentation

7. **License:**
   - Ensure LICENSE file exists (currently MIT)
   - Update if needed

### 🔒 Security Reminders

- **Never commit:**
  - `.env` files with real values
  - API keys or secrets
  - Database passwords
  - JWT secrets
  - Service role keys

- **Always:**
  - Use `.env.example` as a template
  - Keep secrets in environment variables
  - Review `git status` before committing
  - Use `git diff` to check what you're about to commit

### 📝 Quick Pre-Push Commands

```bash
# Check what will be committed
git status

# Review changes
git diff

# Verify .env is not tracked
git ls-files | grep .env

# Check for common secrets (run before committing)
grep -r "SUPABASE_SERVICE_ROLE_KEY" --exclude-dir=.git --exclude="*.example" .
```

## API Endpoints

### Authentication
- `POST /api/register` - Register a new user
- `POST /api/login` - Login and get JWT token + CSRF token
- `GET /api/me` - Get current user info (protected)

### Meals (all protected, require authentication + CSRF token)
- `GET /api/meals` - Get all meals for current user
- `GET /api/meals/{meal_id}` - Get a specific meal
- `POST /api/meals` - Create a new meal
- `PUT /api/meals/{meal_id}` - Update a meal
- `DELETE /api/meals/{meal_id}` - Delete a meal
- `POST /api/meals/upload-photo` - Upload a photo
- `POST /api/meals/extract-text-from-photo` - Extract text from photo using OCR

## Deployment

### Docker Production

1. Set environment variables in `.env` file
2. Build and run:
```bash
docker compose up -d --build
```

3. Configure reverse proxy (Nginx) for SSL and domain routing

### Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - JWT secret for token validation

Optional:
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_BUCKET` - Storage bucket name (default: `photos`)
- `ENVIRONMENT` - `development` or `production` (default: `development`)
- `CORS_ORIGINS` - Additional CORS origins (comma-separated)

## Security Features

- ✅ **JWT Authentication** - Secure token-based auth via Supabase
- ✅ **CSRF Protection** - Token validation for state-changing operations
- ✅ **Rate Limiting** - Prevents abuse of authentication endpoints
- ✅ **Input Validation** - All user inputs validated and sanitized
- ✅ **Secure Headers** - Security headers for production
- ✅ **File Validation** - Image uploads validated for type and size
- ✅ **User Isolation** - Users can only access their own data
- ✅ **Password Security** - Managed by Supabase Auth

## Development

### Running Tests
```bash
# Add tests as needed
pytest
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details
