"""POST /documents uploads a PDF. GET /documents lists what has been uploaded."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.ingest import ingest_pdf
from app.models import Document
from app.openai_client import get_openai_client
from app.schemas import DocumentOut, UploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def validate_pdf(file: UploadFile, data: bytes) -> None:
    name = (file.filename or "").lower()
    if not name.endswith(".pdf") or not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF is larger than 25 MB")


@router.post("", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    client: AsyncOpenAI = Depends(get_openai_client),
) -> UploadResponse:
    data = await file.read()
    validate_pdf(file, data)
    try:
        document = await ingest_pdf(session, client, file.filename or "upload.pdf", data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return UploadResponse.model_validate(document, from_attributes=True)


@router.get("", response_model=list[DocumentOut])
async def list_documents(session: AsyncSession = Depends(get_session)) -> list[DocumentOut]:
    rows = (await session.execute(select(Document).order_by(Document.uploaded_at.desc()))).scalars()
    return [DocumentOut.model_validate(row, from_attributes=True) for row in rows]
