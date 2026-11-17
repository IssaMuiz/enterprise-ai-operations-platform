import re

from .entities import Document, DocumentPage


def clean_text(text: str) -> str:

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = "\n".join(line.rstrip() for line in text.split("\n"))

    text = text.strip()

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def clean_document(document: Document) -> Document:

    cleaned_pages = [
        DocumentPage(
            content=clean_text(page.content),
            page_number=page.page_number,
            start_line=page.start_line,
            end_line=page.end_line,
        )
        for page in document.pages
    ]

    return Document(
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        pages=cleaned_pages,
    )
