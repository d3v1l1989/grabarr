from typing import Dict, Any, Optional, List
import json
import time
import uuid
from datetime import datetime, timedelta
from app.utils.cache import CacheManager
from app.services.smart_search import SmartSearchService

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
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.queue_key = "search_queue"
        self.processing_key = "processing"
        self.smart_search = SmartSearchService(cache_manager)
        self.rate_limit_key = "search:rate_limit:{instance_id}"
        self.max_concurrent_searches = 3
        self.rate_limit_window = 300  # 5 minutes
        self.max_searches_per_window = 10

    async def add_search(self, instance_id: int, episode_id: int, series_id: int,
                        season_number: int, episode_number: int, priority: int = 0) -> str:
        # Get optimal delay from smart search
        optimal_delay = await self.smart_search.get_optimal_delay(
            series_id, season_number, episode_number
        )
        
        job_id = str(uuid.uuid4())
        job = SearchJob(
            job_id=job_id,
            instance_id=instance_id,
            episode_id=episode_id,
            series_id=series_id,
            season_number=season_number,
            episode_number=episode_number,
            priority=priority,
            delay=optimal_delay
        )
        
        job_data = {
            'job_id': job.job_id,
            'instance_id': job.instance_id,
            'episode_id': job.episode_id,
            'series_id': job.series_id,
            'season_number': job.season_number,
            'episode_number': job.episode_number,
            'priority': job.priority,
            'delay': job.delay,
            'created_at': job.created_at.isoformat(),
            'status': job.status,
            'retry_count': job.retry_count,
            'last_attempt': job.last_attempt.isoformat() if job.last_attempt else None,
            'error': job.error
        }
        
        await self.cache.redis.zadd(
            self.queue_key,
            {json.dumps(job_data): -priority}  # Negative priority for correct ordering
        )
        
        return job_id

    async def process_next_job(self) -> Optional[SearchJob]:
        # Check rate limiting
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=self.rate_limit_window)
        
        processing_jobs = await self.cache.redis.zrange(self.processing_key, 0, -1)
        recent_jobs = [
            job for job in processing_jobs
            if datetime.fromisoformat(json.loads(job)['created_at']) > window_start
        ]
        
        if len(recent_jobs) >= self.max_searches_per_window:
            return None
        
        # Get next job from queue
        job_data = await self.cache.redis.zrange(self.queue_key, -1, -1)
        if not job_data:
            return None
        
        job_dict = json.loads(job_data[0])
        job = SearchJob(
            job_id=job_dict['job_id'],
            instance_id=job_dict['instance_id'],
            episode_id=job_dict['episode_id'],
            series_id=job_dict['series_id'],
            season_number=job_dict['season_number'],
            episode_number=job_dict['episode_number'],
            priority=job_dict['priority'],
            delay=job_dict['delay']
        )
        
        # Move to processing
        await self.cache.redis.zrem(self.queue_key, job_data[0])
        await self.cache.redis.zadd(
            self.processing_key,
            {job_data[0]: datetime.utcnow().timestamp()}
        )
        
        return job

    async def complete_job(self, job_id: str, success: bool, error: Optional[str] = None):
        processing_jobs = await self.cache.redis.zrange(self.processing_key, 0, -1)
        for job_data in processing_jobs:
            job_dict = json.loads(job_data)
            if job_dict['job_id'] == job_id:
                job_dict['status'] = 'completed' if success else 'failed'
                job_dict['last_attempt'] = datetime.utcnow().isoformat()
                job_dict['error'] = error
                
                # Update smart search pattern
                await self.smart_search.update_pattern(
                    await self.smart_search.get_pattern(
                        job_dict['series_id'],
                        job_dict['season_number'],
                        job_dict['episode_number']
                    ),
                    success,
                    job_dict['delay']
                )
                
                await self.cache.redis.zrem(self.processing_key, job_data)
                break

    async def get_queue_status(self) -> Dict:
        queue_size = await self.cache.redis.zcard(self.queue_key)
        processing_size = await self.cache.redis.zcard(self.processing_key)
        
        return {
            'queue_size': queue_size,
            'processing_size': processing_size,
            'max_concurrent_searches': self.max_concurrent_searches,
            'rate_limit_window': self.rate_limit_window,
            'max_searches_per_window': self.max_searches_per_window
        } 