from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .dataset import DatasetStore, get_dataset_store
from .schematic import load_schematic, save_schematic
from .schemas import (
    ConversionRequest,
    DatasetEntryResponse,
    DatasetUpdateRequest,
    DatasetUploadResponse,
    GenerationRequest,
    GenerationResponse,
    TrainingRequest,
    TrainingStatusResponse,
)
from .training import TrainingConfig, generate_structure, get_training_state, start_training

app = FastAPI(title="Schem Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.generated_dir.mkdir(parents=True, exist_ok=True)
settings.dataset_dir.mkdir(parents=True, exist_ok=True)
app.mount("/generated", StaticFiles(directory=settings.generated_dir), name="generated")
app.mount("/dataset", StaticFiles(directory=settings.dataset_dir), name="dataset")


def get_store() -> DatasetStore:
    return get_dataset_store()


@app.get("/api/dataset", response_model=List[DatasetEntryResponse])
def list_dataset(store: DatasetStore = Depends(get_store)) -> List[DatasetEntryResponse]:
    return [DatasetEntryResponse(**entry.to_dict()) for entry in store.list_entries()]


@app.post("/api/dataset/upload", response_model=DatasetUploadResponse)
async def upload_schematic(file: UploadFile = File(...), store: DatasetStore = Depends(get_store)) -> DatasetUploadResponse:
    suffix = Path(file.filename).suffix
    if suffix.lower() not in {".schem", ".schematic", ".litematic"}:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        schematic = load_schematic(tmp_path)
    except Exception as exc:  # pragma: no cover - parse errors bubble up
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to read schematic: {exc}") from exc
    stored_name = f"{Path(file.filename).stem}_{uuid.uuid4().hex}{suffix}"
    destination = settings.dataset_dir / stored_name
    shutil.move(str(tmp_path), destination)
    entry = store.add(
        original_name=file.filename,
        stored_name=stored_name,
        size=schematic.size,
        file_format=suffix.lstrip("."),
    )
    return DatasetUploadResponse(
        id=entry.id,
        filename=entry.filename,
        original_name=entry.original_name,
        size=entry.size,
        format=entry.format,
    )


@app.patch("/api/dataset/{entry_id}", response_model=DatasetEntryResponse)
async def update_dataset_entry(entry_id: str, request: DatasetUpdateRequest, store: DatasetStore = Depends(get_store)) -> DatasetEntryResponse:
    entry = store.update(
        entry_id,
        tags=request.tags,
        description=request.description,
        crop_region=request.crop_region,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Dataset entry not found")
    return DatasetEntryResponse(**entry.to_dict())


@app.delete("/api/dataset/{entry_id}")
def delete_dataset_entry(entry_id: str, store: DatasetStore = Depends(get_store)) -> dict:
    entry = store.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dataset entry not found")
    store.remove(entry_id)
    return {"status": "deleted"}


@app.get("/api/dataset/{entry_id}/viewer")
def preview_dataset_entry(entry_id: str, store: DatasetStore = Depends(get_store)) -> dict:
    entry = store.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dataset entry not found")
    path = settings.dataset_dir / entry.filename
    schematic = load_schematic(path)
    if entry.crop_region.max:
        min_x, min_y, min_z = entry.crop_region.min
        max_x, max_y, max_z = entry.crop_region.max
        schematic = schematic.crop((min_x, min_y, min_z), (max_x, max_y, max_z))
    return schematic.to_json()


@app.get("/api/dataset/{entry_id}/download")
def download_dataset_entry(entry_id: str, store: DatasetStore = Depends(get_store)) -> FileResponse:
    entry = store.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dataset entry not found")
    path = settings.dataset_dir / entry.filename
    return FileResponse(path)


@app.post("/api/train", response_model=TrainingStatusResponse)
def trigger_training(request: TrainingRequest, store: DatasetStore = Depends(get_store)) -> TrainingStatusResponse:
    config = TrainingConfig(
        epochs=request.epochs,
        batch_size=request.batch_size,
        learning_rate=request.learning_rate,
        target_shape=request.target_size,
    )
    start_training(config)
    state = get_training_state()
    return TrainingStatusResponse(**state)


@app.get("/api/train/status", response_model=TrainingStatusResponse)
def training_status() -> TrainingStatusResponse:
    state = get_training_state()
    return TrainingStatusResponse(**state)


@app.post("/api/generate", response_model=GenerationResponse)
def generate(request: GenerationRequest) -> GenerationResponse:
    output_path = generate_structure(request.prompt, request.output_format, request.target_size)
    schematic = load_schematic(output_path)
    viewer_data = schematic.to_json()
    relative = f"/generated/{output_path.name}"
    return GenerationResponse(file=relative, viewer_data=viewer_data)


@app.post("/api/convert", response_model=GenerationResponse)
def convert_schema(request: ConversionRequest) -> GenerationResponse:
    source_path = Path(request.source_path)
    if not source_path.is_absolute():
        dataset_candidate = settings.dataset_dir / source_path
        generated_candidate = settings.generated_dir / source_path
        if dataset_candidate.exists():
            source_path = dataset_candidate
        elif generated_candidate.exists():
            source_path = generated_candidate
        else:
            raise HTTPException(status_code=404, detail="Source schematic not found")
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Source schematic not found")
    schematic = load_schematic(source_path)
    output_path = settings.generated_dir / f"{source_path.stem}_converted.{request.output_format}"
    save_schematic(schematic, output_path, fmt=request.output_format)
    viewer_data = schematic.to_json()
    relative = f"/generated/{output_path.name}"
    return GenerationResponse(file=relative, viewer_data=viewer_data)
