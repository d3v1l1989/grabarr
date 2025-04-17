from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    version: str

@router.get("/", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="ok", version="1.0.0") 