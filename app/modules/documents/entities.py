from dataclasses import dataclass, field


@dataclass(frozen=True)
class TextSpan:
    text: str
    font: str | None = None
    font_size: float | None = None
    flags: int | None = None
    bbox: tuple[float, float, float, float] | None = None


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
