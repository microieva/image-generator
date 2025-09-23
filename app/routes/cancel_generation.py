import logging
from app.core.task_manager import TaskManager, TaskStatus
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.models.image_models import CancelRequest, CancellationResponse

router = APIRouter()

@router.post("/cancel-generation", response_model=CancellationResponse)
async def cancel_generation(request: Request, cancel_request: CancelRequest):
    """Endpoint to cancel an ongoing generation with detailed response"""

    task_manager: TaskManager = request.app.state.task_manager
    task_id = cancel_request.task_id

    print(f"\n⏹️ Cancellation request for task: {task_id}")

    task_info = task_manager.get_task_info(task_id)
    
    if not task_info:
        raise HTTPException(
            status_code=404, 
            detail={
                "message": "Task not found",
                "task_id": task_id,
                "suggestion": "Check /tasks endpoint for available tasks"
            }
        )

    if task_info.status == TaskStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Task already cancelled",
                "task_id": task_id,
                "current_status": TaskStatus.CANCELLED
            }
        )
    
    if task_info.status == TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Task already completed",
                "task_id": task_id,
                "current_status": TaskStatus.COMPLETED,
                "result_available": task_info.result is not None
            }
        )
    
    if task_info.status == TaskStatus.ERROR:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Task already failed",
                "task_id": task_id,
                "current_status": TaskStatus.ERROR,
                "error": task_info.error
            }
        )

    cancellation_successful = task_manager.cancel_task(task_id)
    
    if cancellation_successful:
        logging.info(f"Successfully cancelled task {task_id} - Prompt: {task_info.prompt}")
        message = "Task cancelled successfully"
    else:
        logging.warning(f"Task {task_id} could not be cancelled (may have completed during request)")
        message = "Task cancellation attempted, but it may have already completed"

    return JSONResponse({
        "status": "success",
        "message": message,
        "task_id": task_id
    })
