from __future__ import annotations
from sqlmodel import SQLModel, Field
from sqlalchemy import Enum as SqlEnum, JSON, Column
from enum import Enum
from typing import Optional, Any
from datetime import datetime, timezone

class ModelType(str, Enum):
    comic = "comic"
    grammar = "grammar"
    vocab = "vocab"

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    theme_id: int
    model_type: ModelType = Field(sa_type=SqlEnum(ModelType))
    status: JobStatus = Field(default=JobStatus.pending, sa_type=SqlEnum(JobStatus))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # результат воркера (произвольный JSON: словарь с explanation/vocabulary/и т.п.)
    result: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    # текст ошибки при failed
    error: Optional[str] = None
