# EasyMeal Recipe App

A Python-based meal recipe application with FastAPI, featuring user authentication and a modern web interface.

## Features

- User authentication (register/login with JWT tokens)
- Meal list management (create, read, update, delete)
- Modern web interface
- RESTful API
- Dockerized for easy deployment

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

### Docker

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Access the application at http://localhost:8000

## Usage

1. Open http://localhost:8000 in your browser
2. Register a new account or login
3. Create, edit, and delete meals

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

