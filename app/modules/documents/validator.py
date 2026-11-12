from pathlib import Path


def validate_document(filename: str, file_size: int, max_size_bytes: int) -> None:
    if not isinstance(filename, str):
        raise TypeError("Expected a string as the file name")

    if type(file_size) is not int:
        raise TypeError("Expected an integer as the file size")

    if type(max_size_bytes) is not int:
        raise TypeError("Expected an integer as the maximum file size")

    filename = filename.strip()

    if not filename:
        raise ValueError("Invalid file name")

    extension = Path(filename).suffix.lower()

    if extension not in {".pdf", ".txt"}:
        raise ValueError("Unsupported file format")

    if file_size <= 0:
        raise ValueError("File size should be greater zero")

    if max_size_bytes <= 0:
        raise ValueError("Maximum file size musy be greater than zero")

    if file_size > max_size_bytes:
        raise ValueError("File size exceed the maximum allowed size")
