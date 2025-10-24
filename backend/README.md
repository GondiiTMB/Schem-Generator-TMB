# Backend Service

This FastAPI application exposes endpoints required by the Minecraft AI structure generator platform. It is built for full local execution and is designed to be extended with a true generative model and real schematic conversion logic.

## Features

- REST endpoints to trigger structure generation, manage dataset uploads, and monitor training jobs.
- SQLite storage for schematic metadata and training runs.
- Placeholder generator and training simulation to unblock frontend integration.
- Designed to support `.schem`, `.schematic`, and `.litematic` assets.

## Running locally

```bash
uvicorn app.main:app --reload
```

By default the server listens on `http://127.0.0.1:8000` and exposes the OpenAPI schema at `/docs`.

## Extending

- Replace `StructureGenerator` with a model-backed generator that consumes prompts.
- Implement loss computation and dataset loading in `TrainingService` to hook into a real ML training pipeline.
- Swap the placeholder conversion logic in `utils.schematic` for a robust conversion library such as [amulet-nbt](https://github.com/Amulet-Team/Amulet-NBT).
