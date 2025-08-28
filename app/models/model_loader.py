import torch
from diffusers import StableDiffusionPipeline
from app.config import DEVICE

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
    
class ModelLoader:
    def __init__(self):
        self.pipe = None
        self.is_loaded = False
    
    def load(self):
        """Load the model and store it as an instance attribute"""
        if not self.is_loaded:
            self.pipe = load_model()
            self.is_loaded = True
        return self.pipe
    
    def get_model(self):
        """Get the loaded model, load if not already loaded"""
        if not self.is_loaded:
            return self.load()
        return self.pipe

# Create a singleton instance
model_loader = ModelLoader()