from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class TextSpan:
    text: str
    font: str | None = None
    font_size: float | None = None
    flags: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    start_offset: int | None = None
    end_offset: int | None = None


@dataclass(frozen=True)
class DocumentPage:
    content: str
    page_number: int | None = None
    start_line: int | None = None
    end_line: int | None = None
    spans: list[TextSpan] = field(default_factory=list)


@dataclass(frozen=True)
class Document:
    filename: str
    file_type: str
    file_size: int
    metadata: dict[str, str | None] = field(default_factory=dict)
    pages: list[DocumentPage] = field(default_factory=list)

    @property
    def page_count(self):
        return len(self.pages)


@dataclass(frozen=True)
class DocumentElement:
    element_type: Literal["heading", "paragraph"]
    content: str
    level: int | None = None
    spans: list[TextSpan] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedPage:
    page_number: int | None
    elements: list[DocumentElement]


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    file_type: str
    file_size: int
    metadata: dict[str, str | None] = field(default_factory=dict)
    pages: list[ParsedPage] = field(default_factory=list)

    @property
    def page_count(self):
        return len(self.pages)


@dataclass(frozen=True)
class DocumentChunk:
    content: str
    chunk_index: int
    filename: str
    file_type: str
    page_number: int | None = None
    section_heading: str | None = None
    metadata: dict[str, str | None] = field(default_factory=dict)
    source_element_types: tuple[Literal["heading", "paragraph"], ...] = ()


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: DocumentChunk
    vector: tuple[float, ...]
    model: str


@dataclass(frozen=True)
class DocumentProcessingResult:
    document: Document
    parsed_document: ParsedDocument
    chunks: list[DocumentChunk] = field(default_factory=list)
    embedded_chunks: list[EmbeddedChunk] = field(default_factory=list)
