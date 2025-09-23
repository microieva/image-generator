
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.task_manager import TaskManager, TaskStatus
from app.models.image_models import TaskStatusResponse

router = APIRouter()

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_generation_status(request: Request, task_id: str):
    """Check the status of a generation task"""
    task_manager: TaskManager = request.app.state.task_manager
    
    print(f"🔍 Status check for task {task_id}")
    all_tasks = task_manager.list_all_tasks()
    print(f"📊 Available tasks: {list(all_tasks.keys())}")

    task_info = task_manager.get_task_info(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = {
        'status': task_info.status,
        'progress': task_info.progress,
        'created_at': task_info.created_at,
        'started_at': task_info.started_at,
        'completed_at': task_info.completed_at,
        'cancelled': task_info.status == TaskStatus.CANCELLED,
        'prompt': task_info.prompt,
        'result': task_info.result is not None
    }
    
    return JSONResponse({
        "task_id": task_id,
        "status": task_data['status'],
        "progress": task_data.get('progress'),
        "created_at": task_data['created_at'],
        "started_at": task_data.get('started_at'),
        "completed_at": task_data.get('completed_at'),
        "cancelled": task_data.get('cancelled', False),
        "result": task_data.get('result', False),
        "prompt": task_data['prompt']
    })