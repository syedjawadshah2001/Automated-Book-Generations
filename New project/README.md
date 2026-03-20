# Automated Book Generation System

This project is a starter backend for a modular book-generation workflow built with FastAPI. It supports:

- title intake from API or local CSV/XLSX
- outline generation with pre/post-note gating
- chapter-by-chapter generation with cumulative summary context
- final draft compilation to `.txt` and `.docx`
- Supabase-ready persistence and notification hooks
- local JSON persistence fallback for offline development

## Stack

- Backend API: FastAPI
- Workflow orchestration: Python service layer
- Database: Supabase via `supabase-py`
- Local dev fallback: JSON file store
- AI model: Gemini or OpenAI adapter
- Input: local `.csv` / `.xlsx`
- Notifications: console, SMTP email, or MS Teams webhook
- Output: `.txt` and `.docx`

## Run locally

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your credentials.
4. Start the server:

```bash
uvicorn app.main:app --reload
```

For a fully local demo, set `FORCE_LOCAL_STORAGE=true` in `.env`.

## Architecture notes

- `WorkflowService` owns the gating logic for outline, chapters, and final compilation.
- `Repository` is pluggable:
  - `SupabaseRepository` is the main production path.
  - `LocalJSONRepository` keeps the project runnable offline for evaluation.
- `LLMService` supports Gemini or OpenAI and falls back to deterministic mock output when the remote API is unavailable.
- Chapter context chaining is handled by storing a summary per chapter and concatenating prior summaries before generating the next chapter.

## Main endpoints

- `GET /api/health`
- `POST /api/books`
- `GET /api/books`
- `GET /api/books/{book_id}`
- `GET /api/books/{book_id}/chapters`
- `POST /api/books/import`
- `POST /api/books/{book_id}/generate-outline`
- `POST /api/books/{book_id}/review-outline`
- `POST /api/books/{book_id}/generate-next-chapter`
- `POST /api/chapters/{chapter_id}/review`
- `POST /api/books/{book_id}/final-review`
- `POST /api/books/{book_id}/compile`
