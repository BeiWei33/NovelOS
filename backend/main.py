"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import novels, chapters, scenes, resources, skills, pipeline, samples, workflow
from api.routes import errors as errors_router
from api.routes import auto_fix
from core.config import settings
from skills.providers import init_providers
from skills.profile_registry import init_profiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — initialize LLM providers and profiles
    init_providers()
    init_profiles()
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
    app.include_router(samples.router)
    app.include_router(workflow.router)
    app.include_router(errors_router.router)
    app.include_router(auto_fix.router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": settings.APP_NAME}

    return app


app = create_app()