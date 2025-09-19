import torch
from diffusers import StableDiffusionPipeline
from app.config import DEVICE
import gc

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
            print("🔄 Loading model...")
            self.pipe = load_model()
            self.is_loaded = True
            print("✅ Model loaded successfully")
        return self.pipe
    
    def get_model(self):
        """Get the loaded model, load if not already loaded"""
        if not self.is_loaded:
            return self.load()
        return self.pipe
    
    def cleanup(self):
        """Clean up model resources and free memory"""
        print("🧹 ENTERING cleanup method", flush=True)
        print(f"🧹 self.pipe: {self.pipe}", flush=True)
        print(f"🧹 self.is_loaded: {self.is_loaded}", flush=True)
        print(f"🧹 DEVICE: {DEVICE}", flush=True)
        print(f"🧹 torch.cuda.is_available(): {torch.cuda.is_available()}", flush=True)
        
        try:
            if self.pipe is not None:
                print("🧹 Pipe exists, starting cleanup...", flush=True)
                
                # Move to CPU first if using CUDA to properly release GPU memory
                if DEVICE != "cpu":
                    print("🧹 Moving model to CPU...", flush=True)
                    self.pipe = self.pipe.to("cpu")
                    print("🧹 Model moved to CPU", flush=True)
                
                print("🧹 Deleting pipe...", flush=True)
                del self.pipe
                self.pipe = None
                self.is_loaded = False
                print("🧹 Pipe deleted and flags reset", flush=True)
                
                print("🧹 Running garbage collection...", flush=True)
                gc.collect()
                print("🧹 Garbage collection completed", flush=True)
                
                if torch.cuda.is_available():
                    print("🧹 Clearing CUDA cache...", flush=True)
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                    print("🧹 CUDA cache cleared", flush=True)
                
                print("✅ Model resources cleaned up", flush=True)
                return True
            else:
                print("ℹ️  No cleanup needed (pipe was None)", flush=True)
                return True  
            
        except Exception as e:
            print(f"❌ Model cleanup failed: {e}", flush=True)
            import traceback
            traceback.print_exc()  # full stack trace
            return False
        finally:
            print("🧹 EXITING cleanup method", flush=True)
    
    # def cleanup(self):
    #     """Clean up model resources and free memory"""
    #     try:
    #         if self.pipe is not None:
    #             print("🧹 Cleaning up model resources...", flush=True)
    #             # Move to CPU first if using CUDA to properly release GPU memory
    #             if DEVICE != "cpu":
    #                 self.pipe = self.pipe.to("cpu")
                
    #             del self.pipe
    #             self.pipe = None
    #             self.is_loaded = False
                
    #             gc.collect()
                
    #             if torch.cuda.is_available():
    #                 torch.cuda.empty_cache()
    #                 torch.cuda.ipc_collect()
                
    #             print("✅ Model resources cleaned up", flush=True)
    #             return True
    #         return False
    #     except Exception as e:
    #         print(f"❌ Model cleanup failed: {e}", flush=True)
    #         return False

model_loader = ModelLoader()

def cleanup_models():
    """Clean up model resources - to be called by midnight cleanup & shutdown"""
    return model_loader.cleanup()

