from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.models import ImportResult
from app.repository import Repository


class IngestionService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def import_file(self, file_path: str) -> ImportResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        if path.suffix.lower() == ".csv":
            frame = pd.read_csv(path)
        elif path.suffix.lower() in {".xlsx", ".xls"}:
            frame = pd.read_excel(path)
        else:
            raise ValueError("Only .csv, .xls, and .xlsx files are supported.")

        imported = 0
        skipped = 0
        details: list[str] = []
        for index, row in frame.iterrows():
            title = str(row.get("title", "")).strip()
            notes = str(row.get("notes_on_outline_before", "")).strip()
            if not title or not notes or notes.lower() == "nan":
                skipped += 1
                details.append(f"Row {index + 2}: missing required title or notes_on_outline_before.")
                continue
            self.repository.create_book(title=title, notes_on_outline_before=notes)
            imported += 1

        return ImportResult(imported=imported, skipped=skipped, details=details)
