import logging
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models.image_models import CancelRequest
from app.models.model_loader import load_model
from datetime import datetime


router = APIRouter()
pipe = load_model()
ongoing_tasks = {}

@router.post("/cancel-generation")
async def cancel_generation(request: Request, cancel_request: CancelRequest, background_tasks: BackgroundTasks):
    """Endpoint to cancel an ongoing generation"""
    
    # ===== DEBUG: Print cancellation request =====
    print("\n" + "="*50)
    print("⏹️ RECEIVED CANCELLATION REQUEST:")
    print(f"Task ID: {cancel_request.task_id}")
    print("="*50 + "\n")
    # ===== END DEBUG =====
    
    ongoing_tasks = request.app.state.ongoing_tasks
    task_id = cancel_request.task_id
    
    if task_id not in ongoing_tasks:
        print(f"❌ Task {task_id} not found in ongoing_tasks")
        print(f"\nRemaining Tasks: {len(ongoing_tasks)} \n{ongoing_tasks.items()}, \nOngoing: {[tid for tid, tinfo in ongoing_tasks.items() if tinfo.get('status') == 'processing']}")
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    
    # Check if task is already completed or cancelled
    current_status = ongoing_tasks[task_id]['status']
    print(f"📋 Task {task_id} current status: {current_status}")
    
    if current_status in ['completed', 'cancelled', 'error']:
        prompt = ongoing_tasks[task_id]['request']['prompt']
        print(f"ℹ️ Task {task_id} [prompt: {prompt}] is already {current_status}")
        raise HTTPException(status_code=400, detail=f"Task is already {current_status}")
    
    # Mark task as cancelled
    ongoing_tasks[task_id]['cancelled'] = True
    ongoing_tasks[task_id]['status'] = 'cancelling'
    ongoing_tasks[task_id]['cancelled_at'] = datetime.now().isoformat()
    
    logging.info(f"Cancellation requested for task {task_id}")
    print(f"✅ Cancellation marked for task {task_id}")
    print(f"\nRemaining Tasks: {len(ongoing_tasks)} \n{ongoing_tasks.items()},\nOngoing: {[tid for tid, tinfo in ongoing_tasks.items() if tinfo['status'] == 'processing']}")
    print(f"\nBackground tasks: {background_tasks.tasks}\n")
    
    return JSONResponse({
        "status": "success",
        "message": "Cancellation requested",
        "task_id": task_id
    })