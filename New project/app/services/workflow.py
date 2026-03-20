from __future__ import annotations

import re

from fastapi import HTTPException

from app.models import BookRecord, BookStatus, ChapterRecord, NotesStatus
from app.prompts import chapter_prompt, outline_prompt, summary_prompt
from app.repository import Repository
from app.services.exports import ExportService
from app.services.llm import LLMService
from app.services.notifications import NotificationService


class WorkflowService:
    def __init__(
        self,
        repository: Repository,
        llm_service: LLMService,
        notification_service: NotificationService,
        export_service: ExportService,
    ):
        self.repository = repository
        self.llm_service = llm_service
        self.notification_service = notification_service
        self.export_service = export_service

    def create_book(self, title: str, notes_on_outline_before: str) -> BookRecord:
        return self.repository.create_book(title, notes_on_outline_before)

    def list_books(self) -> list[BookRecord]:
        return self.repository.list_books()

    def get_book(self, book_id: str) -> BookRecord:
        return self.repository.get_book(book_id)

    def list_chapters(self, book_id: str) -> list[ChapterRecord]:
        return self.repository.list_chapters(book_id)

    def generate_outline(self, book_id: str) -> BookRecord:
        book = self.repository.get_book(book_id)
        if not book.notes_on_outline_before.strip():
            raise HTTPException(status_code=400, detail="notes_on_outline_before is required before outline generation.")

        prompt = outline_prompt(book.title, book.notes_on_outline_before, book.notes_on_outline_after)
        outline = self.llm_service.generate(prompt)
        chapters = self._extract_chapter_titles(outline)
        updated = self.repository.update_book(
            book_id,
            {
                "outline": outline,
                "outline_structure": chapters,
                "book_output_status": BookStatus.outline_ready.value,
            },
        )
        self.repository.replace_chapters(book_id, chapters)
        self.notification_service.send(
            subject="Outline ready for review",
            message=f'Outline generated for "{book.title}". Editor review is now required.',
        )
        return updated

    def review_outline(self, book_id: str, status: NotesStatus, notes: str | None) -> BookRecord:
        current_status = BookStatus.outline_paused
        if status == NotesStatus.yes:
            if not notes:
                current_status = BookStatus.outline_waiting_notes
            else:
                current_status = BookStatus.outline_ready
        elif status == NotesStatus.no_notes_needed:
            current_status = BookStatus.chapters_in_progress

        updated = self.repository.update_book(
            book_id,
            {
                "status_outline_notes": status.value,
                "notes_on_outline_after": notes,
                "book_output_status": current_status.value,
            },
        )

        if status == NotesStatus.yes and notes:
            return self.generate_outline(book_id)

        return updated

    def generate_next_chapter(self, book_id: str) -> ChapterRecord:
        book = self.repository.get_book(book_id)
        if book.status_outline_notes not in {NotesStatus.no_notes_needed, NotesStatus.yes, "no_notes_needed", "yes"}:
            raise HTTPException(status_code=400, detail="Outline review must be completed before chapter generation.")

        chapter = self.repository.get_next_chapter(book_id)
        if not chapter:
            self.repository.update_book(book_id, {"book_output_status": BookStatus.ready_for_compile.value})
            raise HTTPException(status_code=400, detail="All chapters are already complete.")

        if chapter.chapter_notes_status in {NotesStatus.no.value, "no"} or (
            chapter.chapter_notes_status is None and chapter.status == "waiting_review"
        ):
            raise HTTPException(status_code=400, detail="Chapter is paused until review status changes.")

        chapters = self.repository.list_chapters(book_id)
        previous_summaries = "\n".join(
            f"Chapter {item.chapter_number}: {item.summary}"
            for item in chapters
            if item.chapter_number < chapter.chapter_number and item.summary
        )
        content = self.llm_service.generate(
            chapter_prompt(
                title=book.title,
                outline=book.outline or "",
                chapter_title=chapter.chapter_title,
                chapter_number=chapter.chapter_number,
                previous_summaries=previous_summaries,
                chapter_notes=chapter.chapter_notes,
            )
        )
        summary = self.llm_service.generate(summary_prompt(book.title, chapter.chapter_title, content))

        updated = self.repository.update_chapter(
            chapter.id,
            {
                "content": content,
                "summary": summary,
                "status": "waiting_review",
            },
        )
        self.repository.update_book(book_id, {"book_output_status": BookStatus.chapter_waiting_notes.value})
        self.notification_service.send(
            subject="Chapter ready for review",
            message=f'Chapter {chapter.chapter_number} for "{book.title}" is ready and waiting for notes.',
        )
        return updated

    def review_chapter(self, chapter_id: str, status: NotesStatus, notes: str | None) -> ChapterRecord:
        current_status = "paused"
        if status == NotesStatus.yes:
            current_status = "waiting_regeneration" if notes else "waiting_notes"
        elif status == NotesStatus.no_notes_needed:
            current_status = "approved"

        chapter = self.repository.update_chapter(
            chapter_id,
            {
                "chapter_notes_status": status.value,
                "chapter_notes": notes,
                "status": current_status,
            },
        )

        if status == NotesStatus.yes and notes:
            book = self.repository.get_book(chapter.book_id)
            chapters = self.repository.list_chapters(chapter.book_id)
            previous_summaries = "\n".join(
                f"Chapter {item.chapter_number}: {item.summary}"
                for item in chapters
                if item.chapter_number < chapter.chapter_number and item.summary
            )
            content = self.llm_service.generate(
                chapter_prompt(
                    title=book.title,
                    outline=book.outline or "",
                    chapter_title=chapter.chapter_title,
                    chapter_number=chapter.chapter_number,
                    previous_summaries=previous_summaries,
                    chapter_notes=notes,
                )
            )
            summary = self.llm_service.generate(summary_prompt(book.title, chapter.chapter_title, content))
            chapter = self.repository.update_chapter(
                chapter.id,
                {
                    "content": content,
                    "summary": summary,
                    "status": "waiting_review",
                },
            )
        return chapter

    def compile_book(self, book_id: str) -> tuple[str, str]:
        book = self.repository.get_book(book_id)
        chapters = self.repository.list_chapters(book_id)
        if not chapters or any(chapter.status != "approved" for chapter in chapters):
            raise HTTPException(status_code=400, detail="All chapters must be approved before compilation.")

        allowed = book.final_review_notes_status in {NotesStatus.no_notes_needed, "no_notes_needed"} or bool(book.final_review_notes)
        if not allowed:
            raise HTTPException(status_code=400, detail="Final review is incomplete.")

        txt_path, docx_path = self.export_service.export(book, chapters)
        self.repository.update_book(
            book_id,
            {
                "compiled_txt_path": txt_path,
                "compiled_docx_path": docx_path,
                "book_output_status": BookStatus.compiled.value,
            },
        )
        self.notification_service.send(
            subject="Final draft compiled",
            message=f'Final draft for "{book.title}" was exported successfully.',
        )
        return txt_path, docx_path

    def update_final_review(self, book_id: str, status: NotesStatus, notes: str | None) -> BookRecord:
        output_status = BookStatus.ready_for_compile if status == NotesStatus.no_notes_needed or notes else BookStatus.chapter_paused
        return self.repository.update_book(
            book_id,
            {
                "final_review_notes_status": status.value,
                "final_review_notes": notes,
                "book_output_status": output_status.value,
            },
        )

    @staticmethod
    def _extract_chapter_titles(outline: str) -> list[str]:
        chapter_titles: list[str] = []
        for line in outline.splitlines():
            match = re.match(r"^\s*(\d+)[\.\)]\s+(.*)$", line.strip())
            if match:
                title = match.group(2).split(" - ")[0].strip()
                if title:
                    chapter_titles.append(title)
        return chapter_titles or ["Introduction", "Core Concepts", "Applied Workflow", "Advanced Practice", "Conclusion"]
