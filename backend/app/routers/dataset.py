from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..schemas import DatasetItem
from ..services.dataset import DatasetService
from ..utils.schematic import renderable_payload

router = APIRouter(prefix="/dataset", tags=["dataset"])


def get_service() -> DatasetService:
    return DatasetService()


@router.get("/", response_model=list[DatasetItem])
def list_dataset(service: DatasetService = Depends(get_service)) -> list[DatasetItem]:
    return service.list_items()


@router.post("/", response_model=DatasetItem)
async def upload_schematic(
    tags: str | None = Form(None),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    service: DatasetService = Depends(get_service),
) -> DatasetItem:
    suffix = Path(file.filename).suffix
    if suffix.lower().lstrip('.') not in {"schem", "schematic", "litematic"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    temp_path = service.storage_dir / file.filename
    with temp_path.open("wb") as buffer:
        buffer.write(await file.read())

    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    return service.add_file(temp_path, file.filename, tags=tag_list, description=description)


@router.get("/{item_id}/download")
def download_schematic(item_id: int, service: DatasetService = Depends(get_service)) -> StreamingResponse:
    items = {item.id: item for item in service.list_items()}
    item = items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    path = service.resolve_path(item.filename)
    return StreamingResponse(path.open("rb"), media_type="application/octet-stream",
                             headers={"Content-Disposition": f"attachment; filename={item.filename}"})


@router.get("/{item_id}/viewer")
def schematic_for_viewer(item_id: int, service: DatasetService = Depends(get_service)) -> StreamingResponse:
    items = {item.id: item for item in service.list_items()}
    item = items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    path = service.resolve_path(item.filename)
    payload = renderable_payload(path)
    return StreamingResponse(iter([payload]), media_type="application/octet-stream")
