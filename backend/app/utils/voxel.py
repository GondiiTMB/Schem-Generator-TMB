from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import torch
import torch.nn.functional as F


@dataclass
class BlockVocabulary:
    token_to_id: Dict[str, int]

    @classmethod
    def load(cls, path: Path) -> "BlockVocabulary":
        if not path.exists():
            return cls(token_to_id={})
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(token_to_id={key: int(value) for key, value in data.items()})

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.token_to_id, fh, indent=2)

    def ensure_tokens(self, tokens: Iterable[str]) -> None:
        next_index = max(self.token_to_id.values(), default=-1) + 1
        for token in tokens:
            if token not in self.token_to_id:
                self.token_to_id[token] = next_index
                next_index += 1

    def encode(self, tokens: Sequence[str]) -> np.ndarray:
        self.ensure_tokens(tokens)
        return np.array([self.token_to_id[token] for token in tokens], dtype=np.int64)

    def __len__(self) -> int:
        return len(self.token_to_id)


def voxel_to_tensor(block_indices: np.ndarray, vocab_size: int) -> torch.Tensor:
    """Convert palette indices to one-hot tensor."""
    array = torch.from_numpy(block_indices.astype("int64"))
    one_hot = F.one_hot(array, num_classes=vocab_size).float()
    return one_hot.permute(3, 0, 1, 2)  # C, Y, Z, X


def resize_voxel_tensor(tensor: torch.Tensor, target_shape: Tuple[int, int, int]) -> torch.Tensor:
    _, height, length, width = tensor.shape
    target_y, target_z, target_x = target_shape
    if (height, length, width) == target_shape:
        return tensor
    tensor = tensor.unsqueeze(0)
    resized = F.interpolate(
        tensor,
        size=(target_y, target_z, target_x),
        mode="trilinear",
        align_corners=False,
    )
    return resized.squeeze(0)


def tensor_to_indices(tensor: torch.Tensor) -> np.ndarray:
    indices = tensor.argmax(dim=0)
    return indices.cpu().numpy().astype("int64")
