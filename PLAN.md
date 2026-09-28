# PLAN.md: RAG Chatbot with Citations

**Status: complete.** All four milestones (M1 to M4) are done and verified. See the Status section of
CLAUDE.md for what was verified and how, and eval/results.md for the latest evaluation numbers.

A portfolio-grade Retrieval-Augmented Generation (RAG) chatbot. Users upload PDFs, ask
questions, and get answers grounded in those PDFs with document-and-page citations. If the
documents don't contain the answer, the bot says so instead of guessing.

## 1. Architecture

| Layer | Choice | Why |
|---|---|---|
| Backend API | **FastAPI** (Python 3.13) | Async, typed, auto OpenAPI docs at `/docs` |
| Chat UI | **Next.js** (App Router, TypeScript, Tailwind) | Familiar to clients, easy to deploy |
| Vector store | **PostgreSQL 16 + pgvector** in Docker | One database for metadata *and* vectors, no extra service |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) | Cheap, strong quality for retrieval |
| Answer model | OpenAI `gpt-4o-mini` | Low cost, fast, good enough for grounded Q&A |
| PDF parsing | `pypdf` | Pure Python, gives per-page text (needed for citations) |
| Orchestration | Direct `openai` SDK + thin custom code (no LangChain) | Fewer dependencies, every step is readable in the repo |

### Request flow

```
Upload:  PDF --> extract text per page --> chunk (600 words ~ 800 tokens, 75 words overlap)
             --> embed each chunk --> INSERT (document_id, page, text, embedding)

Ask:     question --> embed --> top-k cosine search in pgvector (k=5)
             --> build prompt with numbered chunks --> gpt-4o-mini
             --> answer + list of {document, page, snippet} citations
```

## 2. Folder structure

```
rag-chatbot-with-citations/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router registration
│   │   ├── config.py          # Settings from env (OPENAI_API_KEY, DATABASE_URL)
│   │   ├── openai_client.py   # Shared AsyncOpenAI client (a FastAPI dependency, faked in tests)
│   │   ├── db.py              # SQLAlchemy async engine, pgvector extension, table creation
│   │   ├── models.py          # documents + chunks tables
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── ingest.py          # PDF -> pages -> chunks -> embeddings
│   │   ├── retrieval.py       # embed query, similarity search
│   │   ├── generate.py        # prompt building, LLM call, refusal logic
│   │   └── routers/
│   │       ├── documents.py   # POST /documents, GET /documents
│   │       └── ask.py         # POST /ask
│   ├── tests/                 # pytest: chunking, refusal rule, endpoints (mocked OpenAI)
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                   # Next.js App Router pages
│   ├── components/            # ChatWindow, MessageBubble, CitationList, UploadDropzone
│   ├── lib/api.ts             # typed client for the backend
│   ├── package.json
│   └── Dockerfile
├── eval/
│   ├── questions.json         # 20 questions + expected answers + expected source
│   ├── run_eval.py            # runs questions against /ask, prints accuracy table
│   ├── sample_docs/           # the public-domain PDFs the questions are about
│   └── results.md             # latest eval output, committed for the README
├── docs/
│   ├── demo.gif               # recorded UI flow used in the README
│   └── screenshots/           # UI screenshots used in the README
├── docker-compose.yml         # postgres(pgvector) + backend + frontend
├── .env.example
├── .gitignore
├── PLAN.md
└── README.md                  # setup, demo GIF, eval results, design notes
```

## 3. API endpoints

| Method | Path | Body / Params | Response |
|---|---|---|---|
| `POST` | `/documents` | `multipart/form-data`, field `file` (PDF) | `{ id, name, pages, chunks }` |
| `GET` | `/documents` | none | `[{ id, name, pages, chunks, uploaded_at }]` |
| `POST` | `/ask` | `{ "question": str, "document_ids"?: [uuid] }` | see below |
| `GET` | `/health` | none | `{ "status": "ok" }` |

`POST /ask` response:

```json
{
  "answer": "The warranty period is 24 months. [1]",
  "citations": [
    { "index": 1, "document": "warranty.pdf", "page": 3, "snippet": "...24 months from the date..." }
  ],
  "refused": false
}
```

Example curl for M1:

```bash
curl -F "file=@eval/sample_docs/handbook.pdf" http://localhost:8000/documents
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "How many vacation days do new employees get?"}'
```

## 4. How citations work

