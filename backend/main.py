from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.database.db import init_db
from backend.routes.health import router as health_router
from backend.routes.routes import router as routes_router
from backend.routes.emissions import router as emissions_router
from backend.routes.road_damage import router as road_damage_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database on startup
    init_db()
    print(f"[{settings.APP_NAME}] Database initialized successfully.")
    yield
    print(f"[{settings.APP_NAME}] Server shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="College-level Machine Learning Web Application for Eco-Friendly Route Optimization",
    lifespan=lifespan,
)

# CORS configuration allowing React + Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount health routes at root level and API versioned level
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(routes_router, prefix="/api/v1")
app.include_router(emissions_router, prefix="/api/v1")
app.include_router(road_damage_router, prefix="/api/v1/road-damage", tags=["Road Damage Detection"])


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/health"
    }
