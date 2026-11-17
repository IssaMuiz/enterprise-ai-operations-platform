from app.modules.documents.cleaner import clean_document, clean_text
from app.modules.documents.entities import Document, DocumentPage


def create_mock_pdf_document(pages: list[str]):

    return Document(
        filename="report.pdf",
        file_type="pdf",
        file_size=2,
        pages=[
            DocumentPage(content=page, page_number=page_number)
            for page_number, page in enumerate(pages, start=1)
        ],
    )


def create_mock_text_document(text: str):

    lines = text.splitlines()

    return Document(
        filename="report.txt",
        file_type="txt",
        file_size=2,
        pages=[DocumentPage(content=text, start_line=1, end_line=len(lines))],
    )


def test_clean_text_normalises_window_line_ending():
    text = "First line\r\nSecond line\r\nThird line"

    result = clean_text(text)

    assert result == "First line\nSecond line\nThird line"


def test_clean_text_normalises_old_mac_line_ending():
    text = "First line\rSecond line\rThird line"

    result = clean_text(text)

    assert result == "First line\nSecond line\nThird line"


def test_clean_text_surrounding_white_space():
    text = "       surrounding white space        "

    result = clean_text(text)

    assert result == "surrounding white space"


def test_text_right_white_space_with_new_line():

    text = "first line     \nsecond line       "

    result = clean_text(text)

    assert result == "first line\nsecond line"


def test_text_with_multiple_lines():

    text = "first line\n\n\n\n\n\n\nsecond line"

    result = clean_text(text)

    assert result == "first line\n\nsecond line"


def test_clean_pdf_document():
    document = create_mock_pdf_document(
        [
            "page 1\r\nfirst line",
            "     page 2     \nfirst line",
            "page 3\n\n\n\n\nfirst line",
        ]
    )

    result = clean_document(document)

    assert result.filename == "report.pdf"
    assert result.file_size == 2
    assert result.file_type == "pdf"
    assert len(result.pages) == 3
    assert [page.page_number for page in result.pages] == [1, 2, 3]
    assert result.pages[0].content == "page 1\nfirst line"
    assert result.pages[1].content == "page 2\nfirst line"
    assert result.pages[2].content == "page 3\n\nfirst line"


def test_unchanged_original_document():
    document = create_mock_pdf_document(["page 1\r\n", "page 2    ", "page 3"])

    result = clean_document(document)

    assert [page.content for page in result.pages] == ["page 1", "page 2", "page 3"]
    assert [page.content for page in document.pages] == [
        "page 1\r\n",
        "page 2    ",
        "page 3",
    ]
    assert result is not document
    assert all(
        original_page is not cleaned_page
        for original_page, cleaned_page in zip(
            document.pages, result.pages, strict=False
        )
    )


def test_document_with_empty_pages():
    document = create_mock_pdf_document(["", "", ""])

    result = clean_document(document)

    assert [page.content for page in result.pages] == ["", "", ""]
    assert [page.page_number for page in result.pages] == [1, 2, 3]


def test_document_with_no_pages():
    document = create_mock_pdf_document([])

    result = clean_document(document)

    assert result.pages == []


def test_clean_txt_document():
    document = create_mock_text_document(
        "first line\r\nsecond line\rthird line    \n\n\n\n\n\nfourth line"
    )

    result = clean_document(document)

    assert result.filename == "report.txt"
    assert result.pages[0].start_line == 1
    assert result.pages[0].end_line == 9
    assert (
        result.pages[0].content == "first line\nsecond line\nthird line\n\nfourth line"
    )
