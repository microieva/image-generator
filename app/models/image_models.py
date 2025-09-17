from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 512
    num_inference_steps: int = 50
    guidance_scale: float = 7.5
    steps: int = 20
    seed: Optional[int] = None

class ImagesParams(BaseModel):
    page: int = 1
    limit: int = 12 
    task_id: Optional[str] = None

class CancelRequest(BaseModel):
    task_id: str

class GenerationStatus(BaseModel):
    task_id: str
    status: str  # 'pending', 'processing', 'completed', 'cancelled', 'error'
    progress: Optional[float] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class GenerationResult(BaseModel):
    task_id: str
    image_url: str        
    prompt: str

class ImageResponse(BaseModel):
    id: int
    task_id: str
    image_url: str
    prompt: str
    created_at: datetime

    class Config:
        from_attributes = True

class ImagesSliceResponse(BaseModel):
    length: int
    slice: Optional[list[ImageResponse]] = None