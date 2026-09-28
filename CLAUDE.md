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
- Next: M1 backend (upload, ask, list documents, citations, refusal rule, pytest)
