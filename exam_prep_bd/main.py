from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from database.session import init_db
from scraper.scheduler import init_scheduler
from routers import auth, users, questions

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Exam Prep BD API...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Initialize scheduler
    scheduler = init_scheduler()
    
    # Schedule news scraping job
    from scraper.news_scraper import run_scrape_job
    scheduler.add_cron_job(
        run_scrape_job,
        minute="0",
        hour=f"*/{settings.SCRAPE_INTERVAL_HOURS}",
        job_id="news_scrape"
    )
    logger.info(f"Scheduled news scraping every {settings.SCRAPE_INTERVAL_HOURS} hours")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Unified educational platform for Bangladeshi government job aspirants",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(questions.router, prefix=settings.API_PREFIX)

# TODO: Add more routers as they are created
# app.include_router(exams.router, prefix=settings.API_PREFIX)
# app.include_router(lessons.router, prefix=settings.API_PREFIX)
# app.include_router(news.router, prefix=settings.API_PREFIX)
# app.include_router(jobs.router, prefix=settings.API_PREFIX)
# app.include_router(courses.router, prefix=settings.API_PREFIX)
# app.include_router(books.router, prefix=settings.API_PREFIX)
# app.include_router(blog.router, prefix=settings.API_PREFIX)
# app.include_router(payment.router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
