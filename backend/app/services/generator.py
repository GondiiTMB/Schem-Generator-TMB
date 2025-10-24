from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from ..config import get_settings
from ..schemas import SupportedFormat
from ..utils.schematic import create_placeholder_structure, ensure_supported, write_schematic

settings = get_settings()


class StructureGenerator:
    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or settings.generated_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, export_format: SupportedFormat) -> Path:
        ensure_supported(export_format)
        timestamp = int(time.time() * 1000)
        filename = f"generated_{timestamp}.{export_format}"
        output_path = self.output_dir / filename

        schematic_file = create_placeholder_structure()
        write_schematic(schematic_file, output_path)
        return output_path
