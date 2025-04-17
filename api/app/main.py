from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, sonarr, queue, health
from app.graphql.router import graphql_router
from app.core.database import engine, Base
from app.config import settings
from app.core.logging import setup_logging
from app.services.queue_service import QueueService
from typing import Dict, Any

# Setup logging
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Grabarr API",
    description="API for Grabarr application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sonarr.router, prefix="/api/sonarr", tags=["sonarr"])
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(graphql_router)

@app.get("/")
async def root():
    return {"message": "grabarr API"}

@app.get("/api/queue/stats")
async def get_queue_stats(queue_service: QueueService = Depends(QueueService)):
    stats = await queue_service.get_queue_status()
    return stats

@app.post("/api/queue/jobs")
async def schedule_job(
    job: Dict[str, Any],
    queue_service: QueueService = Depends(QueueService)
):
    job_id = await queue_service.add_search(job)
    return {"status": "success", "job_id": job_id}

@app.post("/api/queue/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    queue_service: QueueService = Depends(QueueService)
):
    job = await queue_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "failed":
        raise HTTPException(status_code=400, detail="Job is not in failed state")
    
    await queue_service.add_search(job)
    return {"status": "success"}

@app.post("/api/queue/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    queue_service: QueueService = Depends(QueueService)
):
    job = await queue_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] not in ["queued", "processing"]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled in its current state")
    
    job["status"] = "cancelled"
    return {"status": "success"} 