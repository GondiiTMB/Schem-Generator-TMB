from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import TrainingConfig, TrainingStatusResponse, TrainingRunResponse
from ..services.training import TrainingService

router = APIRouter(prefix="/training", tags=["training"])


def get_service() -> TrainingService:
    return TrainingService()


@router.post("/start")
def start_training(config: TrainingConfig, service: TrainingService = Depends(get_service)) -> dict:
    try:
        run_id = service.start_training(config)
        return {"run_id": run_id}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status", response_model=TrainingStatusResponse)
def training_status(service: TrainingService = Depends(get_service)) -> TrainingStatusResponse:
    runs = service.list_runs()
    payload = [
        TrainingRunResponse(
            run_id=run.id,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            metrics=run.metrics or {},
        )
        for run in runs
    ]
    return TrainingStatusResponse(runs=payload)
