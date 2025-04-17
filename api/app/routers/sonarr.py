from fastapi import APIRouter, HTTPException
from typing import List, Optional
import httpx

router = APIRouter()

# Sonarr configuration
SONARR_API_KEY = os.getenv("SONARR_API_KEY")
SONARR_BASE_URL = os.getenv("SONARR_BASE_URL")

@router.get("/series")
async def get_series():
    """
    Get all series from Sonarr
    """
    if not SONARR_API_KEY or not SONARR_BASE_URL:
        raise HTTPException(status_code=500, detail="Sonarr configuration missing")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SONARR_BASE_URL}/api/v3/series",
                headers={"X-Api-Key": SONARR_API_KEY}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Sonarr: {str(e)}")

@router.get("/series/{series_id}")
async def get_series_by_id(series_id: int):
    """
    Get a specific series by ID from Sonarr
    """
    if not SONARR_API_KEY or not SONARR_BASE_URL:
        raise HTTPException(status_code=500, detail="Sonarr configuration missing")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SONARR_BASE_URL}/api/v3/series/{series_id}",
                headers={"X-Api-Key": SONARR_API_KEY}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Sonarr: {str(e)}") 