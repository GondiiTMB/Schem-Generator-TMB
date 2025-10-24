from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from ..config import get_settings
from ..database import session_scope
from ..models import TrainingRun
from ..schemas import TrainingConfig

settings = get_settings()


@dataclass
class TrainingProgress:
    current_epoch: int
    total_epochs: int
    loss: float


class TrainingService:
    def __init__(self, dataset_dir: Path | None = None) -> None:
        self.dataset_dir = dataset_dir or settings.dataset_dir
        self._lock = threading.Lock()
        self._current_run: Optional[int] = None

    def start_training(self, config: TrainingConfig) -> int:
        with self._lock:
            if self._current_run is not None:
                raise RuntimeError("Training already in progress")

            with session_scope() as session:
                run = TrainingRun(status="running", config=config.model_dump())
                session.add(run)
                session.flush()
                run_id = run.id
            self._current_run = run_id

        thread = threading.Thread(target=self._train_background, args=(run_id, config), daemon=True)
        thread.start()
        return run_id

    def _train_background(self, run_id: int, config: TrainingConfig) -> None:
        try:
            self._simulate_training(run_id, config)
        finally:
            with self._lock:
                self._current_run = None

    def _simulate_training(self, run_id: int, config: TrainingConfig) -> None:
        epochs = config.epochs
        with session_scope() as session:
            run = session.get(TrainingRun, run_id)
            if not run:
                return
            run.status = "running"
            session.add(run)

        last_loss = None
        for epoch in range(epochs):
            time.sleep(1.0)
            loss = random.uniform(0.1, 1.0) / (epoch + 1)
            last_loss = loss
            with session_scope() as session:
                run = session.get(TrainingRun, run_id)
                if not run:
                    return
                run.metrics = {"epoch": epoch + 1, "loss": loss}
                session.add(run)

        with session_scope() as session:
            run = session.get(TrainingRun, run_id)
            if not run:
                return
            run.status = "completed"
            run.finished_at = datetime.utcnow()
            run.metrics = {"epochs": epochs, "final_loss": last_loss}
            session.add(run)

    def list_runs(self) -> list[TrainingRun]:
        with session_scope() as session:
            return session.scalars(select(TrainingRun).order_by(TrainingRun.started_at.desc())).all()
