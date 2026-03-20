from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.models import (
    BookCreate,
    BookRecord,
    ChapterRecord,
    ChapterReviewUpdate,
    CompilationResult,
    FinalReviewUpdate,
    GenerateResponse,
    ImportResult,
    OutlineReviewUpdate,
)
from app.repository import build_repository
from app.services.exports import ExportService
from app.services.ingestion import IngestionService
from app.services.llm import LLMService
from app.services.notifications import NotificationService
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/api", tags=["books"])


def get_workflow_service(settings: Settings = Depends(get_settings)) -> WorkflowService:
    repository = build_repository(settings)
    return WorkflowService(
        repository=repository,
        llm_service=LLMService(settings),
        notification_service=NotificationService(settings),
        export_service=ExportService(settings),
    )


def get_ingestion_service(settings: Settings = Depends(get_settings)) -> IngestionService:
    repository = build_repository(settings)
    return IngestionService(repository=repository)


class ImportRequest(BaseModel):
    file_path: str


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/books", response_model=BookRecord)
def create_book(payload: BookCreate, workflow: WorkflowService = Depends(get_workflow_service)) -> BookRecord:
    return workflow.create_book(payload.title, payload.notes_on_outline_before)


@router.get("/books", response_model=list[BookRecord])
def list_books(workflow: WorkflowService = Depends(get_workflow_service)) -> list[BookRecord]:
    return workflow.list_books()


@router.get("/books/{book_id}", response_model=BookRecord)
def get_book(book_id: str, workflow: WorkflowService = Depends(get_workflow_service)) -> BookRecord:
    return workflow.get_book(book_id)


@router.get("/books/{book_id}/chapters", response_model=list[ChapterRecord])
def list_book_chapters(
    book_id: str,
    workflow: WorkflowService = Depends(get_workflow_service),
) -> list[ChapterRecord]:
    return workflow.list_chapters(book_id)


@router.post("/books/import", response_model=ImportResult)
def import_books(payload: ImportRequest, ingestion: IngestionService = Depends(get_ingestion_service)) -> ImportResult:
    return ingestion.import_file(payload.file_path)


@router.post("/books/{book_id}/generate-outline", response_model=BookRecord)
def generate_outline(book_id: str, workflow: WorkflowService = Depends(get_workflow_service)) -> BookRecord:
    return workflow.generate_outline(book_id)


@router.post("/books/{book_id}/review-outline", response_model=BookRecord)
def review_outline(
    book_id: str,
    payload: OutlineReviewUpdate,
    workflow: WorkflowService = Depends(get_workflow_service),
) -> BookRecord:
    return workflow.review_outline(book_id, payload.status_outline_notes, payload.notes_on_outline_after)


@router.get("/books/{book_id}/review-outline", response_model=GenerateResponse)
def review_outline_help(
    book_id: str,
    workflow: WorkflowService = Depends(get_workflow_service),
) -> GenerateResponse:
    book = workflow.get_book(book_id)
    return GenerateResponse(
        message=(
            'Use POST on this endpoint with a JSON body like '
            '{"status_outline_notes":"no_notes_needed","notes_on_outline_after":null}. '
            f'Current book status is "{book.book_output_status}".'
        ),
        status=book.book_output_status,
    )


@router.post("/books/{book_id}/generate-next-chapter", response_model=ChapterRecord)
def generate_next_chapter(book_id: str, workflow: WorkflowService = Depends(get_workflow_service)) -> ChapterRecord:
    return workflow.generate_next_chapter(book_id)


@router.post("/chapters/{chapter_id}/review", response_model=ChapterRecord)
def review_chapter(
    chapter_id: str,
    payload: ChapterReviewUpdate,
    workflow: WorkflowService = Depends(get_workflow_service),
) -> ChapterRecord:
    return workflow.review_chapter(chapter_id, payload.chapter_notes_status, payload.chapter_notes)


@router.get("/chapters/{chapter_id}/review", response_model=GenerateResponse)
def review_chapter_help(
    chapter_id: str,
    workflow: WorkflowService = Depends(get_workflow_service),
) -> GenerateResponse:
    return GenerateResponse(
        message=(
            'Use POST on this endpoint with a JSON body like '
            '{"chapter_notes_status":"no_notes_needed","chapter_notes":null}. '
            f'Chapter id is "{chapter_id}".'
        ),
        status="post_required",
    )


@router.post("/books/{book_id}/final-review", response_model=BookRecord)
def final_review(
    book_id: str,
    payload: FinalReviewUpdate,
    workflow: WorkflowService = Depends(get_workflow_service),
) -> BookRecord:
    return workflow.update_final_review(book_id, payload.final_review_notes_status, payload.final_review_notes)


@router.get("/books/{book_id}/final-review", response_model=GenerateResponse)
def final_review_help(
    book_id: str,
    workflow: WorkflowService = Depends(get_workflow_service),
) -> GenerateResponse:
    book = workflow.get_book(book_id)
    return GenerateResponse(
        message=(
            'Use POST on this endpoint with a JSON body like '
            '{"final_review_notes_status":"no_notes_needed","final_review_notes":null}. '
            f'Current book status is "{book.book_output_status}".'
        ),
        status=book.book_output_status,
    )


@router.post("/books/{book_id}/compile", response_model=CompilationResult)
def compile_book(book_id: str, workflow: WorkflowService = Depends(get_workflow_service)) -> CompilationResult:
    txt_path, docx_path = workflow.compile_book(book_id)
    return CompilationResult(txt_path=txt_path, docx_path=docx_path)


@router.get("/books/{book_id}/compile", response_model=GenerateResponse)
def compile_book_help(book_id: str, workflow: WorkflowService = Depends(get_workflow_service)) -> GenerateResponse:
    book = workflow.get_book(book_id)
    return GenerateResponse(
        message=(
            "Use POST on this endpoint after all chapters are approved and final review is complete. "
            f'Current book status is "{book.book_output_status}".'
        ),
        status=book.book_output_status,
    )


@router.post("/books/{book_id}/resume", response_model=GenerateResponse)
def resume_book(book_id: str, workflow: WorkflowService = Depends(get_workflow_service)) -> GenerateResponse:
    book = workflow.get_book(book_id)
    return GenerateResponse(
        message=f'Book "{book.title}" is currently at status "{book.book_output_status}".',
        status=book.book_output_status,
    )


@router.get("/books/{book_id}/resume", response_model=GenerateResponse)
def resume_book_help(book_id: str, workflow: WorkflowService = Depends(get_workflow_service)) -> GenerateResponse:
    book = workflow.get_book(book_id)
    return GenerateResponse(
        message=f'Book "{book.title}" is currently at status "{book.book_output_status}".',
        status=book.book_output_status,
    )
