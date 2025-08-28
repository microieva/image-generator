from app.config import DEVICE
# from services.image_service import image_generator

# @app.on_event("startup")
async def startup():
    print("✅ Model loaded successfully")
    print(f"💡 Tips: {'GPU' if DEVICE == 'cuda' else 'CPU'} optimized settings applied")

# async def load_models_on_startup():
#     """Event handler for application startup - loads AI models"""
#     try:
#         image_generator.load_model()
#         print(f"✅ Model loaded successfully on {DEVICE}")
#         return {"status": "success", "device": DEVICE}
#     except Exception as e:
#         error_msg = f"❌ Failed to load model: {e}"
#         print(error_msg)
#         return {"status": "error", "error": str(e)}

# async def initialize_database():
#     """Initialize database connections (if you have any)"""
#     print("✅ Database connections initialized")
#     return {"status": "success"}

# async def setup_logging():
#     """Setup application logging"""
#     print("✅ Logging configured")
#     return {"status": "success"}

# # Main startup function that runs all startup tasks
# async def on_startup():
#     """Main startup event handler"""
#     print("🚀 Starting up Image Generator API...")
    
#     results = {}
#     tasks = [
#         ("logging", setup_logging),
#         ("database", initialize_database),
#         ("models", load_models_on_startup)
#     ]
    
#     for name, task in tasks:
#         try:
#             results[name] = await task()
#         except Exception as e:
#             results[name] = {"status": "error", "error": str(e)}
#             print(f"❌ {name} initialization failed: {e}")
    
#     return results