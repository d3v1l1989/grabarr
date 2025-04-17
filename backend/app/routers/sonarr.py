from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
import os

router = APIRouter()

class SonarrInstance(BaseModel):
    id: int
    name: str
    url: str
    api_key: str

@router.get("/instances", response_model=List[SonarrInstance])
async def get_instances():
    # TODO: Implement actual database query
    return []

@router.post("/instances", response_model=SonarrInstance)
async def create_instance(instance: SonarrInstance):
    # TODO: Implement actual database creation
    return instance

@router.put("/instances/{instance_id}", response_model=SonarrInstance)
async def update_instance(instance_id: int, instance: SonarrInstance):
    # TODO: Implement actual database update
    return instance

@router.delete("/instances/{instance_id}")
async def delete_instance(instance_id: int):
    # TODO: Implement actual database deletion
    return {"status": "success"} 