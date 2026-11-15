from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentPage:
    content: str
    page_number: int | None = None
    start_line: int | None = None
    end_line: int | None = None


@dataclass(frozen=True)
class Document:
    filename: str
    file_type: str
    file_size: int
    pages: list[DocumentPage] = field(default_factory=list)
