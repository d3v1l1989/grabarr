from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, sonarr, queue
from app.graphql.router import graphql_router
from app.core.database import engine, Base
from app.services.advanced_queue import AdvancedQueueService

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="grabarr")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3456"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sonarr.router, prefix="/api/sonarr", tags=["sonarr"])
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
app.include_router(graphql_router)

@app.on_event("startup")
async def startup_event():
    app.state.queue_service = AdvancedQueueService(
        cache=app.state.cache,
        max_concurrent_searches=3,
        rate_limit_window=60,
        max_searches_per_window=10
    )

@app.get("/")
async def root():
    return {"message": "grabarr API"}

@app.get("/api/queue/stats")
async def get_queue_stats(queue_service: AdvancedQueueService = Depends(get_queue_service)):
    stats = await queue_service.get_queue_status()
    return stats

@app.post("/api/queue/jobs")
async def schedule_job(
    job: AdvancedSearchJob,
    queue_service: AdvancedQueueService = Depends(get_queue_service)
):
    await queue_service.add_job(job)
    return {"status": "success", "job_id": job.job_id}

@app.post("/api/queue/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    queue_service: AdvancedQueueService = Depends(get_queue_service)
):
    success = await queue_service.retry_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to retry job")
    return {"status": "success"}

@app.post("/api/queue/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    queue_service: AdvancedQueueService = Depends(get_queue_service)
):
    success = await queue_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel job")
    return {"status": "success"} 