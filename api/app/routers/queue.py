# Standard library imports
from typing import Dict, Any, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Local application imports
from app.core.database import get_db
from app.services.queue_service import QueueService

router = APIRouter()

# Global queue service instance
_queue_service: Optional[QueueService] = None

def get_queue_service() -> QueueService:
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service

@router.post("/search")
async def add_search(search_data: Dict[str, Any]) -> Dict[str, str]:
    queue_service = get_queue_service()
    job_id = await queue_service.add_search(search_data)
    return {"job_id": job_id}

@router.get("/status")
async def get_queue_status() -> Dict[str, Any]:
    queue_service = get_queue_service()
    return await queue_service.get_queue_status()

@router.get("/job/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    queue_service = get_queue_service()
    job = await queue_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job 