import asyncio
from typing import Optional, Dict, Any
from app.services.queue_service import QueueService, SearchJob
from app.services.sonarr_service import SonarrService
from app.models.sonarr_instance import SonarrInstance
from sqlalchemy.orm import Session
from app.utils.cache import CacheManager
from app.utils.retry import RetryHandler, RetryConfig, RetryableError

class WorkerService:
    def __init__(self, db: Session, cache_manager: CacheManager):
        self.db = db
        self.cache = cache_manager
        self.queue = QueueService(cache_manager)
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.retry_handler = RetryHandler(
            RetryConfig(
                initial_delay=1.0,
                max_delay=60.0,
                max_retries=5,
                backoff_factor=2.0
            )
        )

    async def start(self):
        """Start the worker service"""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop the worker service"""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _process_job(self, job: SearchJob) -> bool:
        """Process a single job with retry logic"""
        async def process_operation():
            try:
                # Get Sonarr instance
                instance = self.db.query(SonarrInstance).filter(
                    SonarrInstance.id == job.instance_id
                ).first()

                if not instance:
                    raise RetryableError("Instance not found")

                # Create Sonarr service
                sonarr_service = SonarrService(instance, self.cache)

                # Execute the search
                result = await sonarr_service.search_episode(job.episode_id)
                return True
            except Exception as e:
                raise RetryableError(str(e))

        async def on_retry(retry_count: int, delay: float, error: Exception):
            # Update job status with retry information
            job.status = f"retrying ({retry_count}/{self.retry_handler.config.max_retries})"
            job.error = str(error)
            await self.queue.update_job_status(job)

        try:
            await self.retry_handler.execute_with_retry(
                process_operation,
                on_retry=on_retry
            )
            return True
        except RetryableError as e:
            # Final failure after all retries
            job.status = "failed"
            job.error = str(e)
            await self.queue.update_job_status(job)
            return False

    async def _process_queue(self):
        """Process the queue in a loop"""
        while self.running:
            try:
                # Get next job from queue
                job = await self.queue.get_next_job()
                if not job:
                    await asyncio.sleep(1)  # Wait if no jobs available
                    continue

                # Process the job with retry logic
                success = await self._process_job(job)
                
                if success:
                    await self.queue.complete_job(job.job_id)
                else:
                    await self.queue.fail_job(job.job_id)

            except Exception as e:
                # Log error and continue
                print(f"Error processing queue: {e}")
                await asyncio.sleep(1)  # Wait before retrying

    async def get_status(self) -> Dict[str, Any]:
        """Get worker and queue status"""
        queue_status = await self.queue.get_queue_status()
        return {
            "running": self.running,
            "queue": queue_status
        } 