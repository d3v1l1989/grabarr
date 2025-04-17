from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime
import json
from app.utils.cache import CacheManager
import aiohttp

from app.models.sonarr_instance import SonarrInstance
from app.schemas.sonarr_instance import SonarrInstanceCreate, SonarrInstanceUpdate

class SonarrInstanceService:
    def __init__(self, db: Session, cache: CacheManager):
        self.db = db
        self.cache = cache

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
        
        # Clear cache for instances list
        await self.cache.delete("instances:all")
        return db_instance

    async def get_instance(self, instance_id: int) -> Optional[SonarrInstance]:
        # Try to get from cache first
        cached = await self.cache.get(f"instance:{instance_id}")
        if cached:
            return SonarrInstance(**json.loads(cached))

        instance = self.db.query(SonarrInstance).filter(SonarrInstance.id == instance_id).first()
        if instance:
            # Cache the instance
            await self.cache.set(
                f"instance:{instance_id}",
                json.dumps({
                    "id": instance.id,
                    "name": instance.name,
                    "url": instance.url,
                    "api_key": instance.api_key,
                    "status": instance.status,
                    "last_checked": instance.last_checked.isoformat() if instance.last_checked else None,
                    "created_at": instance.created_at.isoformat(),
                    "updated_at": instance.updated_at.isoformat() if instance.updated_at else None
                }),
                expire=300  # 5 minutes
            )
        return instance

    async def get_all_instances(self) -> List[SonarrInstance]:
        # Try to get from cache first
        cached = await self.cache.get("instances:all")
        if cached:
            return [SonarrInstance(**instance) for instance in json.loads(cached)]

        instances = self.db.query(SonarrInstance).all()
        # Cache the instances
        await self.cache.set(
            "instances:all",
            json.dumps([{
                "id": instance.id,
                "name": instance.name,
                "url": instance.url,
                "api_key": instance.api_key,
                "status": instance.status,
                "last_checked": instance.last_checked.isoformat() if instance.last_checked else None,
                "created_at": instance.created_at.isoformat(),
                "updated_at": instance.updated_at.isoformat() if instance.updated_at else None
            } for instance in instances]),
            expire=300  # 5 minutes
        )
        return instances

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
        
        # Clear relevant caches
        await self.cache.delete(f"instance:{instance_id}")
        await self.cache.delete("instances:all")
        return db_instance

    async def delete_instance(self, instance_id: int) -> bool:
        db_instance = await self.get_instance(instance_id)
        if not db_instance:
            return False

        self.db.delete(db_instance)
        self.db.commit()
        
        # Clear relevant caches
        await self.cache.delete(f"instance:{instance_id}")
        await self.cache.delete("instances:all")
        return True

    async def _test_connection(self, url: str, api_key: str) -> bool:
        cache_key = f"connection_test:{url}"
        # Try to get from cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)

        try:
            async with httpx.AsyncClient() as client:
                headers = {"X-Api-Key": api_key}
                response = await client.get(f"{url}/api/v3/system/status", headers=headers)
                result = response.status_code == 200
                # Cache the result for 1 minute
                await self.cache.set(cache_key, json.dumps(result), expire=60)
                return result
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
        
        # Clear relevant caches
        await self.cache.delete(f"instance:{instance_id}")
        await self.cache.delete("instances:all")
        return db_instance

async def test_sonarr_connection(url: str, api_key: str) -> Dict[str, Any]:
    """
    Test connection to a Sonarr instance.
    Returns status and additional information if available.
    """
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"X-Api-Key": api_key}
            async with session.get(f"{url}/api/v3/system/status", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "online",
                        "version": data.get("version"),
                        "appName": data.get("appName"),
                        "isProduction": data.get("isProduction")
                    }
                else:
                    return {
                        "status": "offline",
                        "error": f"HTTP {response.status}: {await response.text()}"
                    }
    except aiohttp.ClientError as e:
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        } 