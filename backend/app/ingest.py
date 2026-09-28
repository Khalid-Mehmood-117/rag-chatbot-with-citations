"""PDF ingestion: bytes -> pages -> chunks -> embeddings -> database rows."""

import io
from dataclasses import dataclass

from openai import AsyncOpenAI
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Chunk, Document

EMBED_BATCH_SIZE = 100


@dataclass
class PageChunk:
    page_number: int
    chunk_index: int
    text: str


def extract_pages(data: bytes) -> list[tuple[int, str]]:
    """Return (page_number, text) for every page that has text. Page numbers start at 1."""
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((number, text))
    return pages


def chunk_text(text: str, size_words: int, overlap_words: int) -> list[str]:
    """Split text into overlapping word windows. A short text becomes a single chunk."""
    if overlap_words >= size_words:
        raise ValueError("overlap must be smaller than chunk size")
    words = text.split()
    if not words:
        return []
    step = size_words - overlap_words
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start : start + size_words]))
        if start + size_words >= len(words):
            break
    return chunks


def chunk_pages(pages: list[tuple[int, str]]) -> list[PageChunk]:
    """Chunk each page on its own so a chunk never spans two pages."""
    settings = get_settings()
    result = []
    for page_number, text in pages:
        for piece in chunk_text(text, settings.chunk_size_words, settings.chunk_overlap_words):
            result.append(PageChunk(page_number, len(result), piece))
    return result


async def embed_texts(client: AsyncOpenAI, texts: list[str]) -> list[list[float]]:
    """Embed texts in batches, preserving order."""
    settings = get_settings()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        response = await client.embeddings.create(model=settings.embedding_model, input=batch)
        vectors.extend(item.embedding for item in response.data)
    return vectors


async def ingest_pdf(
    session: AsyncSession, client: AsyncOpenAI, filename: str, data: bytes
) -> Document:
    """Parse, chunk, embed and store one PDF. Returns the saved Document row."""
    pages = extract_pages(data)
    if not pages:
        raise ValueError("The PDF contains no extractable text")

    chunks = chunk_pages(pages)
    vectors = await embed_texts(client, [chunk.text for chunk in chunks])

    document = Document(name=filename, pages=pages[-1][0], chunks=len(chunks))
    document.chunk_rows = [
        Chunk(
            document_name=filename,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            embedding=vector,
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document
