# Schem-Generator-TMB

A fully local, extensible Minecraft structure generation platform featuring a FastAPI backend, Vite/React frontend, dataset management, and integrated 3D schematic previewing.

## Project layout

```
.
├── backend/              # FastAPI application with dataset, training, and generation endpoints
├── data/                 # Local storage for datasets, generated assets, and models
├── frontend/             # Vite + React single-page application
├── pyproject.toml        # Python project definition
└── README.md
```

## Getting started

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install
uvicorn app.main:app --reload --app-dir backend
```

The API will be accessible at `http://127.0.0.1:8000`. Interactive documentation is available at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies API calls to the FastAPI backend.

## Key capabilities

- Prompt-based structure generation endpoint (currently placeholder) with pluggable model interface.
- Dataset ingestion pipeline with metadata tracking and viewer-ready streaming.
- Training orchestration endpoint with asynchronous execution hooks.
- Modern React UI with tabs for generation, training, and a schematic viewer powered by [`schematic-renderer`](https://github.com/Schem-at/schematic-renderer).

## Next steps

- Replace the placeholder generator/trainer with your custom PyTorch or TensorFlow models.
- Integrate a robust schematic conversion toolkit (e.g., Amulet) to ensure fidelity across `.schem`, `.schematic`, and `.litematic` formats.
- Enhance the viewer pipeline to support cropping, trimming, and tagging workflows before pushing data into the dataset.
