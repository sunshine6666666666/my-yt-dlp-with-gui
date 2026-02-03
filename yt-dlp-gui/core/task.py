from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import subprocess

class TaskStatus(Enum):
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class Task:
    id: str
    url: str
    title: str = ""
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error: str = ""
    notice: str = ""
    
    # Non-serializable field
    process: Optional[subprocess.Popen] = field(default=None, repr=False, compare=False)

    def to_dict(self):
        """Convert to dictionary for serialization, excluding process."""
        data = asdict(self)
        data['status'] = self.status.value
        if 'process' in data:
            del data['process']
        return data

    @classmethod
    def from_dict(cls, data):
        """Create Task instance from dictionary."""
        if 'status' in data:
            data['status'] = TaskStatus(data['status'])
        return cls(**data)
