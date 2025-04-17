import httpx
from typing import Dict, Any, Optional
from ..models.sonarr_instance import SonarrInstance
from ..utils.cache import CacheManager, CacheKeys

class SonarrService:
    def __init__(self, instance: SonarrInstance, cache_manager: CacheManager):
        self.instance = instance
        self.base_url = instance.url.rstrip('/')
        self.api_key = instance.api_key
        self.cache = cache_manager
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def test_connection(self) -> bool:
        """Test connection to Sonarr instance"""
        cache_key = CacheKeys.SONARR_STATUS.format(id=self.instance.id)
        
        async def _test_connection():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v3/system/status",
                        headers=self.headers,
                        timeout=10.0
                    )
                    return response.status_code == 200
            except Exception:
                return False

        return await self.cache.get_or_set(cache_key, _test_connection, expire=300)  # 5 minutes cache

    async def get_series(self) -> Dict[str, Any]:
        """Get all series from Sonarr"""
        cache_key = f"sonarr:series:{self.instance.id}"
        
        async def _get_series():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v3/series",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()

        return await self.cache.get_or_set(cache_key, _get_series, expire=3600)  # 1 hour cache

    async def get_episodes(self, series_id: int) -> Dict[str, Any]:
        """Get episodes for a specific series"""
        cache_key = f"sonarr:episodes:{self.instance.id}:{series_id}"
        
        async def _get_episodes():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v3/episode",
                    headers=self.headers,
                    params={"seriesId": series_id}
                )
                response.raise_for_status()
                return response.json()

        return await self.cache.get_or_set(cache_key, _get_episodes, expire=1800)  # 30 minutes cache

    async def search_episode(self, episode_id: int) -> Dict[str, Any]:
        """Trigger a search for a specific episode"""
        # Don't cache search results as they should be fresh
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v3/command",
                headers=self.headers,
                json={
                    "name": "EpisodeSearch",
                    "episodeIds": [episode_id]
                }
            )
            response.raise_for_status()
            return response.json() 