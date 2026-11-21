import pytest

from app.modules.documents.chunker import chunk_document
from app.modules.documents.entities import (
    DocumentChunk,
    DocumentElement,
    ParsedDocument,
    ParsedPage,
)


def make_parsed_document(
    pages: list[ParsedPage],
    *,
    metadata: dict[str, str | None] | None = None,
) -> ParsedDocument:
    return ParsedDocument(
        filename="report.pdf",
        file_type="pdf",
        file_size=256,
        metadata=metadata if metadata is not None else {"department": "finance"},
        pages=pages,
    )


def heading(content: str) -> DocumentElement:
    return DocumentElement(element_type="heading", content=content)


def paragraph(content: str) -> DocumentElement:
    return DocumentElement(element_type="paragraph", content=content)


def test_chunk_document_groups_paragraphs_and_repeats_section_heading():
    document = make_parsed_document(
        [
            ParsedPage(
                page_number=2,
                elements=[
                    heading("Revenue"),
                    paragraph("Revenue increased during the quarter."),
                    paragraph("Growth was strongest in the enterprise segment."),
                ],
            )
        ]
    )

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].content == (
        "Revenue\nRevenue increased during the quarter.\n\n"
        "Growth was strongest in the enterprise segment."
    )
    assert chunks[0].section_heading == "Revenue"
    assert chunks[0].source_element_types == ("heading", "paragraph", "paragraph")
    assert chunks[0].page_number == 2


def test_chunk_document_keeps_paragraphs_before_first_heading():
    document = make_parsed_document(
        [
            ParsedPage(
                page_number=1,
                elements=[
                    paragraph("Introduction."),
                    heading("Details"),
                    paragraph("More."),
                ],
            )
        ]
    )

    chunks = chunk_document(document)

    assert [chunk.content for chunk in chunks] == ["Introduction.", "Details\nMore."]
    assert [chunk.section_heading for chunk in chunks] == [None, "Details"]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1]


def test_chunk_document_starts_new_section_at_each_heading():
    document = make_parsed_document(
        [
            ParsedPage(
                page_number=1,
                elements=[
                    heading("First"),
                    paragraph("First section text."),
                    heading("Second"),
                    paragraph("Second section text."),
                ],
            )
        ]
    )

    chunks = chunk_document(document)

    assert [chunk.content for chunk in chunks] == [
        "First\nFirst section text.",
        "Second\nSecond section text.",
    ]
    assert [chunk.section_heading for chunk in chunks] == ["First", "Second"]


def test_chunk_document_emits_heading_without_following_paragraphs():
    document = make_parsed_document(
        [ParsedPage(page_number=1, elements=[heading("Appendix")])]
    )

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].content == "Appendix"
    assert chunks[0].section_heading == "Appendix"
    assert chunks[0].source_element_types == ("heading",)


def test_chunk_document_splits_long_paragraph_with_requested_overlap():
    content = "abcdefghijklmnopqrstuvwxyz" * 3
    document = make_parsed_document(
        [ParsedPage(page_number=1, elements=[paragraph(content)])]
    )

    chunks = chunk_document(document, max_chars=30, overlap=10)

    assert len(chunks) == 4
    assert all(len(chunk.content) <= 30 for chunk in chunks)
    assert chunks[0].content[20:] == chunks[1].content[:10]
    assert chunks[1].content[20:] == chunks[2].content[:10]
    assert chunks[2].content[20:] == chunks[3].content[:10]


def test_chunk_document_splits_at_word_boundaries_when_possible():
    content = "alpha beta gamma delta epsilon zeta eta theta"
    document = make_parsed_document(
        [ParsedPage(page_number=1, elements=[paragraph(content)])]
    )

    chunks = chunk_document(document, max_chars=20, overlap=0)

    assert len(chunks) > 1
    assert all(len(chunk.content) <= 20 for chunk in chunks)
    assert all(not chunk.content.startswith(" ") for chunk in chunks)
    assert all(not chunk.content.endswith(" ") for chunk in chunks)
    assert " ".join(chunk.content for chunk in chunks) == content


def test_chunk_document_hard_splits_a_word_longer_than_the_limit():
    long_word = "x" * 25
    document = make_parsed_document(
        [ParsedPage(page_number=1, elements=[paragraph(long_word)])]
    )

    chunks = chunk_document(document, max_chars=10, overlap=0)

    assert [chunk.content for chunk in chunks] == ["x" * 10, "x" * 10, "x" * 5]
    assert all(len(chunk.content) <= 10 for chunk in chunks)


def test_chunk_document_respects_limit_including_heading_prefix():
    document = make_parsed_document(
        [
            ParsedPage(
                page_number=1,
                elements=[heading("Title"), paragraph("abcdefghijklmno")],
            )
        ]
    )

    chunks = chunk_document(document, max_chars=12, overlap=2)

    assert all(len(chunk.content) <= 12 for chunk in chunks)
    assert all(chunk.content.startswith("Title\n") for chunk in chunks)
    assert all(chunk.section_heading == "Title" for chunk in chunks)


def test_chunk_document_splits_long_heading_section_without_exceeding_limit():
    title = "A heading longer than the configured chunk size"
    document = make_parsed_document(
        [ParsedPage(page_number=1, elements=[heading(title), paragraph("Body text.")])]
    )

    chunks = chunk_document(document, max_chars=12, overlap=2)

    assert len(chunks) > 1
    assert all(len(chunk.content) <= 12 for chunk in chunks)
    assert all(chunk.section_heading == title for chunk in chunks)


def test_chunk_document_never_combines_pages_and_indexes_globally():
    document = make_parsed_document(
        [
            ParsedPage(page_number=1, elements=[paragraph("Page one.")]),
            ParsedPage(page_number=2, elements=[paragraph("Page two.")]),
        ]
    )

    chunks = chunk_document(document)

    assert [chunk.page_number for chunk in chunks] == [1, 2]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert [chunk.content for chunk in chunks] == ["Page one.", "Page two."]


def test_chunk_document_copies_metadata_to_each_chunk():
    metadata = {"department": "finance"}
    document = make_parsed_document(
        [
            ParsedPage(
                page_number=1,
                elements=[paragraph("First."), paragraph("Second.")],
            )
        ],
        metadata=metadata,
    )

    chunks = chunk_document(document, max_chars=8, overlap=0)

    assert len(chunks) == 2
    assert all(chunk.metadata == metadata for chunk in chunks)
    assert all(chunk.metadata is not metadata for chunk in chunks)
    assert chunks[0].metadata is not chunks[1].metadata


def test_chunk_document_returns_no_chunks_for_empty_document_or_pages():
    empty_document = make_parsed_document([])
    empty_page_document = make_parsed_document([ParsedPage(page_number=1, elements=[])])

    assert chunk_document(empty_document) == []
    assert chunk_document(empty_page_document) == []


@pytest.mark.parametrize("max_chars", [0, -1])
def test_chunk_document_rejects_non_positive_max_chars(max_chars):
    document = make_parsed_document([])

    with pytest.raises(ValueError, match="max_chars must be greater than zero"):
        chunk_document(document, max_chars=max_chars)


@pytest.mark.parametrize("overlap", [-1])
def test_chunk_document_rejects_negative_overlap(overlap):
    document = make_parsed_document([])

    with pytest.raises(ValueError, match="overlap cannot be negative"):
        chunk_document(document, overlap=overlap)


def test_chunk_document_rejects_overlap_equal_to_or_larger_than_max_chars():
    document = make_parsed_document([])

    with pytest.raises(ValueError, match="overlap must be smaller than max_chars"):
        chunk_document(document, max_chars=10, overlap=10)


@pytest.mark.parametrize("max_chars", ["100", True, 1.5])
def test_chunk_document_rejects_invalid_max_chars_type(max_chars):
    document = make_parsed_document([])

    with pytest.raises(TypeError, match="max_chars must be an integer"):
        chunk_document(document, max_chars=max_chars)


@pytest.mark.parametrize("overlap", ["10", True, 1.5])
def test_chunk_document_rejects_invalid_overlap_type(overlap):
    document = make_parsed_document([])

    with pytest.raises(TypeError, match="overlap must be an integer"):
        chunk_document(document, overlap=overlap)


def test_chunk_document_rejects_non_parsed_document():
    with pytest.raises(TypeError, match="document must be a ParsedDocument"):
        chunk_document("not a parsed document")  # type: ignore[arg-type]


def test_chunk_metadata_includes_document_source_fields():
    document = make_parsed_document(
        [ParsedPage(page_number=7, elements=[paragraph("Source text.")])]
    )

    chunk = chunk_document(document)[0]

    assert isinstance(chunk, DocumentChunk)
    assert chunk.filename == document.filename
    assert chunk.file_type == document.file_type
    assert chunk.page_number == 7
    assert chunk.chunk_index == 0
