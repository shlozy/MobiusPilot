from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai import router as ai_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth import router as auth_router
from app.api.routes.activity import router as activity_router
from app.api.routes.health import router as health_router
from app.api.routes.members import router as members_router
from app.api.routes.messages import router as messages_router
from app.api.routes.organizations import router as organizations_router
from app.api.routes.projects import router as projects_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.workspaces import router as workspaces_router
from app.core.config import get_settings
from app.db.database import SessionLocal, create_db_and_tables
from app.db.seed import seed_demo_data

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    create_db_and_tables()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(organizations_router)
app.include_router(projects_router)
app.include_router(members_router)
app.include_router(tasks_router)
app.include_router(messages_router)
app.include_router(activity_router)
app.include_router(ai_router)
app.include_router(analytics_router)


@app.get("/")
def root() -> dict:
    return {"app": settings.app_name, "status": "online"}
