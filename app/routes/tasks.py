from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.core.task_manager import TaskManager

router = APIRouter()

@router.get("/tasks")
async def get_tasks(request: Request):
    """List all ongoing and recent tasks"""
    task_manager: TaskManager = request.app.state.task_manager
    all_tasks = task_manager.list_all_tasks()
    
    print(f"\n📋 Total Tasks: {len(all_tasks)}")
    
    for task_id, task_data in all_tasks.items():
        status = task_data['status']
        progress = task_data.get('progress', 0)
        prompt_preview = task_data.get('prompt', 'N/A')[:50] + "..." if task_data.get('prompt') and len(task_data.get('prompt', '')) > 50 else task_data.get('prompt', 'N/A')
        print(f"  - {task_id}: {status} ({progress}%) - '{prompt_preview}'")
    
    return JSONResponse({
        "total_tasks": len(all_tasks),
        "tasks": {
            task_id: {
                "status": data['status'],
                "progress": data.get('progress', 0),
                "created_at": data['created_at'],
                "prompt": data.get('prompt', 'N/A')[:50] + "..." if data.get('prompt') and len(data.get('prompt', '')) > 50 else data.get('prompt', 'N/A')
            }
            for task_id, data in all_tasks.items()
        }
    })
