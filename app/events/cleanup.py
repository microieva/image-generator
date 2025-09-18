from fastapi import FastAPI
from sqlalchemy import delete
from app.models import model_loader
from app.models.db_models import Image, Task
from app.utils.database import get_session

def delete_tasks_and_images_from_db():
    db_session = None
    try:
        db_session = get_session() 
        
        stmt_images = delete(Image)
        result_images = db_session.execute(stmt_images)
        db_session.commit()
        print(f"🗑️  Deleted {result_images.rowcount} rows from images table")
        
        stmt_tasks = delete(Task)
        result_tasks = db_session.execute(stmt_tasks)
        db_session.commit()
        print(f"🗑️  Deleted {result_tasks.rowcount} rows from tasks table")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        if db_session:
            db_session.rollback()
    finally:
        if db_session:
            db_session.close()

async def midnight_cleanup(app: FastAPI):
    """Scheduled function to delete all tasks every midnight"""

    task_manager = app.state.task_manager
    cancel_result = task_manager.cancel_all()
    print(f"📊 Cancellation result: {cancel_result}")
    delete_tasks_and_images_from_db()
    
    delete_result = task_manager.delete_all()
    print(f"📊 Deletion result: {delete_result}")
    model_loader.cleanup_models()
