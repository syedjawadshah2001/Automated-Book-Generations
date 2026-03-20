# Demo Guide

This guide gives you a clean end-to-end flow for Swagger, Loom, and interview explanation.

## What The Project Does

This is a modular FastAPI backend that automates book generation in stages:

1. Create a book from a title and required pre-outline notes
2. Generate an outline with an LLM
3. Pause or continue based on editor review
4. Generate chapters one by one
5. Use previous chapter summaries as context for the next chapter
6. Pause or continue based on chapter review
7. Compile the approved draft into `.txt` and `.docx`

## Main Features

- FastAPI + Swagger/OpenAPI testing interface
- Supabase-ready storage with local JSON fallback
- Gemini or OpenAI LLM adapter
- Review gating for outline and chapters
- Chapter summary context chaining
- CSV/XLSX import support
- Notification hooks for console, SMTP, or Teams
- `.txt` and `.docx` export

## Recommended Demo Mode

For the most reliable Loom demo:

- Keep `LLM_PROVIDER=gemini` if your Gemini key works
- If Supabase is unstable, clear `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- The app will use local JSON storage in `data/books.json`

That still demonstrates the workflow cleanly.

## Start The Server

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Open:

- Swagger UI: http://127.0.0.1:8002/docs
- OpenAPI JSON: http://127.0.0.1:8002/openapi.json

## Swagger Demo Flow

### 1. Health Check

Use `GET /api/health`

Expected response:

```json
{
  "status": "ok"
}
```

### 2. Create A Book

Use `POST /api/books`

```json
{
  "title": "AI Automation for Small Businesses",
  "notes_on_outline_before": "Create a practical beginner-friendly five chapter book with clear examples, real business use cases, and implementation advice."
}
```

Copy the returned `id`.

### 3. Generate Outline

Use `POST /api/books/{book_id}/generate-outline`

This creates:

- the book outline
- the chapter titles
- chapter placeholder rows

### 4. Show Chapters

Use `GET /api/books/{book_id}/chapters`

This is a good screen to show in Loom because it proves chapter records are stored separately.

### 5. Review Outline

Use `POST /api/books/{book_id}/review-outline`

For quick progress:

```json
{
  "status_outline_notes": "no_notes_needed",
  "notes_on_outline_after": null
}
```

Optional regeneration example:

```json
{
  "status_outline_notes": "yes",
  "notes_on_outline_after": "Add a chapter about common automation mistakes and make the tone more implementation-focused."
}
```

### 6. Generate Next Chapter

Use `POST /api/books/{book_id}/generate-next-chapter`

This writes:

- chapter content
- chapter summary
- review status

### 7. Review Chapter

Use `POST /api/chapters/{chapter_id}/review`

Quick approval:

```json
{
  "chapter_notes_status": "no_notes_needed",
  "chapter_notes": null
}
```

Optional regeneration:

```json
{
  "chapter_notes_status": "yes",
  "chapter_notes": "Add one real-world example and end with a stronger practical takeaway."
}
```

### 8. Repeat Chapter Flow

Repeat:

- `POST /api/books/{book_id}/generate-next-chapter`
- `POST /api/chapters/{chapter_id}/review`

Do this until all chapters are approved.

### 9. Final Review

Use `POST /api/books/{book_id}/final-review`

```json
{
  "final_review_notes_status": "no_notes_needed",
  "final_review_notes": null
}
```

### 10. Compile Book

Use `POST /api/books/{book_id}/compile`

Expected response includes:

- `txt_path`
- `docx_path`

Generated files are saved in the `exports` folder.

## What To Show In Loom

1. Swagger docs
2. Health endpoint working
3. Create book request
4. Generate outline request
5. Stored chapters via `GET /api/books/{book_id}/chapters`
6. Generate chapter request
7. Review chapter request
8. Final review request
9. Compile request
10. Output files in `exports`
11. Data in Supabase or `data/books.json`

## How To Explain Supabase

If Supabase is connected:

- show the `books` table
- show the `chapters` table
- explain that `books` stores workflow-level state
- explain that `chapters` stores each chapter, review status, notes, and summary

If you use local fallback:

- open `data/books.json`
- explain that it is the offline fallback for the same workflow model
- point to `supabase/schema.sql` as the production table design

## How To Explain OpenAPI

- FastAPI automatically generates OpenAPI
- `/docs` is the Swagger UI
- `/openapi.json` is the machine-readable OpenAPI schema
- this lets reviewers test every stage without a frontend

## Short Interview Explanation

This project is a modular backend for automated book generation. It takes a title and required outline notes, generates an outline with an LLM, stores it for review, then generates chapters one by one while carrying forward summaries of previous chapters for context continuity. At each stage, editor feedback can pause, regenerate, or approve the workflow. After all chapters are approved, the system compiles the final manuscript into exportable files. The storage layer is designed for Supabase and includes a local fallback so the workflow remains demoable even if external services are unavailable.
