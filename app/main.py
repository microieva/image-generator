import os
import torch
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from diffusers import StableDiffusionPipeline
from typing import Optional

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
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

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
            pipe.enable_xformers_memory_efficient_attention()
        elif DEVICE == "cpu":
            pipe.enable_attention_slicing()
            
        return pipe.to(DEVICE)
    
    except Exception as e:
        print(f"❌ Model loading failed: {str(e)}")
        raise

pipe = load_model()

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the input form"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "device": DEVICE
    })

@app.post("/generate")
async def generate_image(
    prompt: str,
    steps: int = 20,
    guidance_scale: float = 7.5,
    seed: Optional[int] = None
):
    """Generate image from text prompt"""
    try:
        # Generator for reproducibility
        generator = torch.Generator(DEVICE)
        if seed:
            generator.manual_seed(seed)
            
        # Generate image
        image = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator
        ).images[0]
        
        # Save output
        output_path = "generated_image.png"
        image.save(output_path)
        
        return FileResponse(
            output_path,
            media_type="image/png",
            filename=os.path.basename(output_path)
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    print("✅ Model loaded successfully")
    print(f"💡 Tips: {'GPU' if DEVICE == 'cuda' else 'CPU'} optimized settings applied")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)