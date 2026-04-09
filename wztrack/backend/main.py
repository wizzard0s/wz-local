from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, users, projects, issues, requirements, wiki, testcases, traceability


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="WZTrack API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(issues.router, prefix="/api/v1/issues", tags=["issues"])
app.include_router(requirements.router, prefix="/api/v1/requirements", tags=["requirements"])
app.include_router(wiki.router, prefix="/api/v1/wiki", tags=["wiki"])
app.include_router(testcases.router, prefix="/api/v1/testcases", tags=["testcases"])
app.include_router(traceability.router, prefix="/api/v1/traceability", tags=["traceability"])


@app.get("/api/v1/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}
