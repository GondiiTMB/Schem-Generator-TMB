from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    dataset_dir: Path = Field(default=Path("data/dataset"))
    generated_dir: Path = Field(default=Path("data/generated"))
    model_dir: Path = Field(default=Path("data/models"))
    database_url: str = Field(default="sqlite:///data/metadata.db")
    allow_cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    enable_training_features: bool = Field(default=True)
    default_export_format: str = Field(default="schem")

    class Config:
        env_prefix = "SCHEM_GEN_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.dataset_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    return settings
