# Exam Prep BD - Backend API

Unified educational platform for Bangladeshi government job aspirants.

## Features

- **Authentication**: JWT-based auth with refresh tokens, OTP verification
- **User Management**: Role-based access (Admin/Teacher/Student)
- **Exam System**: MCQ exams with anti-cheat proctoring, leaderboards
- **Content Management**: Lessons, flashcards, topics, folders
- **News Aggregation**: Automated scraping from Bangladeshi news sources
- **Job Circulars**: Job alerts and listings
- **E-commerce**: Courses, books, SSLCommerz payment integration
- **Blog**: Educational content with comments

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Background Jobs**: APScheduler
- **Storage**: Cloudflare R2
- **Cache**: Redis (Upstash)

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis (optional)

### Installation

```bash
# Clone repository
cd exam_prep_bd

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and set your DATABASE_URL

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/exam_prep_bd

# Security
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Storage (Cloudflare R2)
R2_BUCKET_NAME=your-bucket
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key

# Payment (SSLCommerz)
SSL_STORE_ID=your-store-id
SSL_STORE_PASSWORD=your-store-password

# Email (Resend)
RESEND_API_KEY=your-api-key

# AI (Groq)
GROQ_API_KEY=your-groq-key

# Redis
REDIS_URL=redis://localhost:6379
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
exam_prep_bd/
├── main.py                 # FastAPI app entry point
├── config/
│   └── settings.py         # Application settings
├── database/
│   └── session.py          # Database connection
├── models/
│   └── __init__.py         # SQLAlchemy models
├── schemas/
│   └── __init__.py         # Pydantic schemas
├── routers/
│   ├── auth.py             # Authentication endpoints
│   ├── users.py            # User management
│   ├── exams.py            # Exam system
│   ├── questions.py        # Question bank
│   ├── lessons.py          # Study materials
│   ├── news.py             # News aggregation
│   └── ...
├── utils/
│   ├── auth.py             # Auth utilities
│   └── deps.py             # Dependencies
├── scraper/
│   ├── scheduler.py        # Job scheduler
│   └── news_scraper.py     # News scraping logic
└── requirements.txt
```

## Development

### Running Tests

```bash
pytest
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

## License

MIT
