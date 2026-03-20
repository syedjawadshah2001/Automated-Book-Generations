create extension if not exists "pgcrypto";

create table if not exists public.books (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    notes_on_outline_before text not null,
    outline text,
    outline_structure jsonb not null default '[]'::jsonb,
    notes_on_outline_after text,
    status_outline_notes text,
    final_review_notes_status text,
    final_review_notes text,
    book_output_status text not null default 'draft',
    compiled_txt_path text,
    compiled_docx_path text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.chapters (
    id uuid primary key default gen_random_uuid(),
    book_id uuid not null references public.books(id) on delete cascade,
    chapter_number integer not null,
    chapter_title text not null,
    content text,
    summary text,
    chapter_notes_status text,
    chapter_notes text,
    status text not null default 'pending',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (book_id, chapter_number)
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists books_set_updated_at on public.books;
create trigger books_set_updated_at
before update on public.books
for each row
execute function public.set_updated_at();

drop trigger if exists chapters_set_updated_at on public.chapters;
create trigger chapters_set_updated_at
before update on public.chapters
for each row
execute function public.set_updated_at();
