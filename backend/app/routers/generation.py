from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from ..config import get_settings
from ..schemas import GenerateRequest, GenerateResponse
from ..services.generator import StructureGenerator

router = APIRouter(prefix="/generate", tags=["generation"])


def get_service() -> StructureGenerator:
    return StructureGenerator()


@router.post("/", response_model=GenerateResponse)
def generate_structure(payload: GenerateRequest, service: StructureGenerator = Depends(get_service)) -> GenerateResponse:
    output_path = service.generate(payload.prompt, payload.format)
    return GenerateResponse(
        filename=output_path.name,
        format=payload.format,
        download_url=f"/generate/download/{output_path.name}",
    )


@router.get("/download/{filename}")
def download_generated(filename: str, service: StructureGenerator = Depends(get_service)) -> FileResponse:
    path = service.output_dir / filename
    if not path.exists():
        raise FileNotFoundError(filename)
    return FileResponse(path)
