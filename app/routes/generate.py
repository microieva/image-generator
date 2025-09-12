from io import BytesIO
from fastapi.responses import JSONResponse
from datetime import datetime
import torch
import base64
from fastapi import APIRouter, BackgroundTasks, Request
from app.config import DEVICE
from app.models import load_model
from app.models import GenerateRequest
from app.core.task_manager import TaskManager, TaskStatus

router = APIRouter()
pipe = load_model()

def generate_image_task(app, task_id: str, generate_request: GenerateRequest, request: Request):
    """Background task for image generation"""
    task_manager: TaskManager = app.state.task_manager
    
    try:
        current_info = task_manager.get_task_info(task_id)
        if current_info and current_info.status != TaskStatus.PROCESSING:
            task_manager.update_task_status(task_id, TaskStatus.PROCESSING)
            print(f"🔄 Status corrected to PROCESSING for task {task_id}")
        
        generator = torch.Generator(DEVICE)
        if generate_request.seed:
            generator.manual_seed(generate_request.seed)

        def callback(step: int, timestep: int, latents: torch.FloatTensor):
            """Callback function to check for cancellation"""
            current_info = task_manager.get_task_info(task_id)
            if not current_info or current_info.status == TaskStatus.CANCELLED:
                print(f"⏹️ Cancellation detected in callback for task {task_id}")
                raise InterruptedError("Generation cancelled by user")
            
            progress = (step / generate_request.steps) * 100
            task_manager.update_task_progress(task_id, round(progress, 2))
            
            if step % 10 == 0:
                prompt = generate_request.prompt[:50] + "..." if len(generate_request.prompt) > 50 else generate_request.prompt
                print(f"📊 Task {task_id} progress: {progress:.1f}% - '{prompt}'")

        image = pipe(
            prompt=generate_request.prompt,
            num_inference_steps=generate_request.steps,
            guidance_scale=generate_request.guidance_scale,
            generator=generator,
            callback=callback,
            callback_steps=1
        ).images[0]

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        result = {
            "task_id": task_id,
            "image_url": f"data:image/png;base64,{img_str}",
            "prompt": generate_request.prompt,
        }
        task_manager.mark_task_completed(task_id, result)
        
        print(f"✅ Task {task_id} completed successfully")

    except InterruptedError:
        print(f"⏹️ Task {task_id} was cancelled during generation")
        task_manager.mark_task_cancelled(task_id)
    
    except Exception as e:
        print(f"❌ Error in task {task_id}: {e}")
        import traceback
        traceback.print_exc()
        task_manager.mark_task_error(task_id, str(e))
    
    finally:
        final_info = task_manager.get_task_info(task_id)
        if final_info:
            print(f"🏁 Task {task_id} final status: {final_info.status}")

@router.post("/generate")
async def generate_image(request: Request, generate_request: GenerateRequest, background_tasks: BackgroundTasks):
    """Endpoint to start image generation using TaskManager only"""
    try:
        task_manager: TaskManager = request.app.state.task_manager

        print("\n" + "="*50)
        print("📨 RECEIVED GENERATION REQUEST:")
        print(f"Prompt: '{generate_request.prompt}'")
        print("="*50 + "\n")

        task_id = task_manager.create_task(
            request=generate_request.dict(),
            prompt=generate_request.prompt
        )
        
        print(f"📝 Task created with ID: {task_id}")
        print(f"   Initial status: {task_manager.get_task_info(task_id).status}")
        
        background_tasks.add_task(generate_image_task, request.app, task_id, generate_request, request)
        task_manager.update_task_status(task_id, TaskStatus.PROCESSING)

        print(f"✅ Task {task_id} started via TaskManager")
        print(f"   Status: {task_manager.get_task_info(task_id).status}")
        print(f"   Total ongoing tasks: {task_manager.count}")
        
        return JSONResponse({
            "status": "started",
            "task_id": task_id,
            "message": "Generation started in background",
            "created_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ ERROR in generate endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )      
