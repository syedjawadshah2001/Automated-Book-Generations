from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NotesStatus(str, Enum):
    yes = "yes"
    no = "no"
    no_notes_needed = "no_notes_needed"


class BookStatus(str, Enum):
    draft = "draft"
    outline_ready = "outline_ready"
    outline_waiting_notes = "outline_waiting_notes"
    outline_paused = "outline_paused"
    chapters_in_progress = "chapters_in_progress"
    chapter_waiting_notes = "chapter_waiting_notes"
    chapter_paused = "chapter_paused"
    ready_for_compile = "ready_for_compile"
    compiled = "compiled"
    error = "error"


class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    notes_on_outline_before: str = Field(min_length=1)


class OutlineReviewUpdate(BaseModel):
    status_outline_notes: NotesStatus
    notes_on_outline_after: str | None = None


class ChapterReviewUpdate(BaseModel):
    chapter_notes_status: NotesStatus
    chapter_notes: str | None = None


class FinalReviewUpdate(BaseModel):
    final_review_notes_status: NotesStatus
    final_review_notes: str | None = None


class ImportResult(BaseModel):
    imported: int
    skipped: int
    details: list[str] = Field(default_factory=list)


class BookRecord(BaseModel):
    id: str
    title: str
    notes_on_outline_before: str
    outline: str | None = None
    outline_structure: list[str] = Field(default_factory=list)
    notes_on_outline_after: str | None = None
    status_outline_notes: NotesStatus | None = None
    final_review_notes_status: NotesStatus | None = None
    final_review_notes: str | None = None
    book_output_status: BookStatus = BookStatus.draft
    compiled_txt_path: str | None = None
    compiled_docx_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChapterRecord(BaseModel):
    id: str
    book_id: str
    chapter_number: int
    chapter_title: str
    content: str | None = None
    summary: str | None = None
    chapter_notes_status: NotesStatus | None = None
    chapter_notes: str | None = None
    status: str = "pending"


class GenerateResponse(BaseModel):
    message: str
    status: str


class CompilationResult(BaseModel):
    txt_path: str
    docx_path: str
