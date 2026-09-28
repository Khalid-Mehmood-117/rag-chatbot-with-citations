"""Print the best retrieval similarity for every eval question to help pick SIMILARITY_THRESHOLD.

Usage (from the repo root, with the database running and the sample PDF uploaded):
    python eval/tune_threshold.py

The refusal threshold should sit above the unanswerable questions and below the answerable ones.
This script talks to the database directly through the backend modules, so it needs the same
.env as the backend.
"""

import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.openai_client import get_openai_client  # noqa: E402
from app.retrieval import embed_query, search_chunks  # noqa: E402


async def best_similarity(question: str) -> float:
    client = get_openai_client()
    embedding = await embed_query(client, question)
    async with SessionLocal() as session:
        chunks = await search_chunks(session, embedding, top_k=1)
    return chunks[0].similarity if chunks else 0.0


async def main() -> None:
    items = json.loads((REPO_ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    scored = [(item, await best_similarity(item["question"])) for item in items]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    print(f"{'#':>2}  {'type':<12} {'best sim':>8}  question")
    for item, similarity in scored:
        print(f"{item['id']:>2}  {item['type']:<12} {similarity:>8.3f}  {item['question'][:70]}")

    answerable = [s for item, s in scored if item["type"] == "answerable"]
    unanswerable = [s for item, s in scored if item["type"] == "unanswerable"]
    print()
    print(f"Lowest answerable similarity:    {min(answerable):.3f}")
    print(f"Highest unanswerable similarity: {max(unanswerable):.3f}")
    print(f"Current SIMILARITY_THRESHOLD:    {get_settings().similarity_threshold:.3f}")
    if max(unanswerable) < min(answerable):
        midpoint = (max(unanswerable) + min(answerable)) / 2
        print(f"The two groups separate. A threshold near {midpoint:.2f} would refuse all unanswerable questions.")
    else:
        print("The two groups overlap, so the threshold alone cannot separate them. The prompt layer handles the rest.")


if __name__ == "__main__":
    asyncio.run(main())
