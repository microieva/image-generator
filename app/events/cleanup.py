from fastapi import FastAPI

async def midnight_cleanup(app: FastAPI):
    """Scheduled function to delete all tasks every midnight"""

    task_manager = app.state.task_manager
    cancel_result = task_manager.cancel_all()
    print(f"📊 Cancellation result: {cancel_result}")
    
    delete_result = task_manager.delete_all()
    print(f"📊 Deletion result: {delete_result}")