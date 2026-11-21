import pytest

from app.modules.documents.entities import (
    Document,
    DocumentPage,
    ParsedDocument,
    TextSpan,
)
from app.modules.documents.parser import parse_document, parse_page


def make_span(
    content: str,
    text: str,
    *,
    font_size: float | None = None,
    font: str | None = None,
    flags: int | None = None,
    start_at: int = 0,
) -> TextSpan:
    start_offset = content.index(text, start_at)
    return TextSpan(
        text=text,
        font=font,
        font_size=font_size,
        flags=flags,
        start_offset=start_offset,
        end_offset=start_offset + len(text),
    )


def make_document(
    *,
    file_type: str,
    pages: list[DocumentPage],
    metadata: dict[str, str | None] | None = None,
) -> Document:
    return Document(
        filename="report." + file_type.lower().lstrip("."),
        file_type=file_type,
        file_size=128,
        metadata=metadata or {"title": "Quarterly report"},
        pages=pages,
    )


def test_parse_txt_splits_paragraphs_on_blank_lines():
    page = DocumentPage(
        content="First paragraph, line one.\nFirst paragraph, line two.\n\n\nSecond paragraph.\n"
    )

    result = parse_document(make_document(file_type="txt", pages=[page]))

    assert isinstance(result, ParsedDocument)
    assert [element.element_type for element in result.pages[0].elements] == [
        "paragraph",
        "paragraph",
    ]
    assert [element.content for element in result.pages[0].elements] == [
        "First paragraph, line one.\nFirst paragraph, line two.",
        "Second paragraph.",
    ]
    assert all(element.level is None for element in result.pages[0].elements)


def test_parse_txt_does_not_infer_headings_from_bold_or_font_spans():
    content = "A large styled line\n\nA regular paragraph."
    page = DocumentPage(
        content=content,
        spans=[
            make_span(content, "A large styled line", font_size=28, flags=16),
            make_span(content, "A regular paragraph.", font_size=10, start_at=20),
        ],
    )

    result = parse_document(make_document(file_type="txt", pages=[page]))

    assert [element.element_type for element in result.pages[0].elements] == [
        "paragraph",
        "paragraph",
    ]


def test_parse_pdf_detects_larger_font_heading_and_associates_spans_by_offsets():
    content = "Annual Report\nRevenue increased this year."
    title_span = make_span(content, "Annual Report", font_size=20)
    body_span = make_span(
        content, "Revenue increased this year.", font_size=10, start_at=14
    )
    page = DocumentPage(
        content=content,
        page_number=3,
        spans=[title_span, body_span],
    )

    result = parse_document(make_document(file_type="pdf", pages=[page]))

    parsed_page = result.pages[0]
    assert parsed_page.page_number == 3
    assert [
        (element.element_type, element.content) for element in parsed_page.elements
    ] == [
        ("heading", "Annual Report"),
        ("paragraph", "Revenue increased this year."),
    ]
    assert parsed_page.elements[0].level is None
    assert parsed_page.elements[0].spans == [title_span]
    assert parsed_page.elements[1].spans == [body_span]


def test_parse_pdf_detects_bold_heading_without_font_size_difference():
    content = "Overview\nThis is the explanatory paragraph."
    heading_span = make_span(
        content, "Overview", font_size=12, font="Arial-Bold", flags=16
    )
    body_span = make_span(
        content,
        "This is the explanatory paragraph.",
        font_size=12,
        font="Arial",
        flags=0,
        start_at=9,
    )
    page = DocumentPage(content=content, spans=[heading_span, body_span])

    parsed_page = parse_page(page, "pdf")

    assert [element.element_type for element in parsed_page.elements] == [
        "heading",
        "paragraph",
    ]
    assert parsed_page.elements[0].spans == [heading_span]
    assert parsed_page.elements[1].spans == [body_span]


def test_parse_pdf_uses_font_flags_to_detect_bold_heading():
    content = "Summary\nThe report contains detailed results."
    heading_span = make_span(content, "Summary", font_size=12, flags=16)
    body_span = make_span(
        content,
        "The report contains detailed results.",
        font_size=12,
        flags=0,
        start_at=8,
    )
    page = DocumentPage(content=content, spans=[heading_span, body_span])

    parsed_page = parse_page(page, "pdf")

    assert parsed_page.elements[0].element_type == "heading"


