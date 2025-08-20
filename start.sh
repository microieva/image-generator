#!/bin/bash

# Initialize
echo "🚀 Starting AI Image Generator Setup (Python 3.9)"

# Verify Python version
python3.9 --version || { echo "❌ Python 3.9 not found"; exit 1; }

# Create and activate venv using explicit Python 3.9
python3.9 -m venv venv
source venv/bin/activate

# Install exact pip version known to work with Python 3.9
python -m pip install pip==21.3.1

# Install dependencies (using PyTorch CUDA 11.8 for best compatibility)
pip install -r requirements.txt

# Download model weights (optional)
echo "⏳ Downloading model weights..."
python3 -c "
from diffusers import StableDiffusionPipeline
StableDiffusionPipeline.from_pretrained(
    'stabilityai/stable-diffusion-2-1',
    cache_dir='./models',
    torch_dtype=torch.float16
)
"

# Launch server with production settings
echo "✅ Starting production server..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --timeout-keep-alive 300 