import asyncio
from io import BytesIO
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
import torch
import base64
import uuid
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from app.config import DEVICE
from app.events.generate_stream import create_sse_event
from app.models import load_model
from app.models import GenerateRequest
from app.models.image_models import GenerationStatus

router = APIRouter()
pipe = load_model()
ongoing_tasks = {}

def generate_image_task(app, task_id: str, generate_request: GenerateRequest, request: Request):
    """Background task for image generation with cancellation support"""
    ongoing_tasks = request.app.state.ongoing_tasks
    
    try:
        # Update task status to processing
        ongoing_tasks[task_id]['status'] = 'processing'
        ongoing_tasks[task_id]['started_at'] = datetime.now().isoformat()
        
        # Check if cancelled before starting
        if ongoing_tasks[task_id].get('cancelled', False):
            ongoing_tasks[task_id]['status'] = 'cancelled'
            ongoing_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            prompt
            print(f"❌ Task {task_id} [prompt: {prompt}] was cancelled before starting")
            return
        
        generator = torch.Generator(DEVICE)
        if generate_request.seed:
            generator.manual_seed(generate_request.seed)

        def callback(step: int, timestep: int, latents: torch.FloatTensor):
            """Callback function to check for cancellation at each step"""
            if task_id not in ongoing_tasks:
                return  # Task no longer exists, exit quietly ?
            
            # Check if cancelled 
            if ongoing_tasks[task_id].get('cancelled', False):
                print(f"⏹️ Cancellation detected in callback for task {task_id}")
                raise InterruptedError("Generation cancelled by user")
            
            # Update progress
            progress = (step / generate_request.steps) * 100
            ongoing_tasks[task_id]['progress'] = round(progress, 2)
            # print progress
            if step % 10 == 0:  # Print every 10 steps
                prompt = ongoing_tasks[task_id]['request']['prompt'][:50] + "..." if len(ongoing_tasks[task_id]['request']['prompt']) > 50 else ongoing_tasks[task_id]['request']['prompt']
                print(f"📊 Task {task_id} progress: {progress:.1f}% - '{prompt}'")

        # Generate image 
        image = pipe(
            prompt=generate_request.prompt,
            num_inference_steps=generate_request.steps,
            guidance_scale=generate_request.guidance_scale,
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
                "task_id": task_id,
                "image_url": f"data:image/png;base64,{img_str}",
                "prompt": generate_request.prompt,
            }
            prompt = ongoing_tasks[task_id]['request']['prompt']
            print(f"✅ Task {task_id} [prompt: {prompt}] completed successfully")
            # adding deletion from ongoing_tasks
            del ongoing_tasks[task_id]
            print(f"\nRemaining Tasks: {len(ongoing_tasks)} \n{ongoing_tasks.items()}, \nOngoing: {[tid for tid, tinfo in ongoing_tasks.items() if tinfo.get('status') == 'processing']}")

    except InterruptedError:
        prompt = ongoing_tasks[task_id]['request']['prompt']
        print(f"⏹️ Task {task_id} [prompt: {prompt}] was cancelled during generation")
        if task_id in ongoing_tasks:
            ongoing_tasks[task_id]['status'] = 'cancelled'
            ongoing_tasks[task_id]['completed_at'] = datetime.now().isoformat()
    
    except Exception as e:
        prompt = ongoing_tasks[task_id]['request']['prompt']
        print(f"❌ Error in task {task_id} [prompt: {prompt}] : {e}")
        if task_id in ongoing_tasks:
            ongoing_tasks[task_id]['status'] = 'error'
            ongoing_tasks[task_id]['error'] = str(e)
            ongoing_tasks[task_id]['completed_at'] = datetime.now().isoformat()
    
    finally:
        print(f"\nRemaining Tasks: {len(ongoing_tasks)}, Ongoing: {[tid for tid, tinfo in ongoing_tasks.items() if tinfo['status'] == 'processing']}")

        if task_id in ongoing_tasks:
            print(f"Removing task {task_id} with status: {ongoing_tasks[task_id].get('status')}")
            del ongoing_tasks[task_id]
            print(f"\nRemaining Tasks: {len(ongoing_tasks)} \n{ongoing_tasks.items()}, \nOngoing: {[tid for tid, tinfo in ongoing_tasks.items() if tinfo.get('status') == 'processing']}")
        pass

