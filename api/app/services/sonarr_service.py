from typing import Dict, Any, List, Optional
import httpx
from app.models.sonarr_instance import SonarrInstance

class SonarrService:
    def __init__(self, instance: SonarrInstance):
        self.instance = instance
        self.base_url = instance.url.rstrip('/')
        self.api_key = instance.api_key
        self.headers = {"X-Api-Key": self.api_key}

    async def get_series(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v3/series", headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_episodes(self, series_id: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v3/episode", headers=self.headers, params={"seriesId": series_id})
            response.raise_for_status()
            return response.json()

    async def get_episode(self, episode_id: int) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v3/episode/{episode_id}", headers=self.headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def search_episode(self, episode_id: int) -> Dict[str, Any]:
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