def test_parse_pdf_keeps_regular_text_as_paragraph_when_no_heading_signal_exists():
    content = "A normal line of text.\nAnother normal line."
    page = DocumentPage(
        content=content,
        spans=[
            make_span(content, "A normal line of text.", font_size=11),
            make_span(content, "Another normal line.", font_size=11, start_at=23),
        ],
    )

    parsed_page = parse_page(page, "pdf")

    assert len(parsed_page.elements) == 1
    assert parsed_page.elements[0].element_type == "paragraph"
    assert (
        parsed_page.elements[0].content
        == "A normal line of text.\nAnother normal line."
    )


def test_parse_pdf_groups_adjacent_heading_lines():
    content = "Annual\nResults\nThe details follow."
    page = DocumentPage(
        content=content,
        spans=[
            make_span(content, "Annual", font_size=20),
            make_span(content, "Results", font_size=20, start_at=7),
            make_span(content, "The details follow.", font_size=10, start_at=15),
        ],
    )

    parsed_page = parse_page(page, "pdf")

    assert [
        (element.element_type, element.content) for element in parsed_page.elements
    ] == [
        ("heading", "Annual\nResults"),
        ("paragraph", "The details follow."),
    ]


def test_parse_pdf_does_not_treat_long_bold_body_line_as_heading():
    content = "Bold body content " * 8
    page = DocumentPage(
        content=content,
        spans=[make_span(content, content, font_size=12, flags=16)],
    )

    parsed_page = parse_page(page, "pdf")

    assert parsed_page.elements[0].element_type == "paragraph"


def test_parse_pdf_associates_spans_by_text_when_offsets_are_missing():
    content = "Policy\nThe policy applies to all employees."
    heading_span = TextSpan(text="Policy", font_size=20)
    body_span = TextSpan(text="The policy applies to all employees.", font_size=10)
    page = DocumentPage(content=content, spans=[heading_span, body_span])

    parsed_page = parse_page(page, "pdf")

    assert parsed_page.elements[0].spans == [heading_span]
    assert parsed_page.elements[1].spans == [body_span]


def test_parse_pdf_falls_back_to_text_matching_when_offsets_do_not_overlap():
    content = "Policy\nThe policy applies to all employees."
    heading_span = TextSpan(
        text="Policy", font_size=20, start_offset=500, end_offset=506
    )
    body_span = TextSpan(
        text="The policy applies to all employees.",
        font_size=10,
        start_offset=600,
        end_offset=636,
    )
    page = DocumentPage(content=content, spans=[heading_span, body_span])

    parsed_page = parse_page(page, "pdf")

    assert parsed_page.elements[0].spans == [heading_span]
    assert parsed_page.elements[1].spans == [body_span]


def test_parse_pdf_does_not_misclassify_mixed_style_line_as_bold_heading():
    content = "Important policy text"
    regular_span = make_span(content, "Important ", font_size=12, flags=0)
    bold_span = make_span(content, "policy text", font_size=12, flags=16, start_at=10)
    page = DocumentPage(content=content, spans=[regular_span, bold_span])

    parsed_page = parse_page(page, "pdf")

    assert parsed_page.elements[0].element_type == "paragraph"


def test_parse_document_preserves_document_and_page_metadata():
    metadata = {"title": "Quarterly report", "author": "Example"}
    page = DocumentPage(content="A paragraph.", page_number=4)
    document = make_document(file_type="PDF", pages=[page], metadata=metadata)

    result = parse_document(document)

    assert result.filename == document.filename
    assert result.file_type == "PDF"
    assert result.file_size == document.file_size
    assert result.metadata == metadata
    assert result.metadata is not metadata
    assert result.page_count == 1
    assert result.pages[0].page_number == 4
    assert document.pages == [page]


def test_parse_document_preserves_page_order_and_empty_pages():
    pages = [
        DocumentPage(content="First page.", page_number=1),
        DocumentPage(content="\n \n", page_number=2),
        DocumentPage(content="Third page.", page_number=3),
    ]

    result = parse_document(make_document(file_type="txt", pages=pages))

    assert result.page_count == 3
    assert [page.page_number for page in result.pages] == [1, 2, 3]
    assert result.pages[1].elements == []
    assert result.pages[0].elements[0].content == "First page."
    assert result.pages[2].elements[0].content == "Third page."


def test_parse_document_with_no_pages_returns_empty_parsed_document():
    result = parse_document(make_document(file_type="txt", pages=[]))

    assert result.pages == []
    assert result.page_count == 0


def test_parse_document_rejects_non_document_input():
    with pytest.raises(TypeError, match="document must be a Document"):
        parse_document("report.pdf")  # type: ignore[arg-type]


def test_parse_page_rejects_non_page_input():
    with pytest.raises(TypeError, match="page must be a DocumentPage"):
        parse_page("not a page", "pdf")  # type: ignore[arg-type]
