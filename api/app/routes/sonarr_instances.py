from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.sonarr_instance import SonarrInstanceService
from app.schemas.sonarr_instance import (
    SonarrInstanceCreate,
    SonarrInstanceUpdate,
    SonarrInstanceResponse
)

router = APIRouter()

@router.post("/", response_model=SonarrInstanceResponse)
async def create_instance(
    instance: SonarrInstanceCreate,
    db: Session = Depends(get_db)
):
    service = SonarrInstanceService(db)
    return await service.create_instance(instance)

@router.get("/", response_model=List[SonarrInstanceResponse])
def get_instances(db: Session = Depends(get_db)):
    service = SonarrInstanceService(db)
    return service.get_all_instances()

@router.get("/{instance_id}", response_model=SonarrInstanceResponse)
def get_instance(instance_id: int, db: Session = Depends(get_db)):
    service = SonarrInstanceService(db)
    instance = service.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance

@router.put("/{instance_id}", response_model=SonarrInstanceResponse)
async def update_instance(
    instance_id: int,
    instance: SonarrInstanceUpdate,
    db: Session = Depends(get_db)
):
    service = SonarrInstanceService(db)
    updated_instance = await service.update_instance(instance_id, instance)
    if not updated_instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return updated_instance

@router.delete("/{instance_id}")
def delete_instance(instance_id: int, db: Session = Depends(get_db)):
    service = SonarrInstanceService(db)
    if not service.delete_instance(instance_id):
        raise HTTPException(status_code=404, detail="Instance not found")
    return {"message": "Instance deleted successfully"}

@router.post("/{instance_id}/check", response_model=SonarrInstanceResponse)
async def check_instance_status(instance_id: int, db: Session = Depends(get_db)):
    service = SonarrInstanceService(db)
    instance = await service.check_instance_status(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance 