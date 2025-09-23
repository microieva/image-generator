# AI Image Generator - Backend

A FastAPI backend server for AI-powered image generation using Stable Diffusion. This service provides a RESTful API for creating images from text prompts with optional GPU acceleration.

![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Python](https://img.shields.io/badge/Python-3.9-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0-red)
![Stable Diffusion](https://img.shields.io/badge/Stable_Diffusion-2.1-orange)

## Deployment

Currently this server runs on a [DataCrunch](www.datacrunch.io/) cloud instance with the following production-grade specifications:

**Compute Resources:**
- **GPU**: 1x NVIDIA RTX A6000 with 48GB VRAM (CUDA 12.6)
- **CPU**: 10 vCPUs with 60GB system RAM
- **Storage**: 50GB high-performance storage

**Software Stack:**
- **OS**: Ubuntu 24.04 LTS with Docker containerization
- **Environment**: Fully containerized deployment using Docker Compose
- **Runtime**: Optimized for GPU-accelerated inference with CUDA support

**Cost Optimization:**
- On-demand pricing at **€0.43/hour** (€0.418/h instance + €0.012/h storage)
- Scalable infrastructure capable of handling multiple concurrent generation requests
- Efficient resource utilization for Stable Diffusion model inference

This enterprise-grade configuration ensures high-performance image generation with reliable uptime and scalable resource allocation.

[Image Generator Live](https://react-image-generator-kappa.vercel.app/)

## Architecture

Text Prompt → FastAPI → PyTorch → Stable Diffusion → Image Generation → Base64 Response


## Features

### 🤖 **AI Image Generation & Management**
- **Multiple Model Support**: Flexible architecture for Stable Diffusion 2.1 and future model integrations via `core/model_loader.py`
- **Intelligent Task Orchestration**: Async task management with priority queuing and cancellation support (`core/task_manager.py`, `routes/cancel_generation.py`)
- **Batch Operations**: Bulk task management and deletion capabilities (`routes/delete_tasks.py`, `routes/tasks.py`)

### ⚡ **Performance & Scalability**
- **GPU Acceleration**: Optional CUDA support with intelligent memory management via `core/model_loader.py`
- **Background Processing**: Non-blocking image generation with dedicated scheduler (`core/scheduler.py`)
- **Streaming Progress**: Real-time generation updates through Server-Sent Events (`events/generate_stream.py`)
- **Optimized Resource Handling**: Graceful shutdown with cleanup procedures (`core/shutdown_manager.py`, `events/cleanup.py`)

### 📊 **Real-time Monitoring & Control**
- **Live Progress Tracking**: Real-time event-stream progress streaming for long-running generations
- **Task Status API**: Comprehensive task monitoring with state management (`routes/task_status.py`)
- **Scheduler**: Midnight cleanup of the application state, model and tables (`routes/scheduler.py`)
- **Image Management**: Efficient retrieval and asset handling (`routes/images.py`)

### 🏗️ **Production-Ready Architecture**
- **Database Integration**: Async SQLAlchemy models with connection pooling (`models/db_models.py`, `utils/database.py`)
- **Configuration Management**: Environment-based settings with validation (`config.py`)
- **Lifecycle Management**: Robust startup/shutdown procedures (`events/startup.py`, `utils/lifespan.py`)
- **Image Processing Pipeline**: Optimized transformation and format handling (`utils/image_processing.py`)

### 🔒 **API & Security**
- **CORS Enabled**: Comprehensive cross-origin support for frontend integration
- **Request Validation**: Strongly-typed Pydantic schemas (`models/image_models.py`)
- **Auto Documentation**: Interactive Swagger UI at `/docs` with full endpoint documentation
- **Error Handling**: Error responses across all routes

### 📦 **Deployment & Operations**
- **Containerized Deployment**: Docker and Docker Compose support for easy scaling
- **Health Monitoring**: Database and service health checks (`events/db_events.py`)
- **Resource Cleanup**: Automated cleanup of temporary files and GPU memory
- **Development Tools**: Separate dependency management for dev/production environments

### 🔄 **Workflow Features**
- **Cancellation Support**: Atomic task cancellation with proper resource cleanup
- **Streaming Responses**: Efficient handling of large image payloads
- **Bulk Operations**: Mass task deletion 


## Tech Stack

- **Framework**: FastAPI with Uvicorn
- **AI Engine**: PyTorch + Hugging Face Diffusers
- **Model**: Stable Diffusion 2.1
- **Image Processing**: Pillow, Base64 encoding
- **Optional GPU**: CUDA 11.8 (in production)

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
pip install -r local.txt
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
 - Stream Progress Endpoint: http://localhost:8000/generate-stream/:task_id
 - Generation Tasks Endpoint: http://localhost:8000/tasks
 - Task Status Endpoint: http://localhost:8000/status/:task_id
 - Collection of Generated Images Endpoint: http://localhost:8000/images
 - Cancellation Endpoint: http://localhost:8000/cancel-generation
 - Delete Tasks Endpoint: http://localhost:8000/delete-tasks


## Project structure

```bash

app/
├── main.py                 # FastAPI application entry point with router configuration
├── config.py               # Centralized configuration management 
├── core/                   # Business logic layer - domain-specific services
    ├── model_loader.py     # AI model lifecycle management (loading, caching, GPU optimization)
    ├── scheduler.py        # Background task scheduling (start and shutdown)
    ├── shutdown_manager.py # Graceful shutdown coordination for resource cleanup
    └── task_manager.py     # Async task orchestration and state management
├── events/                 # Application lifecycle event handlers
    ├── cleanup.py          # Resource deallocation (midnight cleanup)
    ├── db_events.py        # Database events for tasks & images tables
    ├── generate_stream.py  # Real-time image generation progress streaming
    └── startup.py          # Database dependency initialization
├── models/                 # Data models and schemas
    ├── db_models.py        # SQLAlchemy ORM models for persistence layer
    └── image_models.py     # Pydantic schemas for API request/response validation
├── routes/                 # HTTP endpoint handlers (REST API layer)
    ├── cancel_generation.py # Task cancellation with atomic state transitions
    ├── delete_tasks.py     # Bulk task management and cleanup operations
    ├── generate_stream.py  # Generation handling       
    ├── generate.py         # Core image generation endpoint with payload validation
    ├── images.py           # Image retrieval from the database
    ├── task_status.py      # Real-time task progress monitoring
    └── tasks.py            # Task listing and metadata operations
├── utils/                  # Shared utilities and helper functions
    ├── database.py         # Async database connection management
    ├── image_processing.py # Image transformation and format validation
    └── lifespan.py         # FastAPI lifespan event context manager
└── venv/                   # Python virtual environment (development only)

# Infrastructure & Deployment
local.txt               # Development dependencies 
requirements.txt        # Production-optimized dependencies
setup.sh                # Environment provisioning and dependency installation
Dockerfile              # Multi-stage container build with optimized layers
docker-compose.yml      # Service orchestration for local development

```

## Acknowledgments
- [DataCrunch](www.datacrunch.io/) team for the access to GPU instance & infrastructure! 

 - Stability AI for Stable Diffusion models

 - Hugging Face for Diffusers library

 - FastAPI team for the excellent web framework

 - PyTorch team for the deep learning framework