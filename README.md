# AI Image Generator - Backend

A FastAPI backend server for AI-powered image generation using Stable Diffusion. This service provides a RESTful API for creating images from text prompts with optional GPU acceleration.

![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Python](https://img.shields.io/badge/Python-3.9-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0-red)
![Stable Diffusion](https://img.shields.io/badge/Stable_Diffusion-2.1-orange)

## Architecture

Text Prompt → FastAPI → PyTorch → Stable Diffusion → Image Generation → Base64 Response


## Features

- **🤖 AI Image Generation**: Create images from text using Stable Diffusion 2.1
- **⚡ GPU Acceleration**: Optional CUDA support for faster generation
- **📊 Progress Tracking**: Real-time generation progress updates
- **🔒 CORS Enabled**: Cross-origin support for frontend integration
- **📚 Auto Documentation**: Interactive Swagger UI at `/docs`


## Tech Stack

- **Framework**: FastAPI with Uvicorn
- **AI Engine**: PyTorch + Hugging Face Diffusers
- **Model**: Stable Diffusion 2.1
- **Image Processing**: Pillow, Base64 encoding
- **Optional GPU**: CUDA 11.8, NVIDIA drivers

## Installation

### Pre-requisites
- Python 3.9+
- pip package manager
- (Optional) NVIDIA GPU with CUDA 11.8

### 1. Clone Repository
```bash
git clone https://github.com/microieva/image-generator.git
cd image-generator
```
### 2. Create Virtual Environment
```bash
python3.9 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Models
The first run will automatically download:

 - Stable Diffusion 2.1 model weights (~5GB)

 - Required tokenizers and configs

 ## Usage

### Start Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access endpoints:

 - API Docs: http://localhost:8000/docs
 - Health Check: http://localhost:8000/
 - Generate Endpoint: http://localhost:8000/generate

## Project structure

```bash
app/
├── main.py                 # FastAPI application and routes
├── models/               
├── static/                 
    ├── css/                
    └── js/                 
├── venv/                   # Generated environment
└── templates/              # HTML templates (if needed)
    └── index.html              

requirements.txt           # Python dependencies
startup.sh                 # Production startup script
```

## Acknowledgments
- [DataCrunch](www.datacrunch.io/) team for the access to GPU instance & infrastructure! _GPU Stable Diffusion speed with RTX 4090 ~1-3 seconds/image_

 - Stability AI for Stable Diffusion models

 - Hugging Face for Diffusers library

 - FastAPI team for the excellent web framework

 - PyTorch team for the deep learning framework