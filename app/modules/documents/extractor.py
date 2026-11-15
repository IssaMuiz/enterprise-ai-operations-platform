from pathlib import Path

import pymupdf

from .entities import DocumentPage


class DocumentExtractionError(Exception):
    """raise when the document extraction fail"""

    pass


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
                    page_text = page.get_text("text")
                    pages.append(
                        DocumentPage(content=page_text, page_number=page_number)
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
