# from services.image_service import image_generator
# import torch

# async def cleanup_models():
#     """Clean up model resources and free GPU memory"""
#     try:
#         if hasattr(image_generator, 'pipe') and image_generator.pipe:
#             # Clear pipeline and free memory
#             del image_generator.pipe
#             image_generator.pipe = None
#             image_generator.is_loaded = False
        
#         if torch.cuda.is_available():
#             torch.cuda.empty_cache()
        
#         print("✅ Model resources cleaned up")
#         return {"status": "success"}
#     except Exception as e:
#         print(f"❌ Model cleanup failed: {e}")
#         return {"status": "error", "error": str(e)}

# async def close_database_connections():
#     """Close database connections (if you have any)"""
#     print("✅ Database connections closed")
#     return {"status": "success"}

# async def on_shutdown():
#     """Main shutdown event handler"""
#     print("🛑 Shutting down Image Generator API...")
    
#     results = {}
#     tasks = [
#         ("models", cleanup_models),
#         ("database", close_database_connections)
#     ]
    
#     for name, task in tasks:
#         try:
#             results[name] = await task()
#         except Exception as e:
#             results[name] = {"status": "error", "error": str(e)}
#             print(f"❌ {name} cleanup failed: {e}")
    
#     return results