# EasyMeal Recipe App

A Python-based meal recipe application with FastAPI, featuring user authentication and a modern web interface.

## Features

- User authentication (register/login with JWT tokens)
- Meal list management (create, read, update, delete)
- Modern web interface
- RESTful API
- Dockerized for easy deployment
- Nginx reverse proxy configuration
- Multi-domain support via path-based routing

## Project Structure

- `app/` - FastAPI application code
- `static/` - Frontend files (HTML, CSS, JS)
- `data/` - Database and user uploads (not in git)
- `docker-compose.prod.yml` - Production Docker configuration
- `nginx.conf` - Nginx reverse proxy configuration
- `HTTPS_SETUP.md` - SSL certificate setup guide

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app.main:app --reload
```

3. Access the application:
- Web interface: http://localhost:8000
- API docs: http://localhost:8000/docs

### Docker Production

1. Set environment variables:
```bash
export SECRET_KEY="your-secret-key-here"
```

2. Build and run:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

3. Set up Nginx and SSL (see `HTTPS_SETUP.md`)

## Deployment

The application is configured to run at `micmoe.ddns.net/easymeal/` with:
- Main landing page at `micmoe.ddns.net`
- EasyMeal app at `micmoe.ddns.net/easymeal/`

See `DEPLOYMENT.md` and `HTTPS_SETUP.md` for detailed deployment instructions.

## API Endpoints

### Authentication
- `POST /api/register` - Register a new user
- `POST /api/login` - Login and get JWT token
- `GET /api/me` - Get current user info (protected)

### Meals (all protected, require authentication)
- `GET /api/meals` - Get all meals for current user
- `GET /api/meals/{meal_id}` - Get a specific meal
- `POST /api/meals` - Create a new meal
- `PUT /api/meals/{meal_id}` - Update a meal
- `DELETE /api/meals/{meal_id}` - Delete a meal

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Users can only access their own meals
- Docker container binds to localhost only (accessed via Nginx)

## License

MIT
