"""Request and response models for the API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    id: uuid.UUID
    name: str
    pages: int
    chunks: int


class DocumentOut(UploadResponse):
    uploaded_at: datetime


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_ids: list[uuid.UUID] | None = None


class Citation(BaseModel):
    index: int
    document: str
    page: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    refused: bool