1. **At ingest**, `pypdf` yields text page by page. Chunks are word windows (600 words with a
   75 word overlap, roughly 800 tokens and 100 tokens) so no tokenizer dependency is needed.
   Each chunk is created *within* a page (never across pages), so every chunk row stores `document_id`, `document_name`,
   `page_number`, `chunk_index`, `text`, `embedding`.
2. **At query time**, the top-k chunks are numbered `[1]..[k]` and placed in the prompt as
   `[1] (handbook.pdf, p.12) <text>`.
3. The system prompt instructs the model to answer **only** from the numbered sources and to
   append the bracket number(s) it used after each claim.
4. The backend parses the `[n]` markers out of the answer and returns only the cited chunks as
   `citations` (document name, page, snippet). Uncited retrieved chunks are dropped. The snippet
   is the sentence of the chunk that shares the most keywords with the question (plural and
   singular forms match), capped at 300 characters, so the chip shows the relevant line rather
   than the top of the page.
5. The UI renders citations as clickable chips under the answer showing `document · page N`.

## 5. Refusal rule

The bot must not guess. Two layers enforce this:

- **Prompt layer.** The system prompt says: *"If the sources do not contain the answer, reply
  exactly: `I don't have that in the documents`."*
- **Code layer.** Before calling the LLM, if the best cosine similarity is below a threshold,
  skip the LLM and return the refusal directly. Tuned once with a throwaway script that printed the
  best retrieval similarity per eval question (removed after use). On the 30 question set, answerable
  questions scored 0.45 to 0.75 and unanswerable ones 0.03 to 0.60. Near-topic unanswerable questions
  (other agencies' leave rules, paid parental leave) score higher than some answerable ones, so the
  threshold cannot separate the groups. It is set to `0.35`, which catches clearly off-topic questions
  cheaply and leaves a margin below the weakest answerable question. The prompt layer does the real
  refusing and scored 9 of 9 on the eval set.
  After the LLM call, if the answer contains the refusal sentence or cites no sources, the
  response is normalised to `answer = "I don't have that in the documents"`,
  `citations = []`, `refused = true`.

The eval set includes questions whose answers are **not** in the documents, so the refusal
rate is measured, not assumed.

## 6. Evaluation

- `eval/questions.json`: 30 items (20 direct, 3 paraphrased, 3 needing two pages, 4 unanswerable
  but close to the handbook topic):
  ```json
  { "id": 1, "question": "...", "expected_answer": "...", "expected_document": "handbook.pdf",
    "expected_pages": [12], "type": "answerable", "group": "base" }
  ```
  21 `answerable` and 9 `unanswerable` (expected answer is the refusal string). Two-page questions
  list both pages and need both cited to count.
- `eval/run_eval.py`: for each question calls `POST /ask`, then scores:
  - **Answer correctness**: `gpt-4o-mini` as judge (`temperature=0`), answering yes only if every
    fact in the expected answer is present. A lenient "conveys the answer" prompt was found to pass
    partial answers and was replaced. For `unanswerable` items, correct means the bot refused.
  - **Citation accuracy**: every expected page of the expected document appears in the citations.
  - Prints a per-question table plus overall **answer accuracy**, **citation accuracy** and
    **refusal accuracy**, and writes `eval/results.md`.
- Target for the README: >= 85% answer accuracy, >= 80% citation accuracy, 5/5 refusals.

## 7. Milestones

| # | Deliverable | Done when |
|---|---|---|
| **M1** | Backend: Postgres+pgvector in Docker, `POST /documents`, `POST /ask`, `GET /documents`, citations + refusal rule, unit tests | Both curl commands above return correct JSON with citations |
| **M2** | `eval/` folder, 20 questions, `run_eval.py`, `results.md` | Script runs end-to-end and prints accuracy; results committed |
| **M3** | Next.js UI: upload dropzone, document list, chat with citation chips, refusal styling | Full flow works in the browser against the local backend |
| **M4** | `docker-compose.yml` for db + backend + frontend, README with setup, architecture diagram, eval results and demo GIF | `docker compose up` on a clean machine brings up the whole stack |

M4 notes: the frontend image is a two-stage build using Next.js `output: "standalone"`. The browser
calls the backend directly, so `NEXT_PUBLIC_API_URL` is a build argument (default
`http://localhost:8000`) and is baked into the client bundle. Compose starts db, backend and frontend
in order using health checks. The architecture diagram is Mermaid in the README so GitHub renders it
without an image file. The demo GIF is assembled from Playwright screenshots with Pillow.

## 8. Out of scope (for now)

Auth, multi-user tenancy, streaming responses, OCR for scanned PDFs, reranking. Listed in the
README as possible extensions.
