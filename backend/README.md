# Exam Prep BD - Backend

FastAPI backend for the unified educational platform serving Bangladeshi government job aspirants.

## Features

- **Authentication**: JWT-based auth with refresh tokens, OTP verification
- **User Management**: Role-based access (Admin/Teacher/Student)
- **Exam System**: Full exam engine with proctoring support
- **Content Management**: Lessons, flashcards, topics, folders
- **News Aggregation**: Scraper for BD news sources
- **Job Circulars**: Job listings and alerts
- **Commerce**: Courses, books, orders with SSLCommerz integration
- **Blog**: Content management with comments

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (async with SQLAlchemy 2.0)
- **Cache**: Redis (Upstash free tier)
- **Auth**: JWT (python-jose)
- **Validation**: Pydantic v2
- **Logging**: Structlog

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Redis (optional for caching)

### Installation

```bash
# Clone repository
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
# Minimum required: DATABASE_URL, SECRET_KEY

# Run migrations (Alembic)
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies
├── config/
│   └── settings.py        # Configuration management
├── database/
│   ├── connection.py      # DB connection & session
│   └── dependencies.py    # FastAPI dependencies
├── models/
│   └── __init__.py        # SQLAlchemy ORM models
├── schemas/
│   └── __init__.py        # Pydantic schemas
├── routers/
│   ├── auth.py           # Authentication endpoints
│   ├── users.py          # User management
│   ├── questions.py      # Question bank
│   ├── exams.py          # Exam system
│   ├── lessons.py        # Lessons & flashcards
│   ├── news.py           # News aggregation
│   ├── jobs.py           # Job circulars
│   ├── courses.py        # Course management
│   └── payments.py       # Payment integration
└── utils/
    └── __init__.py       # Helper functions
```

## Database Schema

The merged schema includes:

| Domain | Tables |
|--------|--------|
| Users & Auth | `users`, `refresh_tokens`, `otp_codes` |
| Content | `topics`, `lessons`, `flashcards`, `folders`, `student_types` |
| Exams | `questions`, `mcq_options`, `exams`, `exam_attempts`, `student_answers` |
| News | `articles`, `sources`, `categories`, `tags`, `scrape_logs` |
| Jobs | `job_circulars` |
| Commerce | `courses`, `enrollments`, `books`, `orders` |
| Blog | `blog_posts`, `comments` |
| Analytics | `activity_logs`, `article_views` |

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - Login and get tokens
- `POST /refresh` - Refresh access token
- `GET /me` - Get current user
- `PUT /me` - Update profile
- `POST /logout` - Logout
- `POST /request-password-reset` - Request password reset
- `POST /reset-password` - Reset password with OTP
- `POST /send-otp` - Send OTP
- `POST /verify-otp` - Verify OTP

### More endpoints coming soon...

## Environment Variables

See `.env.example` for all available options.

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (min 32 chars)

**Optional:**
- `REDIS_URL` - Redis connection for caching
- `RESEND_API_KEY` - Email service
- `R2_*` - Cloudflare R2 storage
- `GROQ_API_KEY` - AI services

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Koyeb (Recommended Free Tier)

1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables
5. Deploy

### Render

Similar setup to Koyeb. Use the free tier for testing.

### Keep-Alive (Prevent Cold Starts)

Use cron-job.org to ping `/health` every 5 minutes:
```
https://your-app.koyeb.app/health
```

## License

MIT

## Contributing

Contributions welcome! Please read our contributing guidelines first.
