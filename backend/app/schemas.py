from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

SupportedFormat = Literal["schem", "schematic", "litematic"]


class DatasetItem(BaseModel):
    id: int
    original_name: str
    filename: str
    format: SupportedFormat
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class DatasetCreateRequest(BaseModel):
    tags: list[str] = Field(default_factory=list)
    description: str | None = None


class GenerateRequest(BaseModel):
    prompt: str
    format: SupportedFormat = Field(default="schem")


class GenerateResponse(BaseModel):
    filename: str
    format: SupportedFormat
    download_url: str


class TrainingConfig(BaseModel):
    epochs: int = 5
    batch_size: int = 4
    learning_rate: float = 1e-3
    dataset_path: Path | None = None


class TrainingRunResponse(BaseModel):
    run_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    metrics: dict = Field(default_factory=dict)


class TrainingStatusResponse(BaseModel):
    runs: list[TrainingRunResponse]
