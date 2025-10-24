from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from sqlalchemy import select

from ..config import get_settings
from ..database import session_scope
from ..models import SchematicEntry
from ..schemas import DatasetItem
from ..utils.schematic import ensure_supported

settings = get_settings()


class DatasetService:
    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or settings.dataset_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def add_file(self, uploaded_path: Path, original_name: str, *, tags: list[str] | None = None,
                 description: str | None = None) -> DatasetItem:
        tags = tags or []
        file_ext = uploaded_path.suffix.lstrip('.')
        fmt = ensure_supported(file_ext)

        target_path = self.storage_dir / uploaded_path.name
        if target_path.exists():
            target_path = self.storage_dir / f"{uploaded_path.stem}_{uploaded_path.stat().st_mtime_ns}.{fmt}"
        shutil.move(str(uploaded_path), target_path)

        with session_scope() as session:
            entry = SchematicEntry(
                filename=target_path.name,
                original_name=original_name,
                format=fmt,
                tags=tags,
                description=description,
                metadata={}
            )
            session.add(entry)
            session.flush()
            dataset_item = DatasetItem(
                id=entry.id,
                original_name=entry.original_name,
                filename=entry.filename,
                format=fmt,
                tags=entry.tags,
                description=entry.description,
                metadata=entry.metadata,
                created_at=entry.created_at,
            )
        return dataset_item

    def list_items(self) -> list[DatasetItem]:
        with session_scope() as session:
            results = session.scalars(select(SchematicEntry).order_by(SchematicEntry.created_at.desc())).all()
            return [DatasetItem(
                id=item.id,
                original_name=item.original_name,
                filename=item.filename,
                format=item.format,
                tags=item.tags,
                description=item.description,
                metadata=item.metadata,
                created_at=item.created_at,
            ) for item in results]

    def resolve_path(self, filename: str) -> Path:
        path = self.storage_dir / filename
        if not path.exists():
            raise FileNotFoundError(filename)
        return path

    def delete(self, item_id: int) -> None:
        with session_scope() as session:
            entry = session.get(SchematicEntry, item_id)
            if not entry:
                return
            path = self.storage_dir / entry.filename
            if path.exists():
                path.unlink()
            session.delete(entry)
