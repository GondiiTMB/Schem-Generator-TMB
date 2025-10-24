from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class DatasetUploadResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    size: Tuple[int, int, int]
    format: str


class DatasetEntryResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    size: Tuple[int, int, int]
    format: str
    tags: List[str]
    description: str
    crop_region: dict


class DatasetUpdateRequest(BaseModel):
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    crop_region: Optional[dict] = Field(
        default=None,
        description="{min: [x,y,z], max: [x,y,z]}"
    )


class TrainingRequest(BaseModel):
    epochs: int = 10
    batch_size: int = 2
    learning_rate: float = 1e-3
    target_size: Tuple[int, int, int] = (32, 32, 32)


class TrainingStatusResponse(BaseModel):
    active: bool
    current_epoch: int
    total_epochs: int
    loss: float


class GenerationRequest(BaseModel):
    prompt: str
    output_format: str = Field(regex="^(schem|schematic|litematic)$")
    target_size: Tuple[int, int, int] = (32, 32, 32)


class GenerationResponse(BaseModel):
    file: str
    viewer_data: dict


class ConversionRequest(BaseModel):
    source_path: str
    output_format: str = Field(regex="^(schem|schematic|litematic)$")
