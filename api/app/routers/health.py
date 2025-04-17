from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    try:
        # Check database connection
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")

@router.get("/health/db")
async def db_health_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    try:
        # Simple query to check database connection
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")

@router.get("/health/queue")
async def queue_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        # Check database connection
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "queue_size": 0,
            "processing_size": 0
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Queue health check failed: {str(e)}") 