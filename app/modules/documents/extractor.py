from pathlib import Path

import pymupdf

from .entities import DocumentPage, TextSpan


class DocumentExtractionError(Exception):
    """raise when the document extraction fail"""

    pass


def extract_text_span(page: pymupdf.Page) -> list[TextSpan]:
    spans = []

    blocks = page.get_text("dict")["blocks"]

    for block in blocks:
        if "lines" not in block:
            continue

        for lines in block["lines"]:
            for span in lines["spans"]:
                text = span["text"]

                if not text.strip():
                    continue

                spans.append(
                    TextSpan(
                        text=text,
                        font=span.get("font"),
                        font_size=span.get("size"),
                        flags=span.get("flags"),
                        bbox=span.get("bbox"),
                    )
                )

    return spans


def extract_document_pages(filename: str, content: bytes) -> list[DocumentPage]:

    if not isinstance(filename, str):
        raise TypeError("Invalid filename type")

    if not isinstance(content, bytes):
        raise TypeError("file content must be in bytes format")

    filename = filename.strip()

    if not filename:
        raise ValueError("Invalid filename")

    extension = Path(filename).suffix.lower()

    if extension not in {".pdf", ".txt"}:
        raise ValueError("Invalid file format")

    if extension == ".pdf":
        try:
            pages = []
            with pymupdf.open(stream=content, filetype="pdf") as document:
                for page_number, page in enumerate(document, start=1):
                    text_span = extract_text_span(page)
                    page_text = page.get_text("text")
                    pages.append(
                        DocumentPage(
                            content=page_text, page_number=page_number, spans=text_span
                        )
                    )

            return pages

        except pymupdf.FileDataError as exc:
            raise DocumentExtractionError("PDF extraction failed") from exc

    elif extension == ".txt":
        try:
            text = content.decode("utf-8")

            if text == "":
                return []

            lines = text.splitlines()

            pages = []

            pages.append(DocumentPage(content=text, start_line=1, end_line=len(lines)))

            return pages
        except UnicodeDecodeError as exc:
            raise DocumentExtractionError("Text extraction failed") from exc