@router.post("/generate")
async def generate_image(request: Request, generate_request: GenerateRequest, background_tasks: BackgroundTasks):
    """Endpoint to start image generation with cancellation support"""
    try:
        ongoing_tasks = request.app.state.ongoing_tasks
        # ===== DEBUG: Print received request =====
        print("\n" + "="*50)
        print("📨 RECEIVED GENERATION REQUEST:")
        print(f"Prompt: '{generate_request.prompt}'")
        print(f"Steps: {generate_request.steps}")
        print(f"Guidance Scale: {generate_request.guidance_scale}")
        print(f"Seed: {generate_request.seed}")
        print("="*50 + "\n")
        print(f"\nCurrent Tasks: {len(ongoing_tasks)} \n{ongoing_tasks.items()}, \nOngoing: {[tid for tid, tinfo in ongoing_tasks.items() if tinfo.get('status') == 'processing']}")
        # ===== END DEBUG =====
        task_id = str(uuid.uuid4())
        ongoing_tasks[task_id] = {
            'status': 'pending',
            'progress': 0.0,
            'created_at': datetime.now().isoformat(),
            'request': generate_request.dict(),
            'cancelled': False,
            'prompt': generate_request.prompt
        }
        
        background_tasks.add_task(generate_image_task, request.app, task_id, generate_request, request)
        
        logging.info(f"Started generation task {task_id} for prompt: {generate_request.prompt}")
        print(f"📋 Task {task_id} added to background tasks")
        
        return JSONResponse({
            "status": "started",
            "task_id": task_id,
            "message": "Generation started in background",
            "created_at": ongoing_tasks[task_id]['created_at']
        })
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        # Additional cleanup if needed
    
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
    
    return JSONResponse({
        "task_id": task_id,
        "status": task_data['status'],
        "progress": task_data.get('progress'),
        "created_at": task_data['created_at'],
        "started_at": task_data.get('started_at'),
        "completed_at": task_data.get('completed_at'),
        "cancelled": task_data.get('cancelled', False),
        "result": 'result' in task_data,
        "prompt": task_data['prompt']
    })

@router.get("/tasks")
async def list_tasks(request: Request, background_tasks: BackgroundTasks):
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

@router.get("/generate-stream/{task_id}")
async def get_generation_stream(request: Request, background_tasks: BackgroundTasks):
    """SSE stream for generation progress (GET)"""
    stop_event = asyncio.Event()
    ongoing_tasks = request.app.state.ongoing_tasks
    task_id = request.path_params['task_id']  
    prompt = ongoing_tasks.get(task_id, {}).get('request', {}).get('prompt', 'N/A')
    print(f"🔗 Client connected to stream for task {task_id} | prompt {prompt}")  
    async def event_stream():
        try:
            while not stop_event.is_set() and not await request.is_disconnected():
                if task_id not in ongoing_tasks:
                    yield create_sse_event({
                        'error': 'Task not found',
                        'status': 'error'
                    })
                    break
                
                task_data = ongoing_tasks[task_id]
                yield create_sse_event({
                    'task_id': task_id,
                    'status': task_data['status'],
                    'progress': task_data.get('progress', 0),
                    'message': f'Progress: {task_data.get("progress", 0)}%'
                })

                if task_data['status'] in ['completed', 'cancelled', 'error']:
                    if task_data['status'] == 'completed' and 'result' in task_data:
                        yield create_sse_event({
                            'task_id': task_id,
                            'status': 'completed',
                            'progress': 100,
                            'result': task_data['result']
                        })
                    break
                
                await asyncio.sleep(0.5)
                
        except Exception as e:
            yield create_sse_event({
                'error': str(e),
                'status': 'error'
            })
        finally:
            stop_event.set()

    background_tasks.add_task(event_stream)

    async def cleanup_on_disconnect():
        await stop_event.wait()
    
    background_tasks.add_task(cleanup_on_disconnect)

    return StreamingResponse(event_stream(), media_type="text/event-stream")