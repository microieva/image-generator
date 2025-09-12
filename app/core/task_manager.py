import asyncio
from typing import Set, Dict, Any, Optional
from concurrent.futures import Future
from datetime import datetime
import uuid
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

@dataclass
class TaskInfo:
    task_id: str
    status: TaskStatus
    progress: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request: Optional[Dict] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    prompt: Optional[str] = None

class TaskManager:
    def __init__(self):
        self.task_metadata: Dict[str, TaskInfo] = {}  

    def create_task(self, request: Dict, prompt: str) -> str:
        """Create a new task with metadata and return its ID."""
        task_id = str(uuid.uuid4())
        
        task_info = TaskInfo(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0.0,
            created_at=datetime.now().isoformat(),
            request=request,
            prompt=prompt
        )
        
        self.task_metadata[task_id] = task_info
        return task_id

    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task metadata."""
        return self.task_metadata.get(task_id)

    def update_task_progress(self, task_id: str, progress: float) -> None:
        """Update task progress."""
        if task_id in self.task_metadata:
            self.task_metadata[task_id].progress = progress
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
      """Update task status."""
      if task_id in self.task_metadata:
          self.task_metadata[task_id].status = status
          if status == TaskStatus.PROCESSING and not self.task_metadata[task_id].started_at:
              self.task_metadata[task_id].started_at = datetime.now().isoformat()
          elif status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.ERROR]:
              self.task_metadata[task_id].completed_at = datetime.now().isoformat()
          print(f"🔄 Status updated: {task_id} -> {status}")

    def mark_task_completed(self, task_id: str, result: Dict) -> None:
        """Mark task as completed with result."""
        if task_id in self.task_metadata:
            self.task_metadata[task_id].status = TaskStatus.COMPLETED
            self.task_metadata[task_id].completed_at = datetime.now().isoformat()
            self.task_metadata[task_id].result = result
            self.task_metadata[task_id].progress = 100.0

    def mark_task_cancelled(self, task_id: str) -> None:
        """Mark task as cancelled."""
        if task_id in self.task_metadata:
            self.task_metadata[task_id].status = TaskStatus.CANCELLED
            self.task_metadata[task_id].completed_at = datetime.now().isoformat()

    def mark_task_error(self, task_id: str, error: str) -> None:
        """Mark task as error."""
        if task_id in self.task_metadata:
            self.task_metadata[task_id].status = TaskStatus.ERROR
            self.task_metadata[task_id].completed_at = datetime.now().isoformat()
            self.task_metadata[task_id].error = error

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task if it's pending or processing."""

        print(f"🔄 Attempting to cancel task: {task_id}")
        
        task_info = self.get_task_info(task_id)
        if not task_info:
            print(f"❌ Task {task_id} not found in metadata")
            return False
        
        if task_info.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            print(f"⚠️  Task {task_id} is already {task_info.status}, cannot cancel")
            return False
        
        print(f"✅ Marking task {task_id} as cancelled (status: {task_info.status} → {TaskStatus.CANCELLED})")
        self.mark_task_cancelled(task_id)
    
        return True

    def cancel_all(self) -> Dict[str, int]:
        """Cancel all ongoing tasks and return counts."""
        print("🔄 Starting cancel_all operation...")
        
        total_cancelled = 0
        
        print(f"   Found {len(self.task_metadata)} tasks in metadata")    
        for task_id, task_info in list(self.task_metadata.items()):
            if task_info.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                print(f"   Marking task {task_id} as cancelled")
                self.mark_task_cancelled(task_id)
                total_cancelled += 1
        
        result = {
            "total_cancelled": total_cancelled
        }
        
        print(f"✅ cancel_all completed: {result}")
        return result
    
    def delete_all(self) -> Dict[str, int]:
        """Delete all tasks from the manager and return counts."""
        print("🗑️  Starting delete_all operation...")
        
        total_tasks = len(self.task_metadata)
        completed_tasks = 0
        ongoing_tasks = 0
        
        for task_info in self.task_metadata.values():
            if task_info.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.ERROR]:
                completed_tasks += 1
            else:
                ongoing_tasks += 1
        
        self.task_metadata.clear()
        self.task_metadata = {}  
        
        result = {
            "total_deleted": total_tasks,
            "completed_tasks_deleted": completed_tasks,
            "ongoing_tasks_deleted": ongoing_tasks
        }
        
        print(f"✅ delete_all completed: {result}")
        return result

    def _find_task_by_id(self, task_id: str) -> Optional[asyncio.Task]:
        """Find async task by ID."""
        for task in self.task_metadata:
            if str(id(task)) == task_id:
                return task
        return None

    def list_all_tasks(self) -> Dict[str, Any]:
        """List all tasks with their metadata."""
        print(f"*** CALLING ALL TASKS ***")
        return {task_id: asdict(info) for task_id, info in self.task_metadata.items()}

    def list_ongoing_tasks(self) -> Dict[str, Any]:
        """List only ongoing tasks."""
        ongoing = {}
        for task_id, info in self.task_metadata.items():
            if info.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                ongoing[task_id] = asdict(info)
        return ongoing

    @property
    def count(self) -> int:
        """Return number of ongoing tasks."""
        return len(self.list_ongoing_tasks())