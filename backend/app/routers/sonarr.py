from fastapi import APIRouter

router = APIRouter()

@router.get("/sonarr/series")
async def get_series():
    return {"series": []}

@router.post("/sonarr/series")
async def add_series():
    return {"message": "Series added to Sonarr"}

@router.get("/sonarr/status")
async def get_sonarr_status():
    return {"status": "connected"} 