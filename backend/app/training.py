from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import torch
from torch import optim
from torch.utils.data import DataLoader, Dataset

from .config import settings
from .dataset import DatasetEntry, get_dataset_store
from .models.voxvae import ModelBundle, TextConditionedVAE
from .schematic import load_schematic, save_schematic, SchematicData
from .utils.text import TextVocabulary
from .utils.voxel import BlockVocabulary, resize_voxel_tensor, tensor_to_indices, voxel_to_tensor


@dataclass
class TrainingConfig:
    epochs: int = 10
    batch_size: int = 2
    learning_rate: float = 1e-3
    target_shape: Tuple[int, int, int] = (32, 32, 32)
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class SchematicDataset(Dataset):
    def __init__(
        self,
        entries: List[DatasetEntry],
        *,
        dataset_dir: Path,
        block_vocab: BlockVocabulary,
        text_vocab: TextVocabulary,
        target_shape: Tuple[int, int, int],
    ) -> None:
        self.entries = entries
        self.dataset_dir = dataset_dir
        self.block_vocab = block_vocab
        self.text_vocab = text_vocab
        self.target_shape = target_shape
        self.cached: List[Tuple[torch.Tensor, torch.Tensor]] = []
        self._load_entries()

    def _load_entries(self) -> None:
        for entry in self.entries:
            path = self.dataset_dir / entry.filename
            schem = load_schematic(path)
            blocks = schem.blocks
            palette_map = np.array(
                [block_vocab.token_to_id[schem.palette[local_idx]] for local_idx in range(len(schem.palette))],
                dtype=np.int64,
            )
            remapped = np.take(palette_map, blocks)
            if entry.crop_region.max:
                min_x, min_y, min_z = entry.crop_region.min
                max_x, max_y, max_z = entry.crop_region.max
                remapped = remapped[min_y:max_y, min_z:max_z, min_x:max_x]
            vocab_size = len(self.block_vocab)
            tensor = voxel_to_tensor(remapped, vocab_size=vocab_size)
            tensor = resize_voxel_tensor(tensor, self.target_shape)
            text_input = " ".join(entry.tags + [entry.description])
            text_vec = torch.from_numpy(self.text_vocab.encode(text_input)).float()
            if text_vec.numel() == 0:
                text_vec = torch.zeros(len(self.text_vocab.token_to_id) or 1)
            self.cached.append((tensor, text_vec))

    def __len__(self) -> int:  # type: ignore[override]
        return len(self.cached)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:  # type: ignore[override]
        return self.cached[idx]


class TrainingState:
    def __init__(self) -> None:
        self.active = False
        self.current_epoch = 0
        self.total_epochs = 0
        self.loss = 0.0
        self.lock = threading.Lock()

    def to_dict(self) -> Dict[str, float]:
        with self.lock:
            return {
                "active": self.active,
                "current_epoch": self.current_epoch,
                "total_epochs": self.total_epochs,
                "loss": self.loss,
            }

    def update(self, epoch: int, total_epochs: int, loss: float, active: bool) -> None:
        with self.lock:
            self.current_epoch = epoch
            self.total_epochs = total_epochs
            self.loss = loss
            self.active = active
            self._save()

    def _save(self) -> None:
        settings.training_state_file.parent.mkdir(parents=True, exist_ok=True)
        with settings.training_state_file.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)


training_state = TrainingState()
training_thread: Optional[threading.Thread] = None


def _kl_divergence(mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
    return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())


def _prepare_vocabularies(entries: Iterable[DatasetEntry]) -> Tuple[BlockVocabulary, TextVocabulary]:
    block_vocab = BlockVocabulary.load(settings.vocab_file)
    text_vocab = TextVocabulary.load(settings.text_vocab_file)
    for entry in entries:
        path = settings.dataset_dir / entry.filename
        schem = load_schematic(path)
        block_vocab.ensure_tokens([schem.palette[idx] for idx in np.unique(schem.blocks)])
        text_vocab.ensure_tokens([" ".join(entry.tags + [entry.description])])
    block_vocab.save(settings.vocab_file)
    text_vocab.save(settings.text_vocab_file)
    return block_vocab, text_vocab


