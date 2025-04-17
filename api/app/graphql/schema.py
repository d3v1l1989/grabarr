from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sonarr_instance import SonarrInstance
from app.services.sonarr_instance import test_sonarr_connection
from app.services.queue_service import QueueService

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

@strawberry.type
class SonarrInstanceType:
    id: int
    name: str
    url: str
    is_active: bool
    status: InstanceStatus
    last_checked: Optional[datetime]
    error_message: Optional[str]

@strawberry.input
class SonarrInstanceInput:
    name: str
    url: str
    api_key: str

@strawberry.type
class ConnectionTestResult:
    success: bool
    message: str

@strawberry.input
class ConnectionTestInput:
    url: str
    api_key: str

@strawberry.type
class Query:
    @strawberry.field
    async def sonarr_instances(self, info) -> List[SonarrInstanceType]:
        db = next(get_db())
        instances = db.query(SonarrInstance).all()
        return [
            SonarrInstanceType(
                id=instance.id,
                name=instance.name,
                url=instance.url,
                is_active=instance.is_active,
                status=InstanceStatus(instance.status),
                last_checked=instance.last_checked,
                error_message=instance.error_message
            )
            for instance in instances
        ]

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

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=lambda: {"db": next(get_db())}) 