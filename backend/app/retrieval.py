"""Query embedding and cosine similarity search over stored chunks."""

import uuid
from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Chunk


@dataclass
class RetrievedChunk:
    document_name: str
    page_number: int
    text: str
    similarity: float


async def embed_query(client: AsyncOpenAI, question: str) -> list[float]:
    response = await client.embeddings.create(
        model=get_settings().embedding_model, input=question
    )
    return response.data[0].embedding


async def search_chunks(
    session: AsyncSession,
    query_embedding: list[float],
    top_k: int,
    document_ids: list[uuid.UUID] | None = None,
) -> list[RetrievedChunk]:
    """Return the top_k most similar chunks, best first. Similarity is 1 - cosine distance."""
    distance = Chunk.embedding.cosine_distance(query_embedding).label("distance")
    query = select(Chunk, distance).order_by(distance).limit(top_k)
    if document_ids:
        query = query.where(Chunk.document_id.in_(document_ids))

    rows = (await session.execute(query)).all()
    return [
        RetrievedChunk(
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            text=chunk.text,
            similarity=1.0 - float(dist),
        )
        for chunk, dist in rows
    ]
