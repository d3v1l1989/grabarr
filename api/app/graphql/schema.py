from typing import List, Optional, Dict
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
from app.services.smart_search import SmartSearchService
from fastapi import HTTPException
import json
import uuid

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

@strawberry.type
class SearchPatternType:
    series_id: int
    season_number: int
    episode_number: int
    successful_delays: Dict[str, int]
    failed_delays: Dict[str, int]
    last_successful_delay: Optional[int]
    last_air_date: Optional[datetime]

@strawberry.type
class SmartSearchStats:
    total_patterns: int
    average_success_rate: float
    most_common_delay: int
    patterns: List[SearchPatternType]

class JobStatusType(graphene.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEPENDENCY_FAILED = "dependency_failed"

class JobPriorityType(graphene.Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

class JobDependencyType(graphene.ObjectType):
    job_id = graphene.String(required=True)
    required_status = graphene.Field(JobStatusType, required=True)

class RetryPolicyType(graphene.ObjectType):
    max_retries = graphene.Int(required=True)
    retry_delay = graphene.Int(required=True)
    backoff_factor = graphene.Int(required=True)

class AdvancedSearchJobType(graphene.ObjectType):
    job_id = graphene.String(required=True)
    instance_id = graphene.Int(required=True)
    episode_id = graphene.Int(required=True)
    series_id = graphene.Int(required=True)
    season_number = graphene.Int(required=True)
    episode_number = graphene.Int(required=True)
    priority = graphene.Field(JobPriorityType, required=True)
    delay = graphene.Int(required=True)
    dependencies = graphene.List(JobDependencyType)
    retry_policy = graphene.Field(RetryPolicyType)
    created_at = graphene.DateTime(required=True)
    status = graphene.Field(JobStatusType, required=True)
    retry_count = graphene.Int(required=True)
    last_attempt = graphene.DateTime()
    error = graphene.String()
    dependent_jobs = graphene.List(graphene.String)

class AdvancedQueueStatsType(graphene.ObjectType):
    queue_size = graphene.Int(required=True)
    processing_size = graphene.Int(required=True)
    max_concurrent_searches = graphene.Int(required=True)
    rate_limit_window = graphene.Int(required=True)
    max_searches_per_window = graphene.Int(required=True)
    jobs_by_status = graphene.JSONString(required=True)
    jobs_by_priority = graphene.JSONString(required=True)

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

    @strawberry.field
    async def smart_search_stats(self, info) -> SmartSearchStats:
        cache_manager = CacheManager("redis://redis:7369/0")
        smart_search = SmartSearchService(cache_manager)
        patterns = await smart_search._load_patterns()
        
        total_patterns = len(patterns)
        total_success_rate = 0.0
        delay_counts = {}
        
        pattern_types = []
        for pattern in patterns.values():
            successes = sum(pattern.successful_delays.values())
            failures = sum(pattern.failed_delays.values())
            total = successes + failures
            success_rate = successes / total if total > 0 else 0
            total_success_rate += success_rate
            
            for delay in pattern.successful_delays:
                delay_counts[delay] = delay_counts.get(delay, 0) + pattern.successful_delays[delay]
            
            pattern_types.append(SearchPatternType(
                series_id=pattern.series_id,
                season_number=pattern.season_number,
                episode_number=pattern.episode_number,
                successful_delays=pattern.successful_delays,
                failed_delays=pattern.failed_delays,
                last_successful_delay=pattern.last_successful_delay,
                last_air_date=pattern.last_air_date
            ))
        
        average_success_rate = total_success_rate / total_patterns if total_patterns > 0 else 0
        most_common_delay = max(delay_counts.items(), key=lambda x: x[1])[0] if delay_counts else 0
        
        return SmartSearchStats(
            total_patterns=total_patterns,
            average_success_rate=average_success_rate,
            most_common_delay=most_common_delay,
            patterns=pattern_types
        )

    advanced_queue_stats = graphene.Field(AdvancedQueueStatsType)

    async def resolve_advanced_queue_stats(self, info):
        queue_service = info.context["queue_service"]
        stats = await queue_service.get_queue_status()
        
        # Get additional statistics
        jobs = await queue_service.cache.redis.hgetall(queue_service.jobs_key)
        jobs_by_status = {}
        jobs_by_priority = {}
        
        for job_data in jobs.values():
            job = json.loads(job_data)
            status = job["status"]
            priority = job["priority"]
            
            jobs_by_status[status] = jobs_by_status.get(status, 0) + 1
            jobs_by_priority[priority] = jobs_by_priority.get(priority, 0) + 1
        
        return AdvancedQueueStatsType(
            queue_size=stats["queue_size"],
            processing_size=stats["processing_size"],
            max_concurrent_searches=stats["max_concurrent_searches"],
            rate_limit_window=stats["rate_limit_window"],
            max_searches_per_window=stats["max_searches_per_window"],
            jobs_by_status=json.dumps(jobs_by_status),
            jobs_by_priority=json.dumps(jobs_by_priority)
        )

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
        
        # Get series and episode info
        db = next(get_db())
        try:
            instance = db.query(SonarrInstance).filter(SonarrInstance.id == input.instance_id).first()
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")
            
            sonarr_service = SonarrService(instance, cache_manager)
            episode = await sonarr_service.get_episode(input.episode_id)
            if not episode:
                raise HTTPException(status_code=404, detail="Episode not found")
            
            job_id = await queue_service.add_search(
                instance_id=input.instance_id,
                episode_id=input.episode_id,
                series_id=episode['seriesId'],
                season_number=episode['seasonNumber'],
                episode_number=episode['episodeNumber'],
                priority=input.priority
            )
            
            return ScheduledSearchType(
                id=job_id,
                episode_id=input.episode_id,
                instance_id=input.instance_id,
                scheduled_time=datetime.utcnow(),
                status="queued",
                priority=input.priority
            )
        finally:
            db.close()

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

    @strawberry.mutation
    async def schedule_advanced_search(self, info, input):
        queue_service = info.context["queue_service"]
        db = info.context["db"]
        
        # Get episode information
        episode = await db.fetch_one(
            "SELECT * FROM episodes WHERE id = $1",
            input.episode_id
        )
        if not episode:
            raise Exception("Episode not found")
        
        # Create job dependencies
        dependencies = []
        if input.dependencies:
            for dep_id in input.dependencies:
                dependencies.append(JobDependency(dep_id))
        
        # Create job
        job = AdvancedSearchJob(
            job_id=str(uuid.uuid4()),
            instance_id=input.instance_id,
            episode_id=input.episode_id,
            series_id=episode["series_id"],
            season_number=episode["season_number"],
            episode_number=episode["episode_number"],
            priority=input.priority,
            dependencies=dependencies,
            retry_policy=input.retry_policy
        )
        
        # Add to queue
        await queue_service.add_job(job)
        return job

    @strawberry.mutation
    async def retry_job(self, info, job_id):
        queue_service = info.context["queue_service"]
        success = await queue_service.retry_job(job_id)
        if not success:
            raise Exception("Failed to retry job")
        return await queue_service._get_job(job_id)

    @strawberry.mutation
    async def cancel_job(self, info, job_id):
        queue_service = info.context["queue_service"]
        success = await queue_service.cancel_job(job_id)
        if not success:
            raise Exception("Failed to cancel job")
        return await queue_service._get_job(job_id)

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
    smartSearchStats: SmartSearchStats!
    advancedQueueStats: AdvancedQueueStatsType!
}

type Mutation {
    createSonarrInstance(input: SonarrInstanceInput!): SonarrInstance!
    deleteSonarrInstance(id: Int!): Boolean!
    testConnection(input: ConnectionTestInput!): ConnectionTestResult!
    scheduleSearch(input: ScheduleSearchInput!): ScheduledSearch!
    retryFailedSearch(jobId: String!): SearchStatus!
    scheduleAdvancedSearch(input: ScheduleAdvancedSearchInput!): AdvancedSearchJobType!
    retryJob(jobId: String!): AdvancedSearchJobType!
    cancelJob(jobId: String!): AdvancedSearchJobType!
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

input ScheduleAdvancedSearchInput {
    episodeId: Int!
    instanceId: Int!
    priority: JobPriorityType
    dependencies: [String!]
    retryPolicy: RetryPolicyType
}
"""

graphql_app = GraphQLRouter(schema, context_getter=lambda: {"db": next(get_db())}) 