import signal
import asyncio
from typing import Callable, List

class ShutdownManager:
    def __init__(self):
        self.is_shutting_down = False
        self.cleanup_handlers: List[Callable] = []
        
    def add_cleanup_handler(self, handler: Callable):
        """Add a cleanup function to be called on shutdown"""
        if handler not in self.cleanup_handlers:
            self.cleanup_handlers.append(handler)
            print(f"✅ Registered cleanup handler: {handler.__name__}")
        
    async def run_cleanup(self):
        """Run all cleanup handlers asynchronously"""
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        print("🛑 Running cleanup handlers...")
        
        for handler in self.cleanup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()  # Call synchronous functions directly
                print(f"✅ Cleanup handler executed: {handler.__name__}")
            except Exception as e:
                print(f"❌ Cleanup handler failed: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"🛑 Received signal {signum}, initiating shutdown...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.run_cleanup())
            finally:
                loop.close()
                exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)  
        signal.signal(signal.SIGTERM, signal_handler) 
        print("✅ Signal handlers registered")

shutdown_manager = ShutdownManager()