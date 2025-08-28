from fastapi import APIRouter
from app.config import DEVICE  

router = APIRouter()

@router.get("/")
async def status():
    """API status endpoint"""
    return {"status": "ready", "device": DEVICE}