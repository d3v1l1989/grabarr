from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sonarr_instance import SonarrInstance
from app.services.sonarr_instance import test_sonarr_connection
from app.services.queue_service import QueueService, SearchJob
from app.services.sonarr_service import SonarrService
from app.utils.cache import CacheManager
import json

class InstanceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UNKNOWN = "unknown"

class EpisodeType(BaseModel):
    id: int
    series_id: int
    season_number: int
    episode_number: int
    title: str
    air_date: Optional[datetime]
    monitored: bool
    has_file: bool
    quality: Optional[str]
    size: Optional[int]

class ScheduledSearchType(BaseModel):
    id: str
    episode_id: int
    instance_id: int
    scheduled_time: datetime
    status: str
    priority: int

class SonarrInstanceType(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    status: InstanceStatus
    last_checked: Optional[datetime]
    error_message: Optional[str]
    upcoming_episodes: List[EpisodeType] = []
    search_history: List[SearchRecordType] = []

class ConnectionTestResult(BaseModel):
    status: str
    version: Optional[str]
    appName: Optional[str]
    isProduction: Optional[bool]
    error: Optional[str]

class SearchRecordType(BaseModel):
    job_id: str
    instance_id: int
    episode_id: int
    priority: int
    created_at: datetime
    status: str
    retry_count: int
    last_attempt: Optional[datetime]
    error: Optional[str]

class SearchStatusType(BaseModel):
    queue_size: int
    processing_size: int
    max_concurrent_searches: int
    rate_limit_window: int
    max_searches_per_window: int

class Query:
    async def resolve_sonarr_instances(self, info) -> List[SonarrInstanceType]:
        db = next(get_db())
        try:
            instances = db.query(SonarrInstance).all()
            result = []
            for instance in instances:
                cache_manager = CacheManager("redis://redis:7369/0")
                sonarr_service = SonarrService(instance, cache_manager)
                queue_service = QueueService(cache_manager)
                
                # Get upcoming episodes
                series = await sonarr_service.get_series()
                upcoming_episodes = []
                for series_item in series:
                    episodes = await sonarr_service.get_episodes(series_item['id'])
                    for episode in episodes:
                        if episode.get('airDate') and datetime.fromisoformat(episode['airDate']) > datetime.utcnow():
                            upcoming_episodes.append(EpisodeType(
                                id=episode['id'],
                                series_id=episode['seriesId'],
                                season_number=episode['seasonNumber'],
                                episode_number=episode['episodeNumber'],
                                title=episode['title'],
                                air_date=datetime.fromisoformat(episode['airDate']) if episode.get('airDate') else None,
                                monitored=episode['monitored'],
                                has_file=episode['hasFile'],
                                quality=episode.get('quality'),
                                size=episode.get('size')
                            ))
                
                # Get search history
                search_history = []
                processing_jobs = await queue_service.cache.redis.zrange(queue_service.processing_key, 0, -1)
                for job_data in processing_jobs:
                    job_dict = json.loads(job_data)
                    if job_dict["instance_id"] == instance.id:
                        search_history.append(SearchRecordType(**job_dict))
                
                result.append(SonarrInstanceType(
                    id=instance.id,
                    name=instance.name,
                    url=instance.url,
                    is_active=instance.is_active,
                    status=InstanceStatus(instance.status),
                    last_checked=instance.last_checked,
                    error_message=instance.error_message,
                    upcoming_episodes=upcoming_episodes,
                    search_history=search_history
                ))
            return result
        finally:
            db.close()

    async def resolve_upcoming_searches(self, info) -> List[ScheduledSearchType]:
        cache_manager = CacheManager("redis://redis:7369/0")
        queue_service = QueueService(cache_manager)
        
        # Get all jobs from the queue
        queue_jobs = await queue_service.cache.redis.zrange(queue_service.queue_key, 0, -1)
        scheduled_searches = []
        
        for job_data in queue_jobs:
            job_dict = json.loads(job_data)
            scheduled_searches.append(ScheduledSearchType(
                id=job_dict["job_id"],
                episode_id=job_dict["episode_id"],
                instance_id=job_dict["instance_id"],
                scheduled_time=datetime.fromisoformat(job_dict["created_at"]),
                status=job_dict["status"],
                priority=job_dict["priority"]
            ))
        
        return scheduled_searches

    async def resolve_search_status(self, info) -> SearchStatusType:
        cache_manager = CacheManager("redis://redis:7369/0")
        queue_service = QueueService(cache_manager)
        status = await queue_service.get_queue_status()
        return SearchStatusType(**status)

@strawberry.input
class SonarrInstanceInput:
    name: str
    url: str
    api_key: str

@strawberry.input
class ConnectionTestInput:
    url: str
    api_key: str

@strawberry.input
class ScheduleSearchInput:
    episode_id: int
    instance_id: int
    priority: int = 0
    delay: Optional[int] = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_sonarr_instance(self, info, input: SonarrInstanceInput) -> SonarrInstanceType:
        db = next(get_db())
        instance = SonarrInstance(
            name=input.name,
            url=input.url,
            api_key=input.api_key
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return SonarrInstanceType(
            id=instance.id,
            name=instance.name,
            url=instance.url,
            is_active=instance.is_active,
            status=InstanceStatus(instance.status),
            last_checked=instance.last_checked,
            error_message=instance.error_message
        )

    @strawberry.mutation
    async def delete_sonarr_instance(self, info, id: int) -> bool:
        db = next(get_db())
        instance = db.query(SonarrInstance).filter(SonarrInstance.id == id).first()
        if instance:
            db.delete(instance)
            db.commit()
            return True
        return False

    @strawberry.mutation
    async def test_connection(self, info, input: ConnectionTestInput) -> ConnectionTestResult:
        result = await test_sonarr_connection(input.url, input.api_key)
        return ConnectionTestResult(**result)

    @strawberry.mutation
    async def schedule_search(self, info, input: ScheduleSearchInput) -> ScheduledSearchType:
        cache_manager = CacheManager("redis://redis:7369/0")
        queue_service = QueueService(cache_manager)
        
        # Calculate scheduled time based on delay
        scheduled_time = datetime.utcnow()
        if input.delay:
            scheduled_time = scheduled_time + timedelta(minutes=input.delay)
        
        job_id = await queue_service.add_search(
            instance_id=input.instance_id,
            episode_id=input.episode_id,
            priority=input.priority
        )
        
        return ScheduledSearchType(
            id=job_id,
            episode_id=input.episode_id,
            instance_id=input.instance_id,
            scheduled_time=scheduled_time,
            status="pending",
            priority=input.priority
        )

    @strawberry.mutation
    async def retry_failed_search(self, info, job_id: str) -> SearchStatusType:
        cache_manager = CacheManager("redis://redis:7369/0")
        queue_service = QueueService(cache_manager)
        
        # Get the failed job
        processing_jobs = await queue_service.cache.redis.zrange(queue_service.processing_key, 0, -1)
        for job_data in processing_jobs:
            job_dict = json.loads(job_data)
            if job_dict["job_id"] == job_id and job_dict["status"] == "failed":
                job = SearchJob.from_dict(job_dict)
                # Reset the job status and add it back to the queue
                job.status = "pending"
                job.retry_count += 1
                job.last_attempt = None
                job.error = None
                await queue_service.add_search(
                    instance_id=job.instance_id,
                    episode_id=job.episode_id,
                    priority=job.priority
                )
                break
        
        # Return updated search status
        status = await queue_service.get_queue_status()
        return SearchStatusType(**status)

schema = """
enum InstanceStatus {
    ONLINE
    OFFLINE
    ERROR
    UNKNOWN
}

type Episode {
    id: Int!
    seriesId: Int!
    seasonNumber: Int!
    episodeNumber: Int!
    title: String!
    airDate: DateTime
    monitored: Boolean!
    hasFile: Boolean!
    quality: String
    size: Int
}

type ScheduledSearch {
    id: String!
    episodeId: Int!
    instanceId: Int!
    scheduledTime: DateTime!
    status: String!
    priority: Int!
}

type SonarrInstance {
    id: Int!
    name: String!
    url: String!
    isActive: Boolean!
    status: InstanceStatus!
    lastChecked: DateTime
    errorMessage: String
    upcomingEpisodes: [Episode!]!
    searchHistory: [SearchRecord!]!
}

type SearchRecord {
    jobId: String!
    instanceId: Int!
    episodeId: Int!
    priority: Int!
    createdAt: DateTime!
    status: String!
    retryCount: Int!
    lastAttempt: DateTime
    error: String
}

type SearchStatus {
    queueSize: Int!
    processingSize: Int!
    maxConcurrentSearches: Int!
    rateLimitWindow: Int!
    maxSearchesPerWindow: Int!
}

type ConnectionTestResult {
    status: String!
    version: String
    appName: String
    isProduction: Boolean
    error: String
}

type Query {
    sonarrInstances: [SonarrInstance!]!
    sonarrInstance(id: Int!): SonarrInstance
    upcomingSearches: [ScheduledSearch!]!
    searchStatus: SearchStatus!
}

type Mutation {
    createSonarrInstance(input: SonarrInstanceInput!): SonarrInstance!
    deleteSonarrInstance(id: Int!): Boolean!
    testConnection(input: ConnectionTestInput!): ConnectionTestResult!
    scheduleSearch(input: ScheduleSearchInput!): ScheduledSearch!
    retryFailedSearch(jobId: String!): SearchStatus!
}

input SonarrInstanceInput {
    name: String!
    url: String!
    apiKey: String!
}

input ConnectionTestInput {
    url: String!
    apiKey: String!
}

input ScheduleSearchInput {
    episodeId: Int!
    instanceId: Int!
    priority: Int
    delay: Int
}
"""

graphql_app = GraphQLRouter(schema, context_getter=lambda: {"db": next(get_db())}) 