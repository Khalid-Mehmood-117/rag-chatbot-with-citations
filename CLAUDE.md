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
- Done: M2 evaluation (2026-09-28). eval/questions.json has 20 questions on the DOI handbook
  (15 answerable with expected page, 5 unanswerable). eval/run_eval.py calls POST /ask for each,
  judges answers with gpt-4o-mini, checks the expected page appears in the citations and writes
  eval/results.md. eval/tune_threshold.py prints the best retrieval similarity per question.
- M2 verification: run_eval.py against the local backend with a real key. Result: 20/20 answers
  correct, 15/15 citations on the expected page, 5/5 refusals, 0 false refusals. Same result at
  threshold 0.25 and 0.35. pytest: 26 passed.
- Design changes in M2: SIMILARITY_THRESHOLD raised from 0.25 to 0.35 (answerable questions scored
  0.45 to 0.75, unanswerable 0.03 to 0.49, so the threshold is a cheap pre-filter and the prompt
  layer does the real refusing). Citation snippet is now the chunk sentence with the most keyword
  overlap with the question plus the answer, capped at 300 characters, instead of the first 200
  characters of the chunk.
- Git identity fixed: all commits on main rewritten to Khalid Mehmood and force-pushed.
- Done: M3 frontend (2026-09-28). Next.js 16 App Router, TypeScript, Tailwind 4 in frontend/.
  lib/api.ts is the typed client (XMLHttpRequest for upload progress, fetch otherwise, one ApiError type).
  Components: UploadDropzone (drag and drop, progress bar, processing state, page and chunk counts),
  DocumentList (name, pages, uploaded time), ChatWindow, MessageBubble (user, answer, refusal, error
  styles), CitationList (chips with document and page, click expands the snippet). Backend URL from
  NEXT_PUBLIC_API_URL with http://localhost:8000 default. Light theme only, no dev indicator.
- M3 verification: backend and frontend run locally, full flow driven in headless Chrome with Playwright:
  upload of the DOI handbook showed 33 pages and 33 chunks, the vacation question answered with a
  page 7 chip whose snippet is the accrual table line, the World Cup question rendered the muted
  "Not in documents" refusal. Zero console errors and zero page errors. tsc and eslint clean.
  Screenshots in docs/screenshots (01-upload, 02-answer-with-citation, 03-refusal).
- Ops note: Docker Desktop failed to start mid-session because of stale Unix socket reparse points in
  %LOCALAPPDATA%\Docker
un. Fix that worked: quit Docker Desktop, rename the run folder, relaunch.
- Next: M4 docker-compose for db + backend + frontend, README with setup, architecture diagram,
  eval results, screenshots and demo GIF.
