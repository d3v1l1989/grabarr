# Standard library imports
import asyncio
from collections import deque
from datetime import datetime
from typing import Dict, Any, Optional

class SearchJob:
    def __init__(self, job_id: str, instance_id: int, episode_id: int, series_id: int, 
                 season_number: int, episode_number: int, priority: int = 0, delay: int = 0):
        self.job_id = job_id
        self.instance_id = instance_id
        self.episode_id = episode_id
        self.series_id = series_id
        self.season_number = season_number
        self.episode_number = episode_number
        self.priority = priority
        self.delay = delay
        self.created_at = datetime.utcnow()
        self.status = "queued"
        self.retry_count = 0
        self.last_attempt = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "instance_id": self.instance_id,
            "episode_id": self.episode_id,
            "series_id": self.series_id,
            "season_number": self.season_number,
            "episode_number": self.episode_number,
            "priority": self.priority,
            "delay": self.delay,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "retry_count": self.retry_count,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchJob':
        job = cls(
            job_id=data["job_id"],
            instance_id=data["instance_id"],
            episode_id=data["episode_id"],
            series_id=data["series_id"],
            season_number=data["season_number"],
            episode_number=data["episode_number"],
            priority=data["priority"],
            delay=data["delay"]
        )
        job.created_at = datetime.fromisoformat(data["created_at"])
        job.status = data["status"]
        job.retry_count = data["retry_count"]
        job.last_attempt = datetime.fromisoformat(data["last_attempt"]) if data["last_attempt"] else None
        job.error = data["error"]
        return job

class QueueService:
    def __init__(self):
        self.queue = deque()
        self.processing = deque()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def add_search(self, search_data: Dict[str, Any]) -> str:
        job_id = str(len(self.jobs) + 1)
        self.jobs[job_id] = {
            **search_data,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self.queue.append(job_id)
        return job_id

    async def get_next_job(self) -> Optional[Dict[str, Any]]:
        async with self.lock:
            if not self.queue:
                return None
            
            job_id = self.queue.popleft()
            job = self.jobs[job_id]
            job["status"] = "processing"
            job["updated_at"] = datetime.utcnow().isoformat()
            self.processing.append(job_id)
            return job

    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        async with self.lock:
            if job_id in self.processing:
                self.processing.remove(job_id)
            if job_id in self.jobs:
                self.jobs[job_id].update({
                    "status": "completed",
                    "result": result,
                    "updated_at": datetime.utcnow().isoformat()
                })

    async def get_queue_status(self) -> Dict[str, Any]:
        return {
            "queued": len(self.queue),
            "processing": len(self.processing),
            "total_jobs": len(self.jobs)
        }

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id) 