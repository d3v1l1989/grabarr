import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.services.smart_search import SmartSearchService, SearchPattern
from app.utils.cache import CacheManager
import json

@pytest.fixture
def mock_cache():
    cache = AsyncMock(spec=CacheManager)
    cache.get.return_value = None
    return cache

@pytest.fixture
def smart_search(mock_cache):
    return SmartSearchService(mock_cache)

@pytest.mark.asyncio
async def test_get_pattern_new(smart_search, mock_cache):
    # Test getting a new pattern
    pattern = await smart_search.get_pattern(1, 1, 1)
    assert pattern.series_id == 1
    assert pattern.season_number == 1
    assert pattern.episode_number == 1
    assert pattern.successful_delays == {}
    assert pattern.failed_delays == {}
    assert pattern.last_successful_delay is None
    assert pattern.last_air_date is None

@pytest.mark.asyncio
async def test_get_pattern_existing(smart_search, mock_cache):
    # Test getting an existing pattern
    existing_pattern = {
        "1:1:1": {
            "successful_delays": {"0": 5, "60": 3},
            "failed_delays": {"0": 2},
            "last_successful_delay": 60,
            "last_air_date": "2023-01-01T00:00:00"
        }
    }
    mock_cache.get.return_value = str(existing_pattern)
    
    pattern = await smart_search.get_pattern(1, 1, 1)
    assert pattern.series_id == 1
    assert pattern.season_number == 1
    assert pattern.episode_number == 1
    assert pattern.successful_delays == {0: 5, 60: 3}
    assert pattern.failed_delays == {0: 2}
    assert pattern.last_successful_delay == 60
    assert pattern.last_air_date == datetime.fromisoformat("2023-01-01T00:00:00")

@pytest.mark.asyncio
async def test_update_pattern(smart_search, mock_cache):
    # Test updating a pattern
    pattern = SearchPattern(1, 1, 1)
    await smart_search.update_pattern(pattern, True, 60)
    
    # Verify the pattern was saved
    mock_cache.set.assert_called_once()
    saved_data = json.loads(mock_cache.set.call_args[0][1])
    assert "1:1:1" in saved_data
    assert saved_data["1:1:1"]["successful_delays"] == {"60": 1}
    assert saved_data["1:1:1"]["failed_delays"] == {}

@pytest.mark.asyncio
async def test_get_optimal_delay(smart_search, mock_cache):
    # Test getting optimal delay with no history
    delay = await smart_search.get_optimal_delay(1, 1, 1)
    assert delay == 0  # Should return 0 for no history
    
    # Test with successful history
    existing_pattern = {
        "1:1:1": {
            "successful_delays": {"0": 2, "60": 5},
            "failed_delays": {"0": 3},
            "last_successful_delay": 60
        }
    }
    mock_cache.get.return_value = str(existing_pattern)
    
    delay = await smart_search.get_optimal_delay(1, 1, 1)
    assert delay == 60  # Should return delay with highest success rate

@pytest.mark.asyncio
async def test_pattern_success_rate_calculation():
    # Test success rate calculation
    pattern = SearchPattern(1, 1, 1)
    pattern.successful_delays = {0: 2, 60: 5}
    pattern.failed_delays = {0: 3}
    
    optimal_delay = pattern.get_optimal_delay()
    assert optimal_delay == 60  # 60 has 100% success rate vs 0's 40% 