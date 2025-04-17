from fastapi import APIRouter
from strawberry.fastapi import GraphQLRouter
from .schema import schema, Query, Mutation
from app.core.database import get_db

graphql_router = APIRouter()

graphql_app = GraphQLRouter(
    schema=schema,
    context_getter=lambda: {"db": next(get_db())}
)

graphql_router.include_router(graphql_app, prefix="/graphql") 