from app.models.image_models import GenerationResult
from app.utils.database import get_db
from app.models.db_models import Image, Task
from sqlalchemy.orm import Session

def save_task_to_db(task_info, db: Session):
    try:
        task = Task(
            task_id=task_info.task_id,
            status=task_info.status,
            progress=task_info.progress
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        print(f"✅ Task {task_info.task_id} saved to db")
        return task
    except Exception as e:
        db.rollback()
        print(f"Error saving task: {e}")

def save_image_to_db(result: GenerationResult, db: Session):
    try:
        image = Image(
            task_id=result["task_id"],   
            image_data=result["image_url"], 
            prompt=result["prompt"]        
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        print(f"✅ Image saved for task {result['task_id']}")
        return image
    except Exception as e:
        db.rollback()
        print(f"Error saving image: {e}")

def delete_image_from_db(task_id: str):
    db_gen = get_db()
    try:
        db = next(db_gen) 
        image = db.query(Image).filter(Image.task_id == task_id).first()
        
        if image:
            db.delete(image)
            print(f"✅ Image with task_id {task_id} deleted successfully")
            return True
        else:
            print(f"⚠️  No image found with task_id {task_id}")
            return False
                
    except Exception as e:
        print(f"❌ Error deleting image with task_id {task_id}: {e}")
        return False
