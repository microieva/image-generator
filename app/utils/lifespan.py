from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.scheduler import TaskScheduler
from app.core.task_manager import TaskManager
from app.events.cleanup import midnight_cleanup
from app.utils.database import initialize_database

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.task_manager = TaskManager()
  app.state.scheduler = TaskScheduler()    
  app.state.scheduler.start_scheduler(app, midnight_cleanup)    
  await initialize_database()
  yield    
  app.state.scheduler.shutdown_scheduler()
  app.state.task_manager.cancel_all()
  app.state.task_manager.delete_all()