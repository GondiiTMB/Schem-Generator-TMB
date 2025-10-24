from __future__ import annotations

import io
import random
from pathlib import Path
from typing import Iterable

import nbtlib
from nbtlib import Compound, Short

from ..config import get_settings

SUPPORTED_FORMATS = {"schem", "schematic", "litematic"}


class UnsupportedFormatError(ValueError):
    pass


def ensure_supported(format_name: str) -> str:
    lowered = format_name.lower()
    if lowered not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(f"Format '{format_name}' is not supported.")
    return lowered


def create_placeholder_structure(size: int = 5) -> nbtlib.File:
    """Create a trivial NBT structure that resembles a valid schematic."""

    block_ids = [random.randint(1, 98) for _ in range(size ** 3)]
    schematic = Compound({
        "Width": Short(size),
        "Height": Short(size),
        "Length": Short(size),
        "Materials": nbtlib.String("Alpha"),
        "Blocks": nbtlib.ByteArray(block_ids),
        "Data": nbtlib.ByteArray([0] * len(block_ids)),
    })
    return nbtlib.File({"Schematic": schematic})


def write_schematic(file: nbtlib.File, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file.save(path)


def convert_between_formats(source_path: Path, destination: Path) -> None:
    src_format = ensure_supported(source_path.suffix.lstrip('.'))
    dst_format = ensure_supported(destination.suffix.lstrip('.'))

    if src_format == dst_format:
        destination.write_bytes(source_path.read_bytes())
        return

    # For now we only copy the binary content. A more robust conversion should
    # be implemented by integrating a dedicated library such as amulet-nbt.
    destination.write_bytes(source_path.read_bytes())


def available_formats() -> Iterable[str]:
    return sorted(SUPPORTED_FORMATS)


def renderable_payload(path: Path) -> bytes:
    """Return the payload for the viewer. For now this is the raw file."""
    return path.read_bytes()