def start_training(config: TrainingConfig) -> None:
    global training_thread
    if training_state.active:
        raise RuntimeError("Training already in progress")

    store = get_dataset_store()
    entries = store.list_entries()
    if not entries:
        raise RuntimeError("Dataset is empty")

    block_vocab, text_vocab = _prepare_vocabularies(entries)

    if len(block_vocab) == 0:
        raise RuntimeError("Block vocabulary is empty; add schematics before training")

    dataset = SchematicDataset(
        entries,
        dataset_dir=settings.dataset_dir,
        block_vocab=block_vocab,
        text_vocab=text_vocab,
        target_shape=config.target_shape,
    )
    dataloader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True)

    model = TextConditionedVAE(
        vocab_size=len(block_vocab),
        text_dim=len(text_vocab.token_to_id) or 1,
    ).to(config.device)
    optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = torch.nn.CrossEntropyLoss()

    def train_loop() -> None:
        training_state.update(0, config.epochs, 0.0, True)
        for epoch in range(1, config.epochs + 1):
            epoch_loss = 0.0
            for voxels, text_vec in dataloader:
                voxels = voxels.to(config.device)
                text_vec = text_vec.to(config.device)
                optimizer.zero_grad()
                outputs, mu, logvar = model(voxels, text_vec)
                targets = voxels.argmax(dim=1)
                recon_loss = criterion(outputs, targets)
                kl_loss = _kl_divergence(mu, logvar) / targets.numel()
                loss = recon_loss + 0.001 * kl_loss
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            avg_loss = epoch_loss / max(1, len(dataloader))
            training_state.update(epoch, config.epochs, avg_loss, True)
        bundle = ModelBundle(model=model, vocab_size=len(block_vocab), text_dim=len(text_vocab.token_to_id) or 1)
        bundle.save(settings.model_dir / "model.pt")
        block_vocab.save(settings.vocab_file)
        text_vocab.save(settings.text_vocab_file)
        training_state.update(config.epochs, config.epochs, avg_loss, False)

    training_thread = threading.Thread(target=train_loop, daemon=True)
    training_thread.start()


def generate_structure(prompt: str, target_format: str, target_shape: Tuple[int, int, int]) -> Path:
    model_path = settings.model_dir / "model.pt"
    if not model_path.exists():
        raise RuntimeError("No trained model available")
    bundle = ModelBundle.load(model_path)
    block_vocab = BlockVocabulary.load(settings.vocab_file)
    text_vocab = TextVocabulary.load(settings.text_vocab_file)
    model = bundle.model
    model.eval()
    text_vector = text_vocab.encode(prompt)
    text_vocab.save(settings.text_vocab_file)
    text_tensor = torch.from_numpy(text_vector).float().unsqueeze(0)
    if text_tensor.size(1) != bundle.text_dim:
        padding = bundle.text_dim - text_tensor.size(1)
        if padding > 0:
            text_tensor = torch.nn.functional.pad(text_tensor, (0, padding))
        else:
            text_tensor = text_tensor[:, : bundle.text_dim]
    with torch.no_grad():
        mu = torch.zeros((1, model.fc_mu.out_features))
        logvar = torch.zeros_like(mu)
        z = model.reparameterize(mu, logvar)
        output = model.decode(z, text_tensor)
        logits = output.squeeze(0)
        resized = resize_voxel_tensor(logits, target_shape)
        indices = tensor_to_indices(resized)
    # Map indices back to palette entries
    inverse_palette = {index: block for block, index in block_vocab.token_to_id.items()}
    palette_list = [inverse_palette[i] for i in sorted(inverse_palette.keys())]
    size = (target_shape[2], target_shape[0], target_shape[1])  # width, height, length
    data = SchematicData(size=size, palette=palette_list, blocks=indices)
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.generated_dir / f"generated_{uuid.uuid4().hex}.{target_format}"
    save_schematic(data, output_path, fmt=target_format)
    return output_path


def get_training_state() -> Dict[str, float]:
    return training_state.to_dict()
