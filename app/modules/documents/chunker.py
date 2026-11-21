from typing import Literal

from .entities import DocumentChunk, ParsedDocument, ParsedPage


def chunk_document(
    document: ParsedDocument,
    max_chars: int = 1500,
    overlap: int = 200,
) -> list[DocumentChunk]:
    """Split parsed pages into character-bounded chunks for downstream retrieval."""
    if not isinstance(document, ParsedDocument):
        raise TypeError("document must be a ParsedDocument")
    if type(max_chars) is not int:
        raise TypeError("max_chars must be an integer")
    if type(overlap) is not int:
        raise TypeError("overlap must be an integer")
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")

    chunks: list[DocumentChunk] = []
    for page in document.pages:
        for heading, paragraphs, element_types in _sections(page):
            chunks.extend(
                _chunk_section(
                    document=document,
                    page=page,
                    heading=heading,
                    paragraphs=paragraphs,
                    element_types=element_types,
                    max_chars=max_chars,
                    overlap=overlap,
                    first_index=len(chunks),
                )
            )
    return chunks


def _sections(
    page: ParsedPage,
) -> list[tuple[str | None, list[str], tuple[Literal["heading", "paragraph"], ...]]]:
    sections = []
    heading = None
    paragraphs: list[str] = []
    element_types: list[Literal["heading", "paragraph"]] = []

    def flush() -> None:
        if heading is not None or paragraphs:
            sections.append((heading, paragraphs.copy(), tuple(element_types)))

    for element in page.elements:
        if element.element_type == "heading":
            flush()
            heading = element.content.strip()
            paragraphs = []
            element_types = ["heading"]
            continue

        paragraph = element.content.strip()
        if paragraph:
            paragraphs.append(paragraph)
            element_types.append("paragraph")

    flush()
    return sections


def _chunk_section(
    *,
    document: ParsedDocument,
    page: ParsedPage,
    heading: str | None,
    paragraphs: list[str],
    element_types: tuple[Literal["heading", "paragraph"], ...],
    max_chars: int,
    overlap: int,
    first_index: int,
) -> list[DocumentChunk]:
    body = "\n\n".join(paragraphs).strip()

    if not body and heading is not None:
        body = heading
        prefix = ""
    elif heading:
        prefix = f"{heading}\n"
    else:
        prefix = ""

    if len(prefix) >= max_chars:
        # An unusually long heading cannot be repeated as a prefix while
        # keeping chunks within the requested limit; split the section text.
        section_text = f"{heading}\n\n{body}" if body else heading or ""
        contents = _split_text(section_text, max_chars, overlap)
    else:
        body_limit = max_chars - len(prefix)
        body_overlap = min(overlap, body_limit - 1)
        contents = [
            prefix + part for part in _split_text(body, body_limit, body_overlap)
        ]

    return [
        DocumentChunk(
            content=content,
            chunk_index=first_index + index,
            filename=document.filename,
            file_type=document.file_type,
            page_number=page.page_number,
            section_heading=heading,
            metadata=dict(document.metadata),
            source_element_types=element_types,
        )
        for index, content in enumerate(contents)
        if content.strip()
    ]


def _split_text(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split text near word boundaries, falling back to hard cuts for long words."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + 1, end)
            if boundary > start:
                end = boundary

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break

        next_start = max(start + 1, end - overlap)
        next_word = text.find(" ", next_start, end)
        if next_word >= 0:
            next_start = next_word + 1
        start = next_start

    return chunks
