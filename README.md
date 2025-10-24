# Schem-Generator-TMB

A fully local Minecraft structure generator that lets you train a voxel VAE on custom schematic datasets and generate new builds directly from text prompts. The web interface provides dataset curation, training controls, multi-format exporting, and an interactive 3D viewer inspired by [BuilderGPT](https://github.com/CyniaAI/BuilderGPT) with rendering support adapted from [schematic-renderer](https://github.com/Schem-at/schematic-renderer).

## Features

- **Local AI pipeline** – no external APIs. Upload schematics, tag them, crop regions, and train a conditional voxel VAE with configurable epochs, batch size, learning rate, and output size.
- **Multi-format support** – `.schem`, `.schematic`, and `.litematic` ingestion with export/convert endpoints for compatibility with FAWE, WorldEdit, Litematica, and Amulet.
- **Modern web dashboard** – prompts, training controls, dataset explorer, and live viewer built with Vite + React using the classic Minecraft font and soft gray “Apple-like” theming.
- **3D inspection** – embedded viewer with orbit, zoom, and layer filtering. Automatically updates when schematics are uploaded, cropped, generated, or converted.

## Project structure

```
backend/      FastAPI application, model training utilities, schematic IO
frontend/     Vite + React interface with schematic viewer
data/         Default storage location for dataset, model checkpoints, and outputs
```

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies API calls to `http://localhost:8000`.

## Usage workflow

1. **Upload schematics** via the Training Lab tab. Tag, describe, and crop regions to focus the dataset.
2. **Start training** with your preferred hyperparameters. Training runs in the FastAPI background thread and persists vocabulary/model checkpoints under `data/model`.
3. **Generate structures** from text prompts on the Generation Studio tab. Choose an export format, preview the result in 3D, and download the schematic.
4. **Convert** existing schematics by calling the `/api/convert` endpoint with a source path and target format to quickly re-export between `.schem`, `.schematic`, and `.litematic`.

## API overview

- `POST /api/dataset/upload` – upload schematics (multi-format).
- `PATCH /api/dataset/{id}` – save tags, descriptions, and crop regions.
- `GET /api/dataset/{id}/viewer` – retrieve voxel data for the viewer.
- `POST /api/train` – trigger training with custom hyperparameters.
- `GET /api/train/status` – poll background training status.
- `POST /api/generate` – produce a new schematic for a prompt.
- `POST /api/convert` – re-export an existing schematic into a new format.

## Notes

- The VAE implementation is intentionally lightweight and intended as a starting point. For larger builds increase the target size and adjust the architecture as needed.
- Litematica support relies on the optional `litemapy` dependency; install Java if the library requires it for certain operations.
- Generated schematics are saved to `data/generated`. Dataset uploads live under `data/dataset` with metadata tracked in `data/dataset/metadata.json`.

Happy building! 🏰
