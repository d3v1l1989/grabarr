from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum
from app.utils.cache import CacheManager
from app.services.smart_search import SmartSearchService
from uuid import UUID, uuid4
from pydantic import BaseModel
from aiocache import Cache

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class JobDependency(BaseModel):
    job_id: UUID
    must_complete: bool = True

class RetryPolicy(BaseModel):
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    backoff_factor: float = 2.0

class AdvancedSearchJob(BaseModel):
    job_id: UUID = uuid4()
    instance_id: UUID
    episode_id: int
    priority: JobPriority = JobPriority.MEDIUM
    dependencies: List[JobDependency] = []
    retry_policy: RetryPolicy = RetryPolicy()
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    retry_count: int = 0
    error: Optional[str] = None

class AdvancedQueueService:
    def __init__(
        self,
        cache: Cache,
        max_concurrent_searches: int = 3,
        rate_limit_window: int = 60,
        max_searches_per_window: int = 10
    ):
        self.cache = cache
        self.max_concurrent_searches = max_concurrent_searches
        self.rate_limit_window = rate_limit_window
        self.max_searches_per_window = max_searches_per_window
        self.queue_key = "advanced_queue:jobs"
        self.processing_key = "advanced_queue:processing"
        self.stats_key = "advanced_queue:stats"
        self.smart_search = SmartSearchService(CacheManager(cache))

    async def add_job(self, job: AdvancedSearchJob) -> None:
        # Check dependencies
        for dep in job.dependencies:
            dep_job = await self.get_job(dep.job_id)
            if not dep_job or dep_job.status != JobStatus.COMPLETED:
                if dep.must_complete:
                    raise ValueError(f"Dependency job {dep.job_id} not completed")
                job.status = JobStatus.PENDING
            else:
                job.status = JobStatus.PENDING

        # Add to queue
        await self.cache.sadd(self.queue_key, job.job_id)
        await self.cache.set(f"job:{job.job_id}", job.json())

    async def get_job(self, job_id: UUID) -> Optional[AdvancedSearchJob]:
        job_data = await self.cache.get(f"job:{job_id}")
        if job_data:
            return AdvancedSearchJob.parse_raw(job_data)
        return None

    async def retry_job(self, job_id: UUID) -> bool:
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.retry_count >= job.retry_policy.max_retries:
            return False

        job.retry_count += 1
        job.status = JobStatus.PENDING
        job.updated_at = datetime.utcnow()
        job.error = None

        await self.cache.set(f"job:{job.job_id}", job.json())
        await self.cache.sadd(self.queue_key, job.job_id)
        return True

    async def cancel_job(self, job_id: UUID) -> bool:
        job = await self.get_job(job_id)
        if not job:
            return False

        job.status = JobStatus.CANCELLED
        job.updated_at = datetime.utcnow()

        await self.cache.set(f"job:{job.job_id}", job.json())
        await self.cache.srem(self.queue_key, job.job_id)
        await self.cache.srem(self.processing_key, job.job_id)
        return True

    async def get_queue_status(self) -> Dict:
        queue_size = await self.cache.scard(self.queue_key)
        processing_size = await self.cache.scard(self.processing_key)

        # Get all jobs
        all_jobs = []
        queue_jobs = await self.cache.smembers(self.queue_key)
        processing_jobs = await self.cache.smembers(self.processing_key)

        for job_id in queue_jobs | processing_jobs:
            job = await self.get_job(UUID(job_id))
            if job:
                all_jobs.append(job)

        # Calculate statistics
        stats = {
            "queue_size": queue_size,
            "processing_size": processing_size,
            "jobs_by_status": {},
            "jobs_by_priority": {},
            "total_jobs": len(all_jobs)
        }

        for status in JobStatus:
            stats["jobs_by_status"][status] = len([
                job for job in all_jobs if job.status == status
            ])

        for priority in JobPriority:
            stats["jobs_by_priority"][priority] = len([
                job for job in all_jobs if job.priority == priority
            ])

        return stats

    async def process_next_job(self) -> Optional[AdvancedSearchJob]:
        # Get all pending jobs
        queue_jobs = await self.cache.smembers(self.queue_key)
        if not queue_jobs:
            return None

        # Get job details and sort by priority
        jobs = []
        for job_id in queue_jobs:
            job = await self.get_job(UUID(job_id))
            if job and job.status == JobStatus.PENDING:
                jobs.append(job)

        if not jobs:
            return None

        # Sort by priority (HIGH first) and creation time
        jobs.sort(
            key=lambda x: (
                JobPriority.HIGH == x.priority,
                JobPriority.MEDIUM == x.priority,
                x.created_at
            ),
            reverse=True
        )

        # Get the highest priority job
        next_job = jobs[0]
        next_job.status = JobStatus.PROCESSING
        next_job.updated_at = datetime.utcnow()

        # Update job status
        await self.cache.set(f"job:{next_job.job_id}", next_job.json())
        await self.cache.srem(self.queue_key, next_job.job_id)
        await self.cache.sadd(self.processing_key, next_job.job_id)

        return next_job

    async def complete_job(self, job_id: UUID, success: bool = True, error: Optional[str] = None) -> None:
        job = await self.get_job(job_id)
        if not job:
            return

        job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
        job.updated_at = datetime.utcnow()
        job.error = error

        await self.cache.set(f"job:{job.job_id}", job.json())
        await self.cache.srem(self.processing_key, job.job_id)

        # Update smart search pattern
        await self.smart_search.update_pattern(
            await self.smart_search.get_pattern(
                job.episode_id,
                job.episode_id,
                job.episode_id
            ),
            success,
            job.episode_id
        )

        # Handle dependent jobs
        for dep in job.dependencies:
            dep_job = await self.get_job(dep.job_id)
            if dep_job and dep_job.status != JobStatus.COMPLETED:
                # Check if all dependencies are met
                if dep.must_complete:
                    await self.add_job(dep_job)
                elif job.status == JobStatus.FAILED:
                    dep_job.status = JobStatus.FAILED
                    await self.add_job(dep_job)

        await self.cache.set(f"job:{job.job_id}", job.json())
        await self.cache.srem(self.processing_key, job.job_id) 