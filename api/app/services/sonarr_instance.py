from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime

from app.models.sonarr_instance import SonarrInstance
from app.schemas.sonarr_instance import SonarrInstanceCreate, SonarrInstanceUpdate

class SonarrInstanceService:
    def __init__(self, db: Session):
        self.db = db

    async def create_instance(self, instance: SonarrInstanceCreate) -> SonarrInstance:
        # Test connection before creating
        if not await self._test_connection(instance.url, instance.api_key):
            raise HTTPException(status_code=400, detail="Failed to connect to Sonarr instance")

        db_instance = SonarrInstance(
            name=instance.name,
            url=str(instance.url),
            api_key=instance.api_key,
            status="online",
            last_checked=datetime.utcnow()
        )
        self.db.add(db_instance)
        self.db.commit()
        self.db.refresh(db_instance)
        return db_instance

    async def get_instance(self, instance_id: int) -> Optional[SonarrInstance]:
        return self.db.query(SonarrInstance).filter(SonarrInstance.id == instance_id).first()

    async def get_all_instances(self) -> List[SonarrInstance]:
        return self.db.query(SonarrInstance).all()

    async def update_instance(self, instance_id: int, instance: SonarrInstanceUpdate) -> Optional[SonarrInstance]:
        db_instance = await self.get_instance(instance_id)
        if not db_instance:
            return None

        update_data = instance.dict(exclude_unset=True)
        
        # If URL or API key is being updated, test the connection
        if "url" in update_data or "api_key" in update_data:
            url = update_data.get("url", db_instance.url)
            api_key = update_data.get("api_key", db_instance.api_key)
            if not await self._test_connection(url, api_key):
                raise HTTPException(status_code=400, detail="Failed to connect to Sonarr instance")

        for key, value in update_data.items():
            setattr(db_instance, key, value)

        db_instance.last_checked = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_instance)
        return db_instance

    async def delete_instance(self, instance_id: int) -> bool:
        db_instance = await self.get_instance(instance_id)
        if not db_instance:
            return False

        self.db.delete(db_instance)
        self.db.commit()
        return True

    async def _test_connection(self, url: str, api_key: str) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                headers = {"X-Api-Key": api_key}
                response = await client.get(f"{url}/api/v3/system/status", headers=headers)
                return response.status_code == 200
        except Exception:
            return False

    async def check_instance_status(self, instance_id: int) -> Optional[SonarrInstance]:
        db_instance = await self.get_instance(instance_id)
        if not db_instance:
            return None

        is_online = await self._test_connection(db_instance.url, db_instance.api_key)
        db_instance.status = "online" if is_online else "offline"
        db_instance.last_checked = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_instance)
        return db_instance 