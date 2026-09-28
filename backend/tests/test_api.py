"""Endpoint tests. The database and OpenAI are replaced with fakes."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.db import get_session
from app.generate import REFUSAL
from app.main import app
from app.models import Document
from app.openai_client import get_openai_client
from app.retrieval import RetrievedChunk
from app.routers import ask as ask_router
from app.routers import documents as documents_router
from tests.fakes import FakeOpenAI


class FakeSession:
    pass


@pytest.fixture
def client_factory():
    def make(reply: str = "") -> tuple[TestClient, FakeOpenAI]:
        fake = FakeOpenAI(reply)
        app.dependency_overrides[get_openai_client] = lambda: fake
        app.dependency_overrides[get_session] = lambda: FakeSession()
        return TestClient(app), fake

    yield make
    app.dependency_overrides.clear()


def test_health(client_factory):
    client, _ = client_factory()
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_returns_answer_with_citations(client_factory, monkeypatch):
    client, _ = client_factory(reply="Employees get 13 days. [1]")

    async def fake_search(session, embedding, top_k, document_ids=None):
        return [RetrievedChunk("handbook.pdf", 12, "13 days of annual leave", 0.9)]

    monkeypatch.setattr(ask_router, "search_chunks", fake_search)
    body = client.post("/ask", json={"question": "How many days?"}).json()
    assert body["refused"] is False
    assert body["answer"] == "Employees get 13 days. [1]"
    assert body["citations"] == [
        {"index": 1, "document": "handbook.pdf", "page": 12, "snippet": "13 days of annual leave"}
    ]


def test_ask_refuses_when_nothing_retrieved(client_factory, monkeypatch):
    client, fake = client_factory(reply="should not be called")

    async def fake_search(session, embedding, top_k, document_ids=None):
        return []

    monkeypatch.setattr(ask_router, "search_chunks", fake_search)
    body = client.post("/ask", json={"question": "Who won the 1998 World Cup?"}).json()
    assert body == {"answer": REFUSAL, "citations": [], "refused": True}
    assert fake.chat.completions.calls == []


def test_ask_rejects_empty_question(client_factory):
    client, _ = client_factory()
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_upload_rejects_non_pdf(client_factory):
    client, _ = client_factory()
    response = client.post("/documents", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 400


def test_upload_returns_document_summary(client_factory, monkeypatch):
    client, _ = client_factory()
    doc_id = uuid.uuid4()

    async def fake_ingest(session, openai_client, filename, data):
        return Document(id=doc_id, name=filename, pages=3, chunks=7, uploaded_at=datetime.now(UTC))

    monkeypatch.setattr(documents_router, "ingest_pdf", fake_ingest)
    response = client.post("/documents", files={"file": ("handbook.pdf", b"%PDF-1.4 fake", "application/pdf")})
    assert response.status_code == 201
    assert response.json() == {"id": str(doc_id), "name": "handbook.pdf", "pages": 3, "chunks": 7}


def test_cors_origins_are_split_and_trimmed():
    from app.config import Settings

    settings = Settings(cors_origins="http://localhost:3000, http://localhost:3001 ,")
    assert settings.cors_origin_list() == ["http://localhost:3000", "http://localhost:3001"]
