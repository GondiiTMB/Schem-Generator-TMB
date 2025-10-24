import json
from pathlib import Path
from typing import Dict, List

import numpy as np


def load_palette(path: Path) -> Dict[str, int]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {key: int(value) for key, value in data.items()}


def save_palette(palette: Dict[str, int], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump({key: int(value) for key, value in palette.items()}, fh, indent=2)


def build_palette(schematics: List[np.ndarray], existing: Dict[str, int]) -> Dict[str, int]:
    palette = dict(existing)
    next_index = max(palette.values(), default=-1) + 1
    for blocks in schematics:
        unique_values = np.unique(blocks)
        for value in unique_values:
            if isinstance(value, str) and value not in palette:
                palette[value] = next_index
                next_index += 1
    return palette
