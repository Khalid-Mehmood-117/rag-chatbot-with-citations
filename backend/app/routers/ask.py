"""POST /ask answers a question from the uploaded documents, with citations."""

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.generate import answer_question
from app.openai_client import get_openai_client
from app.retrieval import embed_query, search_chunks
from app.schemas import AskRequest, AskResponse

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    session: AsyncSession = Depends(get_session),
    client: AsyncOpenAI = Depends(get_openai_client),
) -> AskResponse:
    query_embedding = await embed_query(client, body.question)
    chunks = await search_chunks(
        session, query_embedding, get_settings().top_k, body.document_ids
    )
    return await answer_question(client, body.question, chunks)
