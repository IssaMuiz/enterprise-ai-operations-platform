import pymupdf
import pytest

from app.modules.documents.entities import DocumentPage
from app.modules.documents.extractor import (
    DocumentExtractionError,
    extract_document_pages,
)

content = b"Hello! Enterprise ai platform"


def tmp_pdf_doc(pages: list[str]) -> bytes:

    with pymupdf.open() as document:
        for text in pages:
            page = document.new_page()
            page.insert_text((72, 72), text)

        return document.tobytes()


@pytest.mark.parametrize("filename", [23444, 1.223, True])
def test_invalid_filename_type(filename):

    with pytest.raises(TypeError):
        extract_document_pages(filename=filename, content=content)


def test_empty_filename():

    with pytest.raises(ValueError):
        extract_document_pages(filename="  ", content=content)


@pytest.mark.parametrize("content", [123, "hello", 34.34, True])
def test_invalid_content_type(content):
    with pytest.raises(TypeError):
        extract_document_pages(filename="policy.pdf", content=content)


@pytest.mark.parametrize("filename", ["policy.xlsx", "policy.csv", "policy.yml"])
def test_invalid_file_extension(filename):
    with pytest.raises(ValueError):
        extract_document_pages(filename=filename, content=content)


def test_pdf_file_text_extractor():
    content = tmp_pdf_doc(["page 1", "page 2", "page 3"])

    result = extract_document_pages(filename="report.pdf", content=content)

    assert isinstance(result, list)
    assert isinstance(result[0], DocumentPage)
    assert result[0].content == "page 1\n"
    assert [page.page_number for page in result] == [1, 2, 3]
    assert len(result) == 3


def test_pdf_file_text_span_extractor():
    content = tmp_pdf_doc(["This is a text file"])

    result = extract_document_pages(filename="report.pdf", content=content)

    assert result[0].spans[0].text == "This is a text file"
    assert result[0].spans[0].font is not None
    assert result[0].spans[0].font_size is not None
    assert result[0].spans[0].flags is not None
    assert result[0].spans[0].bbox is not None


def test_malformed_pdf_file():

    text = b"An invalid pdf text file"

    with pytest.raises(DocumentExtractionError):
        extract_document_pages(filename="broken_file.pdf", content=text)


def test_txt_file_text_extractor():

    text = b"This is a text\n The second line"

    result = extract_document_pages(filename="enquiry.txt", content=text)

    assert isinstance(result[0], DocumentPage)
    assert result[0].start_line == 1
    assert result[0].content == "This is a text\n The second line"
    assert result[0].end_line == 2
    assert len(result) == 1


def test_extracting_empty_txt_file():

    text = b""

    result = extract_document_pages(filename="enquiry.txt", content=text)

    assert result == []


def test_invalid_utf8_txt():

    content = b"\xff\xfe\xfa"

    with pytest.raises(DocumentExtractionError):
        extract_document_pages(filename="broken.txt", content=content)
