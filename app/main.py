import os
import torch
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from diffusers import StableDiffusionPipeline
from typing import Optional

import uuid
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import base64
from io import BytesIO

from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import Generator

class GenerateRequest(BaseModel):
    prompt: str
    steps: int = 20
    guidance_scale: float = 7.5
    seed: Optional[int] = None

# --- Environment Setup ---
def get_device():
    """Auto-select the best available device"""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return "mps"  # Apple Silicon
    return "cpu"  # Fallback to CPU

DEVICE = get_device()
print(f"\n🚀 Using device: {DEVICE.upper()}")

# --- App Configuration ---
app = FastAPI()
# app.mount("/static", StaticFiles(directory="app/static"), name="static")
# templates = Jinja2Templates(directory="app/templates")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model Loading ---
def load_model():
    try:
        torch_dtype = torch.float16 if DEVICE in ["cuda", "mps"] else torch.float32

        pipe = StableDiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-2-1",
            torch_dtype=torch_dtype,
            safety_checker=None,
            use_xformers=False,
            variant="fp16" if torch_dtype == torch.float16 else None
        )

        # Optimizations
        if DEVICE == "cuda":
            torch.backends.cuda.enable_flash_sdp(True)
            torch.backends.cuda.enable_mem_efficient_sdp(True)
        elif DEVICE == "cpu":
            pipe.enable_attention_slicing()

        return pipe.to(DEVICE)

    except Exception as e:
        print(f"❌ Model loading failed: {str(e)}")
        raise

pipe = load_model()

# --- Routes ---
# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     """Render the input form"""
#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "device": DEVICE
#     })

@app.get("/")
async def root():
    """API status endpoint"""
    return {"status": "ready", "device": DEVICE}

# @app.post("/generate")
# async def generate_image(
#     prompt: str,
#     steps: int = 20,
#     guidance_scale: float = 7.5,
#     seed: Optional[int] = None
# ):
#     """Generate image from text prompt"""
#     try:
#         # Generator for reproducibility
#         generator = torch.Generator(DEVICE)
#         if seed:
#             generator.manual_seed(seed)

#         # Generate image
#         image = pipe(
#             prompt=prompt,
#             num_inference_steps=steps,
#             guidance_scale=guidance_scale,
#             generator=generator
#         ).images[0]

#         # Save output
#         output_path = "generated_image.png"
#         image.save(output_path)

#         return FileResponse(
#             output_path,
#             media_type="image/png",
#             filename=os.path.basename(output_path)
#         )

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/generate")
# async def generate_image(request: GenerateRequest):
#     try:
#         generator = torch.Generator(DEVICE)
#         if request.seed:
#             generator.manual_seed(request.seed)

#         image = pipe(
#             prompt=request.prompt,
#             num_inference_steps=request.steps,
#             guidance_scale=request.guidance_scale,
#             generator=generator
#         ).images[0]

#         Convert to base64
#         buffered = BytesIO()
#         image.save(buffered, format="PNG")
#         img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

#         return JSONResponse({
#             "status": "success",
#             "image": f"data:image/png;base64,{img_str}",
#             "prompt": request.prompt
#         })

#     except Exception as e:
#         return JSONResponse(
#             status_code=500,
#             content={"status": "error", "message": str(e)}
#         )
# Add static file serving
@app.post("/generate")
async def generate_image(request: GenerateRequest):
    try:
        # ===== DEBUG: Print received request =====
        print("\n" + "="*50)
        print("📨 RECEIVED REQUEST:")
        print(f"Prompt: '{request.prompt}'")
        print(f"Steps: {request.steps}")
        print(f"Guidance Scale: {request.guidance_scale}")
        print(f"Seed: {request.seed}")
        print("="*50 + "\n")
        # ===== END DEBUG =====

        generator = torch.Generator(DEVICE)
        if request.seed:
            generator.manual_seed(request.seed)

        image = pipe(
            prompt=request.prompt,
            num_inference_steps=request.steps,
            guidance_scale=request.guidance_scale,
            generator=generator
        ).images[0]

        # Convert to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return JSONResponse({
            "status": "success",
            "image": f"data:image/png;base64,{img_str}",
            "prompt": request.prompt
        })

    except Exception as e:
        # Log errors too
        print(f"❌ ERROR: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# @app.post("/generate-stream")
# async def generate_image_stream(request: GenerateRequest):
#     print("\n" + "="*50)
#     print("📨 RECEIVED REQUEST:")
#     print(f"Prompt: '{request.prompt}'")
#     print(f"Steps: {request.steps}")
#     print(f"Guidance Scale: {request.guidance_scale}")
#     print(f"Seed: {request.seed}")
#     print("="*50 + "\n")
#     async def event_generator() -> Generator[str, None, None]:
#         """Yield progress updates"""
#         try:
#             # Initialize pipeline
#             generator = torch.Generator(DEVICE)
#             if request.seed:
#                 generator.manual_seed(request.seed)

#             # Send initial progress
#             yield json.dumps({"status": "started", "progress": 0})

#             # Generate with progress updates
#             result = pipe(
#                 prompt=request.prompt,
#                 num_inference_steps=request.steps,
#                 guidance_scale=request.guidance_scale,
#                 generator=generator,
#                 callback=lambda step, timestep, latents:
#                     asyncio.create_task(update_progress(step, request.steps))
#             )

#             image = result.images[0]

#             # Convert to base64
#             buffered = BytesIO()
#             image.save(buffered, format="PNG")
#             img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

#             # Send final result
#             yield json.dumps({
#                 "status": "completed",
#                 "progress": 100,
#                 "image": f"data:image/png;base64,{img_str}",
#                 "prompt": request.prompt
#             })

#         except Exception as e:
#             yield json.dumps({"status": "error", "message": str(e)})

#     async def update_progress(step: int, total_steps: int):
#         """Send progress update"""
#         progress = int((step / total_steps) * 100)
#         yield json.dumps({"status": "generating", "progress": progress})

#     return EventSourceResponse(event_generator())

# @app.get("/generate-stream") 
# async def generate_stream():
#     async def event_generator():
#         # Your image generation logic here
#         for progress in range(0, 101, 10):
#             # Simulate progress updates
#             yield {
#                 "event": "progress",
#                 "data": str(progress)
#             }
#             await asyncio.sleep(1)
    
#     return EventSourceResponse(event_generator())

# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    print("✅ Model loaded successfully")
    print(f"💡 Tips: {'GPU' if DEVICE == 'cuda' else 'CPU'} optimized settings applied")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)