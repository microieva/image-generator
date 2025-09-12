
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from app.core.task_manager import TaskManager

router = APIRouter()

@router.delete("/delete-tasks")
async def delete_tasks(request: Request, background_tasks: BackgroundTasks):
    """Endpoint to delete all tasks that are not processing"""
    
    task_manager: TaskManager = request.app.state.task_manager
    ongoing_tasks = task_manager.list_all_tasks()

    try:
        if not ongoing_tasks or len(ongoing_tasks) == 0:
            return JSONResponse({
                "message": "No tasks found"
            })
        
        total_tasks = len(ongoing_tasks)
        task_manager.delete_all()
        
        return JSONResponse({
            "message": f"Successfully deleted {total_tasks} tasks"
        })
        
    except Exception as e:
        print(f"❌ ERROR deleting tasks: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to delete tasks: {str(e)}"}
        )
