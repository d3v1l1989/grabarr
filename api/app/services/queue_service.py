from typing import Dict, Any, Optional, List
import json
import time
import uuid
from datetime import datetime
from app.utils.cache import CacheManager

class SearchJob:
    def __init__(self, job_id: str, instance_id: int, episode_id: int, priority: int = 0):
        self.job_id = job_id
        self.instance_id = instance_id
        self.episode_id = episode_id
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.status = "pending"
        self.retry_count = 0
        self.last_attempt = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "instance_id": self.instance_id,
            "episode_id": self.episode_id,
            "priority": self.priority,
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
            priority=data["priority"]
        )
        job.created_at = datetime.fromisoformat(data["created_at"])
        job.status = data["status"]
        job.retry_count = data["retry_count"]
        job.last_attempt = datetime.fromisoformat(data["last_attempt"]) if data["last_attempt"] else None
        job.error = data["error"]
        return job

class QueueService:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.queue_key = "search:queue"
        self.processing_key = "search:processing"
        self.rate_limit_key = "search:rate_limit:{instance_id}"
        self.max_concurrent_searches = 3
        self.rate_limit_window = 60  # 60 seconds
        self.max_searches_per_window = 10  # 10 searches per minute per instance

    async def add_search(self, instance_id: int, episode_id: int, priority: int = 0) -> str:
        """Add a search job to the queue with priority"""
        job_id = str(uuid.uuid4())
        job = SearchJob(job_id, instance_id, episode_id, priority)
        
        # Add to sorted set with priority score (higher priority = higher score)
        # We use timestamp as part of the score to maintain FIFO within same priority
        score = float(f"{priority}.{int(time.time())}")
        await self.cache.redis.zadd(
            self.queue_key,
            {json.dumps(job.to_dict()): score}
        )
        return job_id

    async def get_next_job(self) -> Optional[SearchJob]:
        """Get the next job from the queue based on priority"""
        # Get the highest priority job
        job_data = await self.cache.redis.zrange(self.queue_key, -1, -1)
        if not job_data:
            return None

        job_dict = json.loads(job_data[0])
        job = SearchJob.from_dict(job_dict)
        
        # Check if we can process this job (rate limit and concurrent searches)
        if not await self._can_process_job(job):
            return None

        # Move job to processing set
        await self.cache.redis.zrem(self.queue_key, job_data[0])
        await self.cache.redis.zadd(
            self.processing_key,
            {json.dumps(job.to_dict()): time.time()}
        )
        
        return job

    async def _can_process_job(self, job: SearchJob) -> bool:
        """Check if we can process a job based on rate limits and concurrent searches"""
        # Check concurrent searches
        processing_count = await self.cache.redis.zcard(self.processing_key)
        if processing_count >= self.max_concurrent_searches:
            return False

        # Check rate limit
        rate_limit_key = self.rate_limit_key.format(instance_id=job.instance_id)
        current_time = time.time()
        
        # Get searches in the current window
        window_start = current_time - self.rate_limit_window
        searches = await self.cache.redis.zrangebyscore(
            rate_limit_key,
            window_start,
            current_time
        )
        
        if len(searches) >= self.max_searches_per_window:
            return False
            
        return True

    async def update_job_status(self, job: SearchJob):
        """Update the status of a job in the processing set"""
        # Find and update the job in processing
        processing_jobs = await self.cache.redis.zrange(self.processing_key, 0, -1)
        for job_data in processing_jobs:
            job_dict = json.loads(job_data)
            if job_dict["job_id"] == job.job_id:
                # Remove old entry
                await self.cache.redis.zrem(self.processing_key, job_data)
                # Add updated entry
                await self.cache.redis.zadd(
                    self.processing_key,
                    {json.dumps(job.to_dict()): time.time()}
                )
                break

    async def complete_job(self, job_id: str):
        """Mark a job as completed"""
        # Find the job in processing
        processing_jobs = await self.cache.redis.zrange(self.processing_key, 0, -1)
        for job_data in processing_jobs:
            job_dict = json.loads(job_data)
            if job_dict["job_id"] == job_id:
                job = SearchJob.from_dict(job_dict)
                job.status = "completed"
                job.last_attempt = datetime.utcnow()
                
                # Remove from processing
                await self.cache.redis.zrem(self.processing_key, job_data)
                
                # Update rate limit tracking
                rate_limit_key = self.rate_limit_key.format(instance_id=job.instance_id)
                await self.cache.redis.zadd(
                    rate_limit_key,
                    {job_id: time.time()}
                )
                
                # Clean up old rate limit entries
                await self.cache.redis.zremrangebyscore(
                    rate_limit_key,
                    0,
                    time.time() - self.rate_limit_window
                )
                break

    async def fail_job(self, job_id: str):
        """Mark a job as failed"""
        # Find the job in processing
        processing_jobs = await self.cache.redis.zrange(self.processing_key, 0, -1)
        for job_data in processing_jobs:
            job_dict = json.loads(job_data)
            if job_dict["job_id"] == job_id:
                job = SearchJob.from_dict(job_dict)
                job.status = "failed"
                job.last_attempt = datetime.utcnow()
                
                # Remove from processing
                await self.cache.redis.zrem(self.processing_key, job_data)
                break

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        queue_size = await self.cache.redis.zcard(self.queue_key)
        processing_size = await self.cache.redis.zcard(self.processing_key)
        
        return {
            "queue_size": queue_size,
            "processing_size": processing_size,
            "max_concurrent_searches": self.max_concurrent_searches,
            "rate_limit_window": self.rate_limit_window,
            "max_searches_per_window": self.max_searches_per_window
        } 