from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Protocol

from supabase import Client, create_client
from postgrest.exceptions import APIError

from app.config import Settings
from app.models import BookRecord, BookStatus, ChapterRecord


class Repository(Protocol):
    def create_book(self, title: str, notes_on_outline_before: str) -> BookRecord: ...
    def get_book(self, book_id: str) -> BookRecord: ...
    def list_books(self) -> list[BookRecord]: ...
    def update_book(self, book_id: str, updates: dict[str, Any]) -> BookRecord: ...
    def replace_chapters(self, book_id: str, chapter_titles: list[str]) -> list[ChapterRecord]: ...
    def list_chapters(self, book_id: str) -> list[ChapterRecord]: ...
    def get_next_chapter(self, book_id: str) -> ChapterRecord | None: ...
    def update_chapter(self, chapter_id: str, updates: dict[str, Any]) -> ChapterRecord: ...


class RepositoryError(Exception):
    pass


class SupabaseRepository:
    def __init__(self, settings: Settings):
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)

    def create_book(self, title: str, notes_on_outline_before: str) -> BookRecord:
        book_id = str(uuid.uuid4())
        payload = {
            "id": book_id,
            "title": title,
            "notes_on_outline_before": notes_on_outline_before,
            "book_output_status": BookStatus.draft.value,
        }
        self.client.table("books").insert(payload).execute()
        return self.get_book(book_id)

    def get_book(self, book_id: str) -> BookRecord:
        response = self.client.table("books").select("*").eq("id", book_id).single().execute()
        return BookRecord.model_validate(response.data)

    def list_books(self) -> list[BookRecord]:
        try:
            response = self.client.table("books").select("*").order("created_at").execute()
        except APIError as exc:
            if "created_at" not in str(exc):
                raise
            response = self.client.table("books").select("*").execute()
        return [BookRecord.model_validate(item) for item in response.data or []]

    def update_book(self, book_id: str, updates: dict[str, Any]) -> BookRecord:
        self.client.table("books").update(updates).eq("id", book_id).execute()
        return self.get_book(book_id)

    def replace_chapters(self, book_id: str, chapter_titles: list[str]) -> list[ChapterRecord]:
        self.client.table("chapters").delete().eq("book_id", book_id).execute()
        payload = [
            {
                "id": str(uuid.uuid4()),
                "book_id": book_id,
                "chapter_number": index,
                "chapter_title": chapter_title,
                "status": "pending",
            }
            for index, chapter_title in enumerate(chapter_titles, start=1)
        ]
        if payload:
            self.client.table("chapters").insert(payload).execute()
        return self.list_chapters(book_id)

    def list_chapters(self, book_id: str) -> list[ChapterRecord]:
        try:
            response = (
                self.client.table("chapters")
                .select("*")
                .eq("book_id", book_id)
                .order("chapter_number")
                .execute()
            )
        except APIError as exc:
            if "chapter_number" not in str(exc):
                raise
            response = self.client.table("chapters").select("*").eq("book_id", book_id).execute()
        return [ChapterRecord.model_validate(item) for item in response.data or []]

    def get_next_chapter(self, book_id: str) -> ChapterRecord | None:
        chapters = self.list_chapters(book_id)
        for chapter in chapters:
            if chapter.status != "approved":
                return chapter
        return None

    def update_chapter(self, chapter_id: str, updates: dict[str, Any]) -> ChapterRecord:
        self.client.table("chapters").update(updates).eq("id", chapter_id).execute()
        response = self.client.table("chapters").select("*").eq("id", chapter_id).single().execute()
        return ChapterRecord.model_validate(response.data)


class LocalJSONRepository:
    def __init__(self, settings: Settings):
        self.root = settings.data_dir
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "books.json"
        if not self.path.exists():
            self._write({"books": [], "chapters": []})

    def create_book(self, title: str, notes_on_outline_before: str) -> BookRecord:
        state = self._read()
        record = {
            "id": str(uuid.uuid4()),
            "title": title,
            "notes_on_outline_before": notes_on_outline_before,
            "outline": None,
            "outline_structure": [],
            "notes_on_outline_after": None,
            "status_outline_notes": None,
            "final_review_notes_status": None,
            "final_review_notes": None,
            "book_output_status": BookStatus.draft.value,
            "compiled_txt_path": None,
            "compiled_docx_path": None,
            "metadata": {},
        }
        state["books"].append(record)
        self._write(state)
        return BookRecord.model_validate(record)

    def get_book(self, book_id: str) -> BookRecord:
        state = self._read()
        for record in state["books"]:
            if record["id"] == book_id:
                return BookRecord.model_validate(record)
        raise RepositoryError(f"Book not found: {book_id}")

    def list_books(self) -> list[BookRecord]:
        state = self._read()
        return [BookRecord.model_validate(record) for record in state["books"]]

    def update_book(self, book_id: str, updates: dict[str, Any]) -> BookRecord:
        state = self._read()
        for record in state["books"]:
            if record["id"] == book_id:
                record.update(updates)
                self._write(state)
                return BookRecord.model_validate(record)
        raise RepositoryError(f"Book not found: {book_id}")

    def replace_chapters(self, book_id: str, chapter_titles: list[str]) -> list[ChapterRecord]:
        state = self._read()
        state["chapters"] = [chapter for chapter in state["chapters"] if chapter["book_id"] != book_id]
        for index, chapter_title in enumerate(chapter_titles, start=1):
            state["chapters"].append(
                {
                    "id": str(uuid.uuid4()),
                    "book_id": book_id,
                    "chapter_number": index,
                    "chapter_title": chapter_title,
                    "content": None,
                    "summary": None,
                    "chapter_notes_status": None,
                    "chapter_notes": None,
                    "status": "pending",
                }
            )
        self._write(state)
        return self.list_chapters(book_id)

    def list_chapters(self, book_id: str) -> list[ChapterRecord]:
        state = self._read()
        chapters = [chapter for chapter in state["chapters"] if chapter["book_id"] == book_id]
        chapters.sort(key=lambda item: item["chapter_number"])
        return [ChapterRecord.model_validate(chapter) for chapter in chapters]

    def get_next_chapter(self, book_id: str) -> ChapterRecord | None:
        for chapter in self.list_chapters(book_id):
            if chapter.status != "approved":
                return chapter
        return None

    def update_chapter(self, chapter_id: str, updates: dict[str, Any]) -> ChapterRecord:
        state = self._read()
        for chapter in state["chapters"]:
            if chapter["id"] == chapter_id:
                chapter.update(updates)
                self._write(state)
                return ChapterRecord.model_validate(chapter)
        raise RepositoryError(f"Chapter not found: {chapter_id}")

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_repository(settings: Settings) -> Repository:
    if settings.force_local_storage:
        return LocalJSONRepository(settings)
    if settings.supabase_url and settings.supabase_key:
        return SupabaseRepository(settings)
    return LocalJSONRepository(settings)
