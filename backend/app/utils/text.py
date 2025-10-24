from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np

TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_]+")


@dataclass
class TextVocabulary:
    token_to_id: Dict[str, int]

    @classmethod
    def load(cls, path: Path) -> "TextVocabulary":
        if not path.exists():
            return cls(token_to_id={})
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(token_to_id={key: int(value) for key, value in data.items()})

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.token_to_id, fh, indent=2)

    def tokenize(self, text: str) -> List[str]:
        return [token.lower() for token in TOKEN_REGEX.findall(text)]

    def encode(self, text: str) -> np.ndarray:
        tokens = self.tokenize(text)
        vector = np.zeros(len(self.token_to_id) or 1, dtype=np.float32)
        if not tokens:
            return vector
        for token in tokens:
            if token not in self.token_to_id:
                self.token_to_id[token] = len(self.token_to_id)
            idx = self.token_to_id[token]
            if idx >= len(vector):
                vector = np.pad(vector, (0, idx - len(vector) + 1))
            vector[idx] += 1.0
        if vector.sum() > 0:
            vector /= vector.sum()
        return vector

    def ensure_tokens(self, texts: Iterable[str]) -> None:
        for text in texts:
            for token in self.tokenize(text):
                if token not in self.token_to_id:
                    self.token_to_id[token] = len(self.token_to_id)
