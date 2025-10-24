from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import dataset, generation, training

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Minecraft Structure Generator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generation.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")
app.include_router(training.router, prefix="/api")


@app.get("/api/health")
def healthcheck() -> dict:
    return {"status": "ok"}
