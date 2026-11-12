import pytest

from app.modules.documents.validator import validate_document


def test_valid_document():
    file_name = "book.pdf"
    file_size = 1
    file_max_size = 2

    result = validate_document(
        filename=file_name, file_size=file_size, max_size_bytes=file_max_size
    )

    assert result is None


def test_valid_document_with_leading_whitespace():
    file_name = "  book.pdf"
    file_size = 1
    file_max_size = 2

    result = validate_document(
        filename=file_name, file_size=file_size, max_size_bytes=file_max_size
    )

    assert result is None


@pytest.mark.parametrize("filename", ["  ", ""])
def test_empty_filename(filename):
    with pytest.raises(ValueError):
        validate_document(filename=filename, file_size=1, max_size_bytes=2)


@pytest.mark.parametrize("filename", [123, None, []])
def test_invalid_filename_type(filename):
    with pytest.raises(TypeError):
        validate_document(filename=filename, file_size=1, max_size_bytes=2)


@pytest.mark.parametrize("filename", ["book.pdf", "bood.txt", "book.PDF", "book.TXT"])
def test_valid_document_extension(filename):
    result = validate_document(filename=filename, file_size=1, max_size_bytes=2)

    assert result is None


@pytest.mark.parametrize("filename", ["book.csv", "book.xlsx", "book.docx"])
def test_invalid_file_extension(filename):
    with pytest.raises(ValueError):
        validate_document(filename=filename, file_size=1, max_size_bytes=2)


@pytest.mark.parametrize("file_size", [0, -1, 5])
def test_invalid_file_size(file_size):

    with pytest.raises(ValueError):
        validate_document(filename="book.pdf", file_size=file_size, max_size_bytes=2)


@pytest.mark.parametrize("file_size", ["1", True, 1.3])
def test_invalid_file_size_type(file_size):
    with pytest.raises(TypeError):
        validate_document(filename="book.pdf", file_size=file_size, max_size_bytes=2)


def test_file_size_at_maximum():
    result = validate_document(filename="book.pdf", file_size=2, max_size_bytes=2)

    assert result is None


@pytest.mark.parametrize("max_size_bytes", ["1", True, 1.5])
def test_invalid_max_size_bytes_type(max_size_bytes):
    with pytest.raises(TypeError):
        validate_document(
            filename="book.pdf", file_size=1, max_size_bytes=max_size_bytes
        )


@pytest.mark.parametrize("max_size_bytes", [0, -1])
def test_invalid_max_size_bytes(max_size_bytes):
    with pytest.raises(ValueError):
        validate_document(
            filename="book.pdf", file_size=1, max_size_bytes=max_size_bytes
        )
