import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import settings


def _load_metadata() -> Dict[str, dict]:
    if not settings.metadata_file.exists():
        return {}
    with settings.metadata_file.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_metadata(metadata: Dict[str, dict]) -> None:
    settings.metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with settings.metadata_file.open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


@dataclass
class CropRegion:
    min: Tuple[int, int, int] = (0, 0, 0)
    max: Optional[Tuple[int, int, int]] = None


@dataclass
class DatasetEntry:
    id: str
    filename: str
    original_name: str
    size: Tuple[int, int, int]
    format: str
    tags: List[str] = field(default_factory=list)
    description: str = ""
    crop_region: CropRegion = field(default_factory=CropRegion)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_name": self.original_name,
            "size": self.size,
            "format": self.format,
            "tags": self.tags,
            "description": self.description,
            "crop_region": {
                "min": list(self.crop_region.min),
                "max": list(self.crop_region.max) if self.crop_region.max else None,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DatasetEntry":
        crop = data.get("crop_region") or {}
        region = CropRegion(
            min=tuple(crop.get("min", (0, 0, 0))),
            max=tuple(crop["max"]) if crop.get("max") else None,
        )
        return cls(
            id=data["id"],
            filename=data["filename"],
            original_name=data.get("original_name", data["filename"]),
            size=tuple(data["size"]),
            format=data["format"],
            tags=data.get("tags", []),
            description=data.get("description", ""),
            crop_region=region,
        )


class DatasetStore:
    def __init__(self) -> None:
        self._metadata = _load_metadata()

    def list_entries(self) -> List[DatasetEntry]:
        return [DatasetEntry.from_dict(item) for item in self._metadata.values()]

    def get(self, entry_id: str) -> Optional[DatasetEntry]:
        if entry_id not in self._metadata:
            return None
        return DatasetEntry.from_dict(self._metadata[entry_id])

    def add(
        self,
        *,
        original_name: str,
        stored_name: str,
        size: Tuple[int, int, int],
        file_format: str,
    ) -> DatasetEntry:
        entry_id = uuid.uuid4().hex
        entry = DatasetEntry(
            id=entry_id,
            filename=stored_name,
            original_name=original_name,
            size=size,
            format=file_format,
        )
        self._metadata[entry_id] = entry.to_dict()
        _save_metadata(self._metadata)
        return entry

    def update(self, entry_id: str, **fields) -> Optional[DatasetEntry]:
        entry = self.get(entry_id)
        if not entry:
            return None
        for key, value in fields.items():
            if key == "tags" and value is not None:
                entry.tags = list(value)
            elif key == "description" and value is not None:
                entry.description = value
            elif key == "crop_region" and value is not None:
                region = value
                entry.crop_region = CropRegion(
                    min=tuple(region.get("min", entry.crop_region.min)),
                    max=tuple(region.get("max")) if region.get("max") else None,
                )
        self._metadata[entry_id] = entry.to_dict()
        _save_metadata(self._metadata)
        return entry

    def remove(self, entry_id: str) -> None:
        entry = self._metadata.pop(entry_id, None)
        if entry:
            _save_metadata(self._metadata)
            stored_path = settings.dataset_dir / entry["filename"]
            if stored_path.exists():
                stored_path.unlink()


def get_dataset_store() -> DatasetStore:
    return DatasetStore()
