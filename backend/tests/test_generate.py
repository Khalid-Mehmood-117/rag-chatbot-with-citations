from app.generate import REFUSAL, answer_question, build_citations, build_messages, parse_cited_indexes
from app.retrieval import RetrievedChunk
from tests.fakes import FakeOpenAI


def make_chunks(similarity: float = 0.8) -> list[RetrievedChunk]:
    return [
        RetrievedChunk("handbook.pdf", 12, "New employees earn 13 days of annual leave per year.", similarity),
        RetrievedChunk("handbook.pdf", 4, "Sick leave accrues at 4 hours per pay period.", similarity - 0.1),
    ]


def test_parse_cited_indexes_dedupes_and_ignores_out_of_range():
    assert parse_cited_indexes("Claim [2]. More [1] and again [2]. Bad [9].", 3) == [2, 1]


def test_build_citations_returns_only_cited_chunks():
    citations = build_citations("Thirteen days [1].", make_chunks())
    assert len(citations) == 1
    assert citations[0].document == "handbook.pdf"
    assert citations[0].page == 12
    assert "13 days" in citations[0].snippet


def test_build_messages_numbers_sources_with_document_and_page():
    messages = build_messages("How much leave?", make_chunks())
    assert messages[0]["role"] == "system"
    assert "[1] (handbook.pdf, p.12)" in messages[1]["content"]
    assert "[2] (handbook.pdf, p.4)" in messages[1]["content"]
    assert messages[1]["content"].endswith("Question: How much leave?")


async def test_answer_with_citations():
    client = FakeOpenAI(reply="New employees earn 13 days per year. [1]")
    response = await answer_question(client, "How much leave?", make_chunks())
    assert response.refused is False
    assert response.answer.startswith("New employees earn 13 days")
    assert [(c.document, c.page) for c in response.citations] == [("handbook.pdf", 12)]


async def test_low_similarity_refuses_without_calling_llm():
    client = FakeOpenAI(reply="should not be used")
    response = await answer_question(client, "What is the capital of France?", make_chunks(0.1))
    assert response.answer == REFUSAL
    assert response.refused is True
    assert response.citations == []
    assert client.chat.completions.calls == []


async def test_no_chunks_refuses():
    response = await answer_question(FakeOpenAI(), "Anything?", [])
    assert response.refused is True
    assert response.answer == REFUSAL


async def test_model_refusal_is_normalised():
    client = FakeOpenAI(reply="Sorry, I don't have that in the documents. [1]")
    response = await answer_question(client, "Who is the CEO?", make_chunks())
    assert response.answer == REFUSAL
    assert response.citations == []
    assert response.refused is True


async def test_answer_without_citations_is_refused():
    client = FakeOpenAI(reply="Probably 13 days.")
    response = await answer_question(client, "How much leave?", make_chunks())
    assert response.refused is True
    assert response.answer == REFUSAL
