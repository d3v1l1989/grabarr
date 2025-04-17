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
import strawberry
from fastapi import Depends
import os

from ..core.auth import get_current_user, verify_password, authenticate_user, login as auth_login
from ..core.session import create_session, delete_session
from ..database import get_db
from ..models.user import User

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
class LoginResponse:
    message: str

@strawberry.type
class LogoutResponse:
    message: str

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

    @strawberry.field
    async def me(self, info) -> Optional[str]:
        user = await get_current_user()
        return user

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
    async def login(
        self,
        info,
        username: str,
        password: str,
    ) -> LoginResponse:
        try:
            session_id = await auth_login(username, password)
            response = info.context["response"]
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=True,
                samesite="lax"
            )
            return LoginResponse(message="Login successful")
        except Exception as e:
            raise Exception("Invalid username or password")

    @strawberry.mutation
    async def logout(self, info) -> LogoutResponse:
        response = info.context["response"]
        response.delete_cookie("session_id")
        return LogoutResponse(message="Logout successful")

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema) 