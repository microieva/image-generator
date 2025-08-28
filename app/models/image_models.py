from pydantic import BaseModel
from typing import Optional

class CancelRequest(BaseModel):
    task_id: str

from pydantic import BaseModel
from typing import Optional, Dict, Any
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