from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core import model_loader, shutdown_manager
from app.core.scheduler import TaskScheduler
from app.core.task_manager import TaskManager
from app.events.cleanup import db_weekly_cleanup, midnight_cleanup
from app.utils.database import initialize_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application starting up...")
    
    app.state.task_manager = TaskManager()
    app.state.scheduler = TaskScheduler()    
    await initialize_database()
    
    app.state.scheduler.start_midnight_scheduler(app, midnight_cleanup)
    app.state.scheduler.start_weekly_scheduler(app, db_weekly_cleanup)
    
    if hasattr(model_loader, 'cleanup'):
        shutdown_manager.add_cleanup_handler(model_loader.cleanup)
        print("✅ Model cleanup handler registered")
    
    yield 
    
    print("🛑 Application shutting down...")
    
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown_scheduler()
    
    if hasattr(app.state, 'task_manager'):
        app.state.task_manager.cancel_all()
        app.state.task_manager.delete_all()
    
    await shutdown_manager.run_cleanup()
