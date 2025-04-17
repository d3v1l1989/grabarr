from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter()

class QueueItem(BaseModel):
    id: int
    title: str
    status: str
    progress: float

@router.get("/items", response_model=List[QueueItem])
async def get_queue_items():
    # TODO: Implement actual queue retrieval
    return []

@router.get("/items/{item_id}", response_model=QueueItem)
async def get_queue_item(item_id: int):
    # TODO: Implement actual item retrieval
    return QueueItem(id=item_id, title="Sample", status="pending", progress=0.0) 