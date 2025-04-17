from fastapi import FastAPI
from app.routers import sonarr, queue, health
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title=os.getenv("PROJECT_NAME", "Grabarr"),
    version=os.getenv("VERSION", "1.0.0"),
    openapi_url=f"{os.getenv('API_V1_STR', '/api/v1')}/openapi.json"
)

app.include_router(sonarr.router, prefix=f"{os.getenv('API_V1_STR', '/api/v1')}/sonarr", tags=["sonarr"])
app.include_router(queue.router, prefix=f"{os.getenv('API_V1_STR', '/api/v1')}/queue", tags=["queue"])
app.include_router(health.router, prefix=f"{os.getenv('API_V1_STR', '/api/v1')}/health", tags=["health"]) 