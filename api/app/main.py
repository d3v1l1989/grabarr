from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, sonarr
from app.graphql.router import graphql_router

app = FastAPI(title="grabarr")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3456"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sonarr.router, prefix="/api/sonarr", tags=["sonarr"])
app.include_router(graphql_router)

@app.get("/")
async def root():
    return {"message": "grabarr API"} 