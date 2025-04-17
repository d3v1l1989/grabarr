from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sonarr_instance import SonarrInstance
from app.services.sonarr_instance import test_sonarr_connection

class SonarrInstanceType(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    status: str
    last_checked: Optional[datetime]
    error_message: Optional[str]

class ConnectionTestResult(BaseModel):
    status: str
    version: Optional[str]
    appName: Optional[str]
    isProduction: Optional[bool]
    error: Optional[str]

class Query:
    async def resolve_sonarr_instances(self, info) -> List[SonarrInstanceType]:
        db = next(get_db())
        try:
            instances = db.query(SonarrInstance).all()
            return [SonarrInstanceType(
                id=instance.id,
                name=instance.name,
                url=instance.url,
                is_active=instance.is_active,
                status=instance.status,
                last_checked=instance.last_checked,
                error_message=instance.error_message
            ) for instance in instances]
        finally:
            db.close()

    async def resolve_sonarr_instance(self, info, id: int) -> Optional[SonarrInstanceType]:
        db = next(get_db())
        try:
            instance = db.query(SonarrInstance).filter(SonarrInstance.id == id).first()
            if instance:
                return SonarrInstanceType(
                    id=instance.id,
                    name=instance.name,
                    url=instance.url,
                    is_active=instance.is_active,
                    status=instance.status,
                    last_checked=instance.last_checked,
                    error_message=instance.error_message
                )
            return None
        finally:
            db.close()

@strawberry.input
class SonarrInstanceInput:
    name: str
    url: str
    api_key: str

@strawberry.input
class ConnectionTestInput:
    url: str
    api_key: str

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
            status=instance.status,
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

schema = """
type SonarrInstance {
    id: Int!
    name: String!
    url: String!
    isActive: Boolean!
    status: String!
    lastChecked: DateTime
    errorMessage: String
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
}

type Mutation {
    createSonarrInstance(input: SonarrInstanceInput!): SonarrInstance!
    deleteSonarrInstance(id: Int!): Boolean!
    testConnection(input: ConnectionTestInput!): ConnectionTestResult!
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
"""

graphql_app = GraphQLRouter(schema, context_getter=lambda: {"db": next(get_db())}) 