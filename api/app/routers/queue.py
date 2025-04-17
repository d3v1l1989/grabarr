from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.utils.cache import CacheManager
from app.services.queue_service import QueueService
from app.services.worker_service import WorkerService
from pydantic import BaseModel

router = APIRouter()

class SearchRequest(BaseModel):
    instance_id: int
    episode_id: int
    priority: int = 0

class SearchResponse(BaseModel):
    job_id: str
    status: str

class QueueStatus(BaseModel):
    queue_size: int
    processing_size: int
    max_concurrent_searches: int
    rate_limit_window: int
    max_searches_per_window: int

class WorkerStatus(BaseModel):
    running: bool
    queue: QueueStatus

# Global worker service instance
_worker_service: Optional[WorkerService] = None

def get_worker_service(db: Session = Depends(get_db)) -> WorkerService:
    global _worker_service
    if _worker_service is None:
        cache_manager = CacheManager("redis://redis:7369/0")
        _worker_service = WorkerService(db, cache_manager)
    return _worker_service

@router.post("/search", response_model=SearchResponse)
async def add_search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Add a new search job to the queue"""
    # Verify instance exists
    instance = db.query(SonarrInstance).filter(
        SonarrInstance.id == request.instance_id
    ).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Add to queue
    queue = QueueService(CacheManager("redis://redis:7369/0"))
    job_id = await queue.add_search(
        request.instance_id,
        request.episode_id,
        request.priority
    )

    return SearchResponse(job_id=job_id, status="queued")

@router.get("/status", response_model=WorkerStatus)
async def get_status(
    worker: WorkerService = Depends(get_worker_service)
):
    """Get current worker and queue status"""
    return await worker.get_status()

@router.post("/start")
async def start_worker(
    worker: WorkerService = Depends(get_worker_service)
):
    """Start the worker service"""
    await worker.start()
    return {"status": "started"}

@router.post("/stop")
async def stop_worker(
    worker: WorkerService = Depends(get_worker_service)
):
    """Stop the worker service"""
    await worker.stop()
    return {"status": "stopped"} 