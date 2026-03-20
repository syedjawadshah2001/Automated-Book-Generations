def outline_prompt(title: str, notes_before: str, notes_after: str | None = None) -> str:
    revision_clause = ""
    if notes_after:
        revision_clause = (
            "\nRevise the previous outline by applying these editor notes:\n"
            f"{notes_after}\n"
        )
    return f"""
You are helping draft a book called "{title}".

Use the mandatory editor notes below when creating the outline:
{notes_before}
{revision_clause}

Return:
1. A concise book positioning summary.
2. A numbered chapter outline.
3. A one-line purpose statement for each chapter.

Keep the outline practical and coherent across the full book.
""".strip()


def chapter_prompt(
    title: str,
    outline: str,
    chapter_title: str,
    chapter_number: int,
    previous_summaries: str,
    chapter_notes: str | None = None,
) -> str:
    notes_block = f"\nEditor chapter notes:\n{chapter_notes}\n" if chapter_notes else ""
    return f"""
Write Chapter {chapter_number}: "{chapter_title}" for the book "{title}".

Book outline:
{outline}

Summaries of previous chapters:
{previous_summaries or "No previous chapters yet."}
{notes_block}
Requirements:
- Maintain continuity with prior chapters.
- Write with clear section breaks.
- End with a short takeaway.
- Keep the chapter useful and publication-ready.
""".strip()


def summary_prompt(title: str, chapter_title: str, chapter_content: str) -> str:
    return f"""
Summarize the following chapter from the book "{title}" titled "{chapter_title}".

Return a compact summary that preserves the important context needed for later chapters.

Chapter content:
{chapter_content}
""".strip()
