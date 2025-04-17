from typing import Dict, Optional
from datetime import datetime, timedelta
import json
from app.utils.cache import CacheManager
from app.utils.retry import RetryableError

class SearchPattern:
    def __init__(self, series_id: int, season_number: int, episode_number: int):
        self.series_id = series_id
        self.season_number = season_number
        self.episode_number = episode_number
        self.successful_delays: Dict[int, int] = {}  # delay -> success count
        self.failed_delays: Dict[int, int] = {}     # delay -> failure count
        self.last_air_date: Optional[datetime] = None
        self.last_successful_delay: Optional[int] = None

    def record_success(self, delay: int):
        self.successful_delays[delay] = self.successful_delays.get(delay, 0) + 1
        self.last_successful_delay = delay

    def record_failure(self, delay: int):
        self.failed_delays[delay] = self.failed_delays.get(delay, 0) + 1

    def get_optimal_delay(self) -> int:
        if not self.successful_delays:
            return 0  # Default to immediate search if no history
        
        # Calculate success rate for each delay
        success_rates = {}
        for delay in set(self.successful_delays.keys()) | set(self.failed_delays.keys()):
            successes = self.successful_delays.get(delay, 0)
            failures = self.failed_delays.get(delay, 0)
            total = successes + failures
            if total > 0:
                success_rates[delay] = successes / total
        
        # Return delay with highest success rate
        return max(success_rates.items(), key=lambda x: x[1])[0]

class SmartSearchService:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.patterns_key = "search_patterns"
        self.learning_rate = 0.1  # How quickly to adapt to new patterns

    async def get_pattern(self, series_id: int, season_number: int, episode_number: int) -> SearchPattern:
        pattern_key = f"{series_id}:{season_number}:{episode_number}"
        patterns = await self._load_patterns()
        
        if pattern_key not in patterns:
            patterns[pattern_key] = SearchPattern(series_id, season_number, episode_number)
            await self._save_patterns(patterns)
        
        return patterns[pattern_key]

    async def update_pattern(self, pattern: SearchPattern, success: bool, delay: int):
        if success:
            pattern.record_success(delay)
        else:
            pattern.record_failure(delay)
        
        patterns = await self._load_patterns()
        pattern_key = f"{pattern.series_id}:{pattern.season_number}:{pattern.episode_number}"
        patterns[pattern_key] = pattern
        await self._save_patterns(patterns)

    async def get_optimal_delay(self, series_id: int, season_number: int, episode_number: int) -> int:
        pattern = await self.get_pattern(series_id, season_number, episode_number)
        return pattern.get_optimal_delay()

    async def _load_patterns(self) -> Dict[str, SearchPattern]:
        patterns_data = await self.cache.get(self.patterns_key)
        if not patterns_data:
            return {}
        
        patterns = {}
        for key, data in json.loads(patterns_data).items():
            series_id, season, episode = map(int, key.split(':'))
            pattern = SearchPattern(series_id, season, episode)
            pattern.successful_delays = data.get('successful_delays', {})
            pattern.failed_delays = data.get('failed_delays', {})
            pattern.last_successful_delay = data.get('last_successful_delay')
            if data.get('last_air_date'):
                pattern.last_air_date = datetime.fromisoformat(data['last_air_date'])
            patterns[key] = pattern
        
        return patterns

    async def _save_patterns(self, patterns: Dict[str, SearchPattern]):
        patterns_data = {}
        for key, pattern in patterns.items():
            patterns_data[key] = {
                'successful_delays': pattern.successful_delays,
                'failed_delays': pattern.failed_delays,
                'last_successful_delay': pattern.last_successful_delay,
                'last_air_date': pattern.last_air_date.isoformat() if pattern.last_air_date else None
            }
        
        await self.cache.set(self.patterns_key, json.dumps(patterns_data)) 