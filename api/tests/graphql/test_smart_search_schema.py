import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.services.smart_search import SmartSearchService
from app.utils.cache import CacheManager
import json

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def redis_cache():
    cache = CacheManager("redis://localhost:7369/0")
    await cache.redis.flushdb()  # Clear Redis before tests
    yield cache
    await cache.redis.flushdb()  # Clear Redis after tests

@pytest.mark.asyncio
async def test_smart_search_stats_query(client, redis_cache):
    # Setup test data
    smart_search = SmartSearchService(redis_cache)
    pattern = await smart_search.get_pattern(1, 1, 1)
    await smart_search.update_pattern(pattern, True, 60)
    await smart_search.update_pattern(pattern, True, 60)
    await smart_search.update_pattern(pattern, False, 0)
    
    # Query smart search stats
    query = """
    query {
        smartSearchStats {
            totalPatterns
            averageSuccessRate
            mostCommonDelay
            patterns {
                seriesId
                seasonNumber
                episodeNumber
                successfulDelays
                failedDelays
                lastSuccessfulDelay
            }
        }
    }
    """
    
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    
    data = response.json()["data"]["smartSearchStats"]
    assert data["totalPatterns"] == 1
    assert 0.5 <= data["averageSuccessRate"] <= 1.0  # 2/3 success rate
    assert data["mostCommonDelay"] == 60
    
    pattern_data = data["patterns"][0]
    assert pattern_data["seriesId"] == 1
    assert pattern_data["seasonNumber"] == 1
    assert pattern_data["episodeNumber"] == 1
    assert pattern_data["successfulDelays"] == {"60": 2}
    assert pattern_data["failedDelays"] == {"0": 1}
    assert pattern_data["lastSuccessfulDelay"] == 60

@pytest.mark.asyncio
async def test_schedule_search_with_smart_delay(client, redis_cache):
    # Setup test data
    smart_search = SmartSearchService(redis_cache)
    pattern = await smart_search.get_pattern(1, 1, 1)
    await smart_search.update_pattern(pattern, True, 60)
    
    # Schedule a search
    mutation = """
    mutation ScheduleSearch($input: ScheduleSearchInput!) {
        scheduleSearch(input: $input) {
            id
            episodeId
            instanceId
            scheduledTime
            status
            priority
        }
    }
    """
    
    variables = {
        "input": {
            "episodeId": 100,
            "instanceId": 1,
            "priority": 0
        }
    }
    
    response = client.post(
        "/graphql",
        json={
            "query": mutation,
            "variables": variables
        }
    )
    
    assert response.status_code == 200
    data = response.json()["data"]["scheduleSearch"]
    assert data["status"] == "queued"
    assert data["priority"] == 0
    
    # Verify the job was added with the learned delay
    queue_service = QueueService(redis_cache)
    queue_jobs = await redis_cache.redis.zrange(queue_service.queue_key, 0, -1)
    job_data = json.loads(queue_jobs[0])
    assert job_data["delay"] == 60  # Should use the learned delay 