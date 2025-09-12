from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None

    def start_scheduler(self, app, cleanup_function):
        """Start the scheduler with midnight cleanup."""
        try:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.add_job(
                cleanup_function,
                trigger=CronTrigger(hour=0, minute=0, second=0),
                args=[app],
                id="midnight_task_cleanup",
                name="Delete all tasks daily at midnight",
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("✅ Task scheduler started successfully")
            logger.info("⏰ Scheduled task cleanup: Daily at 00:00 (midnight)")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def shutdown_scheduler(self):
        """Shutdown the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("🛑 Task scheduler shut down successfully")