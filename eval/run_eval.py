"""Run the evaluation set against a running backend and write eval/results.md.

Usage (from the repo root, with the backend running and the sample PDF uploaded):
    python eval/run_eval.py [--base-url http://localhost:8000] [--questions eval/questions.json]

Scoring:
  - Answer correctness: gpt-4o-mini judges whether the bot's answer conveys the expected answer.
    For unanswerable questions, correct means the bot refused.
  - Citation accuracy (answerable only): every expected page of the expected document appears in
    the citations. Two-page questions need both pages.
  - Refusal accuracy: share of unanswerable questions that were refused.
"""

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parents[1]
REFUSAL = "I don't have that in the documents"
JUDGE_MODEL = "gpt-4o-mini"

JUDGE_PROMPT = """You are grading a question answering system.
Question: {question}
Expected answer: {expected}
System answer: {answer}

Answer yes only if every fact in the expected answer is present in the system answer with the same
meaning. If any expected fact is missing, contradicted or replaced by a different fact, answer no.
Extra detail beyond the expected answer is fine.
Reply with exactly one word: yes or no."""


@dataclass
class Result:
    id: int
    type: str
    group: str
    question: str
    answer: str
    refused: bool
    correct: bool
    citation_ok: bool | None
    cited_pages: list[int]


def ask(client: httpx.Client, question: str) -> dict:
    response = client.post("/ask", json={"question": question}, timeout=120)
    response.raise_for_status()
    return response.json()


def judge(openai_client: OpenAI, question: str, expected: str, answer: str) -> bool:
    prompt = JUDGE_PROMPT.format(question=question, expected=expected, answer=answer)
    response = openai_client.chat.completions.create(
        model=JUDGE_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0
    )
    return (response.choices[0].message.content or "").strip().lower().startswith("yes")


def citation_matches(item: dict, citations: list[dict]) -> bool:
    """True when every expected page of the expected document was cited."""
    cited_pages = {c["page"] for c in citations if c["document"] == item["expected_document"]}
    return all(page in cited_pages for page in item["expected_pages"])


def evaluate_item(item: dict, client: httpx.Client, openai_client: OpenAI) -> Result:
    response = ask(client, item["question"])
    refused = response["refused"]
    citations = response["citations"]

    if item["type"] == "unanswerable":
        correct = refused
        citation_ok = None
    else:
        correct = not refused and judge(openai_client, item["question"], item["expected_answer"], response["answer"])
        citation_ok = citation_matches(item, citations)

    return Result(
        id=item["id"],
        type=item["type"],
        group=item.get("group", "base"),
        question=item["question"],
        answer=response["answer"],
        refused=refused,
        correct=correct,
        citation_ok=citation_ok,
        cited_pages=[c["page"] for c in citations],
    )


def percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{100 * numerator / denominator:.0f}%"


def summarise(results: list[Result]) -> dict[str, str]:
    answerable = [r for r in results if r.type == "answerable"]
    unanswerable = [r for r in results if r.type == "unanswerable"]
    return {
        f"Answer accuracy (all {len(results)})": percent(sum(r.correct for r in results), len(results)),
        "Answer accuracy (answerable)": percent(sum(r.correct for r in answerable), len(answerable)),
        "Citation accuracy (answerable)": percent(sum(bool(r.citation_ok) for r in answerable), len(answerable)),
        "Refusal accuracy (unanswerable)": percent(sum(r.refused for r in unanswerable), len(unanswerable)),
        "False refusals (answerable)": f"{sum(r.refused for r in answerable)} of {len(answerable)}",
    }


def summarise_by_group(results: list[Result]) -> list[tuple[str, str, str]]:
    """(group, description, correct count) rows in a fixed order."""
    descriptions = {
        "base": "Base set, direct questions",
        "paraphrase": "Paraphrased wording",
        "two-page": "Needs two pages",
        "near-topic": "Unanswerable, close to the handbook topic",
    }
    rows = []
    for group, description in descriptions.items():
        members = [r for r in results if r.group == group]
        if members:
            rows.append((group, description, f"{sum(r.correct for r in members)} of {len(members)}"))
    return rows


def mark(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def render_markdown(results: list[Result], summary: dict[str, str], sample_doc: str) -> str:
    answerable = sum(r.type == "answerable" for r in results)
    unanswerable = len(results) - answerable
    lines = [
        "# Evaluation results",
        "",
        f"Run on {date.today().isoformat()} against `{sample_doc}` with {len(results)} questions "
        f"({answerable} answerable, {unanswerable} unanswerable). Answers are judged by gpt-4o-mini, "
        "citations are checked against the expected pages (two-page questions need both).",
        "",
        "## Summary",
        "",
        "| Metric | Result |",
        "|---|---|",
    ]
    lines += [f"| {name} | {value} |" for name, value in summary.items()]
    lines += ["", "## By question group", "", "| Group | Description | Correct |", "|---|---|---|"]
    lines += [f"| {g} | {d} | {c} |" for g, d, c in summarise_by_group(results)]
    lines += [
        "",
        "## Per question",
        "",
        "| # | Group | Type | Question | Correct | Citation | Refused | Pages cited |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        pages = ", ".join(str(p) for p in r.cited_pages) or "-"
        lines.append(
            f"| {r.id} | {r.group} | {r.type} | {r.question} | {mark(r.correct)} | {mark(r.citation_ok)} | "
            f"{mark(r.refused)} | {pages} |"
        )
    lines.append("")
    return "\n".join(lines)


def print_table(results: list[Result], summary: dict[str, str]) -> None:
    print(f"{'#':>2}  {'group':<11} {'type':<12} {'correct':<8} {'citation':<9} {'refused':<8} pages")
    for r in results:
        pages = ",".join(str(p) for p in r.cited_pages) or "-"
        print(f"{r.id:>2}  {r.group:<11} {r.type:<12} {mark(r.correct):<8} {mark(r.citation_ok):<9} {mark(r.refused):<8} {pages}")
    print()
    for name, value in summary.items():
        print(f"{name}: {value}")
    for group, description, count in summarise_by_group(results):
        print(f"{description}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--questions", default=str(REPO_ROOT / "eval" / "questions.json"))
    parser.add_argument("--output", default=str(REPO_ROOT / "eval" / "results.md"))
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    items = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    openai_client = OpenAI()

    with httpx.Client(base_url=args.base_url) as client:
        results = [evaluate_item(item, client, openai_client) for item in items]

    summary = summarise(results)
    print_table(results, summary)

    sample_doc = next((i["expected_document"] for i in items if i["expected_document"]), "sample document")
    Path(args.output).write_text(render_markdown(results, summary, sample_doc), encoding="utf-8")
    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
