"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import novels, chapters, scenes, resources, skills, pipeline
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(novels.router)
    app.include_router(chapters.router)
    app.include_router(scenes.router)
    app.include_router(resources.router)
    app.include_router(skills.router)
    app.include_router(pipeline.router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": settings.APP_NAME}

    return app


app = create_app()