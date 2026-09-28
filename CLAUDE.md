# CLAUDE.md

## Project
RAG chatbot that answers questions from uploaded PDFs with source citations (document name and page number). Public portfolio project on GitHub, shown to Upwork clients. Code quality, README and evaluation results matter.

## Owner
Khalid Mehmood, AI Engineer. Working with Claude Code as the daily coding partner. Windows machine, repo at C:\Data\Projects\rag-chatbot-with-citations.

## Stack (fixed, do not change without asking)
- Backend: Python 3.13, FastAPI, direct OpenAI SDK (no LangChain)
- Models: text-embedding-3-small for embeddings, gpt-4o-mini for answers
- Database: PostgreSQL 16 with pgvector, in Docker
- Frontend: Next.js (App Router, TypeScript, Tailwind)
- PDF parsing: pypdf
- Tests: pytest with OpenAI mocked

## Rules
- Follow PLAN.md. Milestones M1 to M4 in order. Do not start the next milestone until the current one is verified with real output.
- Never commit .env or any API key. .env.example is the only env file in git.
- Refusal rule: if the retrieved chunks do not contain the answer, reply exactly "I don't have that in the documents".
- Every answer must return citations with document name and page number.
- No em dashes in any file, README or comment.
- Prefer small, readable functions over clever code. This repo is read by clients.
- Commit after every verified milestone with a clear message, then push to origin main.

## Self-maintenance (mandatory)
At the end of every milestone, before telling the owner it is done:
1. Update the Status section below: what is complete, what was verified and how, what is next.
2. Update PLAN.md if any design decision changed.
3. Commit CLAUDE.md and PLAN.md together with the milestone code.
Do this without being asked. A milestone is not complete until this is done.

## Status
- Environment verified: Python 3.13.5, Docker 29.7.2, Node 24.14.0, npm 11.9.0, Git 2.55.0
- Done: PLAN.md, .env.example, .gitignore, CLAUDE.md
- Done: M1 backend (2026-09-28). FastAPI app in backend/app with POST /documents, GET /documents,
  POST /ask, GET /health. pgvector Postgres runs from docker-compose.yml (db service only for now).
  Sample document: eval/sample_docs/doi_absence_and_leave_handbook.pdf (US DOI, public domain, 33 pages).
- M1 verification: server run locally with uvicorn against the Docker database and a real OpenAI key.
  Upload curl returned 33 pages and 33 chunks. Ask curl "How many vacation days do new employees get?"
  returned the 13 days per year answer citing page 7. FMLA question cited page 6. An off-topic question
  returned the exact refusal string with refused=true and no citations. pytest: 21 passed (OpenAI and
  database faked).
- Design notes from M1: chunks are 600 word windows with 75 word overlap (no tokenizer dependency),
  similarity threshold 0.25 kept as the starting value for M2 tuning, system prompt tells the model that
  question wording may differ from source wording (needed for "vacation" vs "annual leave").
- Next: M2 evaluation (eval/questions.json with 20 questions, eval/run_eval.py, eval/results.md).
