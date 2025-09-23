import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.events.generate_stream import create_sse_event
from app.core.task_manager import TaskManager, TaskStatus

router = APIRouter()

@router.get("/generate-stream/{task_id}")
async def get_generation_stream(request: Request, task_id: str):
    """SSE stream for generation progress (GET)"""

    task_manager: TaskManager = request.app.state.task_manager
    task_info = task_manager.get_task_info(task_id)
    
    if not task_info:
        print(f"❌ Client tried to connect to non-existent task {task_id}")
        async def error_stream():
            yield create_sse_event({
                'error': 'Task not found',
                'status': 'error'
            })
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    prompt = task_info.prompt or 'N/A'
    print(f"🔗 Client connected to stream for task {task_id} | prompt: {prompt}")  
    
    stop_event = asyncio.Event()
    
    async def event_stream():
        try:
            while not stop_event.is_set() and not await request.is_disconnected():
                current_task_info = task_manager.get_task_info(task_id)
                
                if not current_task_info:
                    yield create_sse_event({
                        'error': 'Task was removed',
                        'status': 'error'
                    })
                    break
                
                sse_data = {
                    'task_id': task_id,
                    'status': current_task_info.status,
                    'progress': current_task_info.progress,
                    'message': f'Progress: {current_task_info.progress}%'
                }
                
                if (current_task_info.status == TaskStatus.COMPLETED and 
                    current_task_info.result):
                    sse_data['result'] = current_task_info.result
                
                if (current_task_info.status == TaskStatus.ERROR and 
                    current_task_info.error):
                    sse_data['error'] = current_task_info.error
                
                yield create_sse_event(sse_data)
                
                if current_task_info.status in [
                    TaskStatus.COMPLETED, 
                    TaskStatus.CANCELLED, 
                    TaskStatus.ERROR
                ]:
                    print(f"📤 Stream ending for task {task_id} with status: {current_task_info.status}")
                    break
                
                await asyncio.sleep(0.5) 
                
        except asyncio.CancelledError:
            print(f"📡 Stream connection cancelled for task {task_id}")
        except Exception as e:
            print(f"❌ Error in SSE stream for task {task_id}: {e}")
            yield create_sse_event({
                'error': f'Stream error: {str(e)}',
                'status': 'error'
            })
        finally:
            stop_event.set()
            print(f"🔌 Client disconnected from stream for task {task_id}")
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
