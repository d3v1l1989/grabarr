import pytest
from datetime import datetime, timedelta
import json
from app.services.queue_service import QueueService, SearchJob
from app.utils.cache import CacheManager
from app.services.smart_search import SmartSearchService

@pytest.fixture
async def redis_cache():
    cache = CacheManager("redis://localhost:7369/0")
    await cache.redis.flushdb()  # Clear Redis before tests
    yield cache
    await cache.redis.flushdb()  # Clear Redis after tests

@pytest.fixture
async def queue_service(redis_cache):
    return QueueService(redis_cache)

@pytest.mark.asyncio
async def test_add_search_with_smart_delay(queue_service, redis_cache):
    # Add a search job
    job_id = await queue_service.add_search(
        instance_id=1,
        episode_id=100,
        series_id=10,
        season_number=1,
        episode_number=1,
        priority=0
    )
    
    # Verify job was added to queue
    queue_jobs = await redis_cache.redis.zrange(queue_service.queue_key, 0, -1)
    assert len(queue_jobs) == 1
    
    job_data = json.loads(queue_jobs[0])
    assert job_data['job_id'] == job_id
    assert job_data['delay'] == 0  # Initial delay should be 0 for new pattern

@pytest.mark.asyncio
async def test_learn_from_successful_search(queue_service, redis_cache):
    # First search (should fail)
    job_id1 = await queue_service.add_search(
        instance_id=1,
        episode_id=100,
        series_id=10,
        season_number=1,
        episode_number=1,
        priority=0
    )
    
    # Complete with failure
    await queue_service.complete_job(job_id1, False, "Not found")
    
    # Second search with delay (should succeed)
    job_id2 = await queue_service.add_search(
        instance_id=1,
        episode_id=100,
        series_id=10,
        season_number=1,
        episode_number=1,
        priority=0
    )
    
    # Complete with success
    await queue_service.complete_job(job_id2, True)
    
    # Third search should use learned delay
    job_id3 = await queue_service.add_search(
        instance_id=1,
        episode_id=100,
        series_id=10,
        season_number=1,
        episode_number=1,
        priority=0
    )
    
    # Verify the pattern was learned
    smart_search = SmartSearchService(redis_cache)
    pattern = await smart_search.get_pattern(10, 1, 1)
    assert pattern.successful_delays.get(0, 0) > 0
    assert pattern.failed_delays.get(0, 0) > 0

@pytest.mark.asyncio
async def test_rate_limiting(queue_service, redis_cache):
    # Add multiple searches
    for i in range(15):  # More than max_searches_per_window
        await queue_service.add_search(
            instance_id=1,
            episode_id=100 + i,
            series_id=10,
            season_number=1,
            episode_number=1,
            priority=0
        )
    
    # Process jobs until rate limit is hit
    processed_count = 0
    while True:
        job = await queue_service.process_next_job()
        if not job:
            break
        processed_count += 1
        await queue_service.complete_job(job.job_id, True)
    
    # Verify rate limiting
    assert processed_count <= queue_service.max_searches_per_window

@pytest.mark.asyncio
async def test_concurrent_search_limit(queue_service, redis_cache):
    # Add multiple searches
    for i in range(5):  # More than max_concurrent_searches
        await queue_service.add_search(
            instance_id=1,
            episode_id=100 + i,
            series_id=10,
            season_number=1,
            episode_number=1,
            priority=0
        )
    
    # Start processing jobs
    processing_jobs = []
    for _ in range(5):
        job = await queue_service.process_next_job()
        if job:
            processing_jobs.append(job)
    
    # Verify concurrent search limit
    assert len(processing_jobs) <= queue_service.max_concurrent_searches

@pytest.mark.asyncio
async def test_queue_status(queue_service, redis_cache):
    # Add some jobs
    for i in range(3):
        await queue_service.add_search(
            instance_id=1,
            episode_id=100 + i,
            series_id=10,
            season_number=1,
            episode_number=1,
            priority=0
        )
    
    # Process some jobs
    for _ in range(2):
        job = await queue_service.process_next_job()
        if job:
            await queue_service.complete_job(job.job_id, True)
    
    # Check queue status
    status = await queue_service.get_queue_status()
    assert status['queue_size'] >= 0
    assert status['processing_size'] >= 0
    assert status['max_concurrent_searches'] == queue_service.max_concurrent_searches
    assert status['rate_limit_window'] == queue_service.rate_limit_window
    assert status['max_searches_per_window'] == queue_service.max_searches_per_window 