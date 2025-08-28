from io import BytesIO
from fastapi.responses import JSONResponse
from datetime import datetime
import torch
import base64
import uuid
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from app.config import DEVICE
from app.models import load_model
from app.models import GenerateRequest
from app.models.image_models import GenerationStatus

router = APIRouter()
pipe = load_model()
ongoing_tasks = {}

def generate_image_task(app, task_id: str, request: GenerateRequest):
    """Background task for image generation with cancellation support"""
    ongoing_tasks = app.state.ongoing_tasks
    
    try:
        # Update task status to processing
        ongoing_tasks[task_id]['status'] = 'processing'
        ongoing_tasks[task_id]['started_at'] = datetime.now().isoformat()
        
        # Check if cancelled before starting
        if ongoing_tasks[task_id].get('cancelled', False):
            ongoing_tasks[task_id]['status'] = 'cancelled'
            ongoing_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            print(f"❌ Task {task_id} was cancelled before starting")
            return
        
        generator = torch.Generator(DEVICE)
        if request.seed:
            generator.manual_seed(request.seed)

        def callback(step: int, timestep: int, latents: torch.FloatTensor):
            """Callback function to check for cancellation at each step"""
            if (task_id in ongoing_tasks and 
                ongoing_tasks[task_id].get('cancelled', False)):
                # Raise exception to stop generation
                raise InterruptedError("Generation cancelled by user")
            
            if task_id in ongoing_tasks:
                progress = (step / request.steps) * 100
                ongoing_tasks[task_id]['progress'] = round(progress, 2)
                print(f"📊 Task {task_id} progress: {progress:.1f}%")

        # Generate image with callback for cancellation checks
        image = pipe(
            prompt=request.prompt,
            num_inference_steps=request.steps,
            guidance_scale=request.guidance_scale,
            generator=generator,
            callback=callback,  # Add callback for cancellation
            callback_steps=1    # Check every step
        ).images[0]

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Update task with result (only if not cancelled)
        if not ongoing_tasks[task_id].get('cancelled', False):
            ongoing_tasks[task_id]['status'] = 'completed'
            ongoing_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            ongoing_tasks[task_id]['result'] = {
                "image_url": f"data:image/png;base64,{img_str}",
                "prompt": request.prompt,
            }
            print(f"✅ Task {task_id} completed successfully")

    except InterruptedError:
        print(f"⏹️ Task {task_id} was cancelled during generation")
        if task_id in ongoing_tasks:
            ongoing_tasks[task_id]['status'] = 'cancelled'
            ongoing_tasks[task_id]['completed_at'] = datetime.now().isoformat()
    
    except Exception as e:
        # Handle other errors
        print(f"❌ Error in task {task_id}: {e}")
        if task_id in ongoing_tasks:
            ongoing_tasks[task_id]['status'] = 'error'
            ongoing_tasks[task_id]['error'] = str(e)
            ongoing_tasks[task_id]['completed_at'] = datetime.now().isoformat()
    
    finally:
        # todo: remove task after some time
        pass

@router.post("/generate")
async def generate_image(request: Request, generate_request: GenerateRequest, background_tasks: BackgroundTasks):
    """Endpoint to start image generation with cancellation support"""
    try:
        # ===== DEBUG: Print received request =====
        print("\n" + "="*50)
        print("📨 RECEIVED GENERATION REQUEST:")
        print(f"Prompt: '{generate_request.prompt}'")
        print(f"Steps: {generate_request.steps}")
        print(f"Guidance Scale: {generate_request.guidance_scale}")
        print(f"Seed: {generate_request.seed}")
        print("="*50 + "\n")
        # ===== END DEBUG =====

        task_id = str(uuid.uuid4())
        ongoing_tasks = request.app.state.ongoing_tasks
        ongoing_tasks[task_id] = {
            'status': 'pending',
            'progress': 0.0,
            'created_at': datetime.now().isoformat(),
            'request': generate_request.dict(),
            'cancelled': False
        }
        
        background_tasks.add_task(generate_image_task, request.app, task_id, generate_request)
        
        logging.info(f"Started generation task {task_id} for prompt: {generate_request.prompt}")
        print(f"📋 Task {task_id} added to background tasks")
        
        # Return immediately with task ID - don't wait for generation to complete
        return JSONResponse({
            "status": "started",
            "task_id": task_id,
            "message": "Generation started in background",
            "created_at": ongoing_tasks[task_id]['created_at']
        })
    
    except Exception as e:
        print(f"❌ ERROR in generate endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@router.get("/status/{task_id}")
async def get_generation_status(request: Request, task_id: str):
    """Check the status of a generation task"""
    ongoing_tasks = request.app.state.ongoing_tasks
    
    print(f"🔍 Status check for task {task_id}")
    print(f"📊 Available tasks: {list(ongoing_tasks.keys())}")
    
    if task_id not in ongoing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = ongoing_tasks[task_id]
    
    return {
        "task_id": task_id,
        "status": task_data['status'],
        "progress": task_data.get('progress'),
        "created_at": task_data['created_at'],
        "started_at": task_data.get('started_at'),
        "completed_at": task_data.get('completed_at'),
        "cancelled": task_data.get('cancelled', False),
        "has_result": 'result' in task_data
    }

@router.get("/tasks")
async def list_tasks(request: Request):
    """List all ongoing and recent tasks"""

    ongoing_tasks = request.app.state.ongoing_tasks
    return {
        "total_tasks": len(ongoing_tasks),
        "tasks": {
            task_id: {
                "status": data['status'],
                "progress": data.get('progress'),
                "created_at": data['created_at'],
                "prompt": data['request']['prompt'][:50] + "..." if len(data['request']['prompt']) > 50 else data['request']['prompt']
            }
            for task_id, data in ongoing_tasks.items()
        }
    }