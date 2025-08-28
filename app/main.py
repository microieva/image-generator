import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor

from .config import DEVICE, EXECUTOR
from .routes import status
from .routes import generate_image 
from .routes import cancel_generation
from .routes import get_generation_status
from .routes import list_tasks
from .events import startup

print(f"\n🚀 Using device: {DEVICE.upper()}")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "https://react-image-generator-five.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.ongoing_tasks = {}
app.state.executor = EXECUTOR

# --- Routes ---
app.include_router(status)
app.include_router(generate_image)
app.include_router(get_generation_status)
app.include_router(list_tasks)
app.include_router(cancel_generation)

# --- Events ---
app.add_event_handler("startup", startup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)