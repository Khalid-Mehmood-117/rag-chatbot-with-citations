"""Prompt building, the answer call to gpt-4o-mini, citation parsing and the refusal rule."""

import re

from openai import AsyncOpenAI

from app.config import get_settings
from app.retrieval import RetrievedChunk
from app.schemas import AskResponse, Citation

REFUSAL = "I don't have that in the documents"
SNIPPET_CHARS = 300

SYSTEM_PROMPT = f"""You answer questions using only the numbered sources provided.
Rules:
1. Use only facts that appear in the sources. Do not use outside knowledge.
2. The question may use different words than the sources (for example "vacation" for
   "annual leave"). If a source clearly answers the question under another name, use it.
3. After each claim, append the bracket number of the source it came from, like [1] or [2].
4. If the sources do not contain the answer, reply exactly: {REFUSAL}
5. Keep the answer short and direct."""

CITATION_PATTERN = re.compile(r"\[(\d+)\]")
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
STOPWORDS = {
    "the", "and", "for", "are", "does", "how", "what", "when", "who", "why", "which", "can",
    "may", "with", "from", "that", "this", "into", "have", "has", "get", "many", "much",
    "any", "per", "their", "there", "they", "will", "not", "his", "her", "each", "under",
}


def format_sources(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for index, chunk in enumerate(chunks, start=1):
        lines.append(f"[{index}] ({chunk.document_name}, p.{chunk.page_number}) {chunk.text}")
    return "\n\n".join(lines)


def build_messages(question: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    user_content = f"Sources:\n\n{format_sources(chunks)}\n\nQuestion: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def parse_cited_indexes(answer: str, source_count: int) -> list[int]:
    """Bracket numbers used in the answer, deduplicated, in order of first use."""
    cited = []
    for match in CITATION_PATTERN.findall(answer):
        index = int(match)
        if 1 <= index <= source_count and index not in cited:
            cited.append(index)
    return cited


def split_sentences(text: str) -> list[str]:
    collapsed = " ".join(text.split())
    return [s for s in SENTENCE_BOUNDARY.split(collapsed) if s]


def keywords(text: str) -> set[str]:
    """Lowercase words with a trailing s removed, so 'employees' matches 'employee'."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w.rstrip("s") for w in words if len(w) > 2 and w not in STOPWORDS}


def truncate(text: str) -> str:
    if len(text) <= SNIPPET_CHARS:
        return text
    return text[:SNIPPET_CHARS].rstrip() + "..."


def make_snippet(text: str, question: str, answer: str = "") -> str:
    """The sentence of the chunk that best matches the question.

    The answer's words are counted too, because the answer repeats the source wording even
    when the question does not (for example "vacation" versus "annual leave").
    """
    sentences = split_sentences(text)
    if not sentences:
        return ""
    target = keywords(question) | keywords(answer)
    best = max(sentences, key=lambda s: len(keywords(s) & target))
    if not keywords(best) & target:
        best = sentences[0]
    return truncate(best)


def build_citations(answer: str, chunks: list[RetrievedChunk], question: str) -> list[Citation]:
    """Only the chunks the model actually cited are returned."""
    return [
        Citation(
            index=index,
            document=chunks[index - 1].document_name,
            page=chunks[index - 1].page_number,
            snippet=make_snippet(chunks[index - 1].text, question, answer),
        )
        for index in parse_cited_indexes(answer, len(chunks))
    ]


def refusal_response() -> AskResponse:
    return AskResponse(answer=REFUSAL, citations=[], refused=True)


def is_refusal(answer: str) -> bool:
    return REFUSAL.lower() in answer.lower()


async def call_llm(client: AsyncOpenAI, messages: list[dict[str, str]]) -> str:
    response = await client.chat.completions.create(
        model=get_settings().chat_model, messages=messages, temperature=0
    )
    return (response.choices[0].message.content or "").strip()


async def answer_question(
    client: AsyncOpenAI, question: str, chunks: list[RetrievedChunk]
) -> AskResponse:
    """Apply the refusal rule before and after the model call. See PLAN.md section 5."""
    threshold = get_settings().similarity_threshold
    if not chunks or chunks[0].similarity < threshold:
        return refusal_response()

    answer = await call_llm(client, build_messages(question, chunks))
    citations = build_citations(answer, chunks, question)
    if is_refusal(answer) or not citations:
        return refusal_response()
    return AskResponse(answer=answer, citations=citations, refused=False)
