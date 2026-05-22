from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background job scheduler using APScheduler."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}
    
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def shutdown(self, wait=True):
        """Shutdown the scheduler."""
        self.scheduler.shutdown(wait=wait)
        logger.info("Scheduler shutdown")
    
    def add_interval_job(
        self,
        func: Callable,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        job_id: Optional[str] = None,
        **kwargs
    ):
        """Add a job that runs at regular intervals."""
        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            days=days
        )
        
        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            **kwargs
        )
        
        if job_id:
            self.jobs[job_id] = job
        
        logger.info(f"Added interval job: {job_id or job.id}")
        return job
    
    def add_cron_job(
        self,
        func: Callable,
        minute: str = "*",
        hour: str = "*",
        day_of_week: str = "*",
        day_of_month: str = "*",
        month: str = "*",
        job_id: Optional[str] = None,
        **kwargs
    ):
        """Add a cron-style scheduled job."""
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month=month
        )
        
        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            **kwargs
        )
        
        if job_id:
            self.jobs[job_id] = job
        
        logger.info(f"Added cron job: {job_id or job.id} ({minute} {hour} {day_of_week} {day_of_month} {month})")
        return job
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
    
    def get_job(self, job_id: str):
        """Get a scheduled job by ID."""
        return self.scheduler.get_job(job_id)
    
    def pause_job(self, job_id: str):
        """Pause a scheduled job."""
        self.scheduler.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")
    
    def resume_job(self, job_id: str):
        """Resume a paused job."""
        self.scheduler.resume_job(job_id)
        logger.info(f"Resumed job: {job_id}")


# Global scheduler instance
scheduler = SchedulerService()


def init_scheduler():
    """Initialize and start the global scheduler."""
    scheduler.start()
    return scheduler
