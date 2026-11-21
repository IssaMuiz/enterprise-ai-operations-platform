import re

from .entities import (
    Document,
    DocumentElement,
    DocumentPage,
    ParsedDocument,
    ParsedPage,
    TextSpan,
)

_BOLD_FLAG = 16
_HEADING_SIZE_RATIO = 1.15
_MAX_BOLD_HEADING_LENGTH = 120


def parse_document(document: Document) -> ParsedDocument:
    """Parse a cleaned document into heading and paragraph elements.

    PDF headings are inferred from span font size or bold styling. TXT documents
    have no layout information, so their non-empty blocks are paragraphs.
    """
    if not isinstance(document, Document):
        raise TypeError("document must be a Document")

    pages = [parse_page(page, document.file_type) for page in document.pages]
    return ParsedDocument(
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        metadata=dict(document.metadata),
        pages=pages,
    )


def parse_page(page: DocumentPage, file_type: str) -> ParsedPage:
    """Split one page into non-empty paragraphs and inferred PDF headings."""
    if not isinstance(page, DocumentPage):
        raise TypeError("page must be a DocumentPage")

    is_pdf = file_type.lower().lstrip(".") == "pdf"
    elements: list[DocumentElement] = []
    current_lines: list[tuple[str, tuple[TextSpan, ...]]] = []
    current_heading: bool | None = None
    sizes = [
        span.font_size
        for span in page.spans
        if span.font_size is not None and span.font_size > 0
    ]
    typical_size = sorted(sizes)[(len(sizes) - 1) // 4] if sizes else None

    def flush() -> None:
        if not current_lines or current_heading is None:
            return
        spans = _unique_spans(
            span for _, line_spans in current_lines for span in line_spans
        )
        elements.append(
            DocumentElement(
                element_type="heading" if current_heading else "paragraph",
                content="\n".join(content for content, _ in current_lines),
                level=None,
                spans=spans,
            )
        )

    offset = 0
    for raw_with_ending in page.content.splitlines(keepends=True):
        raw_line = raw_with_ending.rstrip("\r\n")
        content = raw_line.strip()
        line_start = offset
        line_end = offset + len(raw_line)
        offset += len(raw_with_ending)
        if not content:
            flush()
            current_lines.clear()
            current_heading = None
            continue

        line_spans = _spans_for_line(page, raw_line, line_start, line_end)
        heading = _is_heading(content, line_spans, typical_size) if is_pdf else False
        if current_lines and heading != current_heading:
            flush()
            current_lines.clear()
        current_lines.append((content, line_spans))
        current_heading = heading

    flush()
    return ParsedPage(page_number=page.page_number, elements=elements)


def _is_heading(
    content: str,
    spans: tuple[TextSpan, ...],
    typical_size: float | None = None,
) -> bool:
    if not spans:
        return False

    if typical_size is not None:
        large_text_length = sum(
            len(span.text.strip())
            for span in spans
            if span.font_size is not None
            and span.font_size >= typical_size * _HEADING_SIZE_RATIO
        )
        if large_text_length >= len(content) * 0.5:
            return True

    is_bold = all(
        bool((span.flags or 0) & _BOLD_FLAG)
        or "bold" in (span.font or "").lower()
        for span in spans
    )
    return is_bold and len(content) <= _MAX_BOLD_HEADING_LENGTH


def _spans_for_line(
    page: DocumentPage, line: str, line_start: int, line_end: int
) -> tuple[TextSpan, ...]:
    """Associate spans to a text line using offsets, then text as a fallback."""
    matches = []

    for span in page.spans:
        if (
            span.start_offset is not None
            and span.end_offset is not None
            and span.start_offset < line_end
            and span.end_offset > line_start
        ):
            matches.append(span)
            continue

        normalized_span = re.sub(r"\s+", " ", span.text).strip()
        normalized_line = re.sub(r"\s+", " ", line).strip()
        if normalized_span and normalized_span in normalized_line:
            matches.append(span)

    return tuple(matches)


def _unique_spans(spans) -> list[TextSpan]:
    result = []
    seen = set()
    for span in spans:
        identity = id(span)
        if identity not in seen:
            result.append(span)
            seen.add(identity)
    return result
