from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from .database import Base


class SchematicEntry(Base):
    __tablename__ = "schematics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    format = Column(String, nullable=False)
    tags = Column(JSON, nullable=False, default=list)
    description = Column(String, nullable=True)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    config = Column(JSON, default=dict)
    metrics = Column(JSON, default=dict)
