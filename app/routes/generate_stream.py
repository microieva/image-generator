from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime
import uuid
from app.models.image_models import GenerateRequest
from app.routes.generate import generate_image_task


router = APIRouter()

def create_sse_event(data: dict) -> str:
    """Create a properly formatted SSE event"""
    json_data = json.dumps(data)
    return f"data: {json_data}\n\n"

@router.post("/generate-stream")
async def generate_image_stream(request: Request, generate_request: GenerateRequest):
    """Stream generation progress via SSE"""
    task_id = str(uuid.uuid4())
    ongoing_tasks = request.app.state.ongoing_tasks
    
    ongoing_tasks[task_id] = {
        'status': 'pending',
        'progress': 0.0,
        'created_at': datetime.now().isoformat(),
        'request': generate_request.dict(),
        'cancelled': False
    }

    async def event_stream():
        """SSE stream generator"""
        try:
            # Send initial response
            yield create_sse_event({
                'task_id': task_id,
                'status': 'pending',
                'progress': 0,
                'message': 'Generation started'
            })

            # Start generation in background
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, generate_image_task, request.app, task_id, generate_request)
            
            # Stream progress updates
            while True:
                if task_id not in ongoing_tasks:
                    break
                    
                task_data = ongoing_tasks[task_id]
                
                # Send progress update
                yield create_sse_event({
                    'task_id': task_id,
                    'status': task_data['status'],
                    'progress': task_data.get('progress', 0),
                    'message': f'Progress: {task_data.get("progress", 0)}%'
                })

                # Break if generation is complete
                if task_data['status'] in ['completed', 'cancelled', 'error']:
                    # Send final result if completed
                    if task_data['status'] == 'completed' and 'result' in task_data:
                        yield create_sse_event({
                            'task_id': task_id,
                            'status': 'completed',
                            'progress': 100,
                            'result': task_data['result'],
                            'message': 'Generation complete'
                        })
                    break
                    
                await asyncio.sleep(0.5)  # Send updates every 500ms
                
        except Exception as e:
            yield create_sse_event({
                'task_id': task_id,
                'status': 'error',
                'progress': 0,
                'error': str(e),
                'message': f'Error: {str(e)}'
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',  # For frontend development
        }
    )