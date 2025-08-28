import torch
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from diffusers import StableDiffusionPipeline
from typing import Optional

from pydantic import BaseModel
from fastapi.responses import JSONResponse
import base64
from io import BytesIO


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "https://react-image-generator-five.vercel.app/"],
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
@app.get("/")
async def root():
    """API status endpoint"""
    return {"status": "ready", "device": DEVICE}

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

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    print("✅ Model loaded successfully")
    print(f"💡 Tips: {'GPU' if DEVICE == 'cuda' else 'CPU'} optimized settings applied")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)