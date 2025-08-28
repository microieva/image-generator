import torch
from concurrent.futures import ThreadPoolExecutor

def get_device():
    """Auto-select the best available device"""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return "mps"  # Apple Silicon
    return "cpu"  # Fallback to CPU

MODEL_NAME = "stabilityai/stable-diffusion-2-1"
DEVICE = get_device()

IMAGE_SIZE = 512  # Default image size
MAX_CONCURRENT_JOBS = 4  # Maximum simultaneous generations
DEFAULT_STEPS = 50  # Default inference steps
DEFAULT_GUIDANCE = 7.5  

MODEL_CONFIG = {
    "torch_dtype": torch.float16 if DEVICE in ["cuda", "mps"] else torch.float32,
    "safety_checker": None,
    "use_xformers": False,
    "variant": "fp16" if DEVICE in ["cuda", "mps"] else None
}

# logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

EXECUTOR = ThreadPoolExecutor(max_workers=4) 