from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import connections, databases, query, upload
from config.settings import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for the Agentic SQL Copilot.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(databases.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(connections.router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
