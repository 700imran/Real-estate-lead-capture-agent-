from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import track, leads, auth, agent, ws

app = FastAPI(title="Agentic Revenue Engine API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(track.router, prefix="/api/v1", tags=["tracking"])
app.include_router(leads.router, prefix="/api/v1", tags=["crm"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(agent.router, prefix="/api/v1", tags=["ai-agent"])
app.include_router(ws.router, prefix="/api/v1", tags=["realtime"])


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "env": settings.env}


@app.on_event("startup")
def on_startup():
    # Dev convenience only. In staging/production, manage schema changes
    # with Alembic migrations instead of create_all — see README.
    if settings.env == "development":
        Base.metadata.create_all(bind=engine)
