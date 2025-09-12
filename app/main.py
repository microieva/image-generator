import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils import lifespan

from .config import DEVICE, EXECUTOR
from .routes import generate_image, cancel_generation, get_generation_stream, get_tasks, get_generation_status, delete_tasks

print(f"\n🚀 Using device: {DEVICE.upper()}")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "https://react-image-generator-five.vercel.app/", 
        "http://172.20.10.5:3000/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.executor = EXECUTOR

app.include_router(generate_image)
app.include_router(get_generation_stream)
app.include_router(get_generation_status)
app.include_router(cancel_generation)
app.include_router(delete_tasks)
app.include_router(get_tasks)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
