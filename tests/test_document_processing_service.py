import pytest

from app.modules.documents.entities import EmbeddedChunk
from app.modules.documents.extractor import DocumentExtractionError
from app.modules.documents.service import DocumentProcessingService


class FakeEmbeddingProvider:
    model = "fake-model"

    def __init__(self):
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[float(len(text)), 0.5] for text in texts]


def make_service(
    provider: FakeEmbeddingProvider | None = None,
    *,
    max_file_size_bytes: int = 1_000,
) -> tuple[DocumentProcessingService, FakeEmbeddingProvider]:
    embedding_provider = provider or FakeEmbeddingProvider()
    return (
        DocumentProcessingService(
            embedding_provider=embedding_provider,
            max_file_size_bytes=max_file_size_bytes,
        ),
        embedding_provider,
    )


def test_process_runs_txt_through_clean_parse_chunk_and_embed_stages():
    service, provider = make_service()
    content = b"  First paragraph.  \r\n\r\n\r\nSecond paragraph.  "
    metadata = {"department": "finance"}

    result = service.process("  report.TXT  ", content, metadata)

    assert result.document.filename == "report.TXT"
    assert result.document.file_type == "txt"
    assert result.document.file_size == len(content)
    assert result.document.metadata == metadata
    assert result.document.metadata is not metadata
    assert result.document.pages[0].content == "First paragraph.\n\nSecond paragraph."
    assert [
        element.content for element in result.parsed_document.pages[0].elements
    ] == [
        "First paragraph.",
        "Second paragraph.",
    ]
    assert len(result.chunks) == 1
    assert result.chunks[0].content == "First paragraph.\n\nSecond paragraph."
    assert len(result.embedded_chunks) == 1
    assert isinstance(result.embedded_chunks[0], EmbeddedChunk)
    assert result.embedded_chunks[0].chunk is result.chunks[0]
    assert result.embedded_chunks[0].model == "fake-model"
    assert result.embedded_chunks[0].vector == (len(result.chunks[0].content), 0.5)
    assert provider.calls == [[result.chunks[0].content]]


def test_process_uses_actual_content_length_for_file_size_validation():
    service, _ = make_service(max_file_size_bytes=4)

    with pytest.raises(ValueError, match="exceed the maximum allowed size"):
        service.process("report.txt", b"12345")


@pytest.mark.parametrize("filename", ["", "   ", "report.csv"])
def test_process_rejects_invalid_filename_before_extraction(filename):
    service, _ = make_service()
    expected_message = (
        "Invalid file name" if not filename.strip() else "Unsupported file format"
    )

    with pytest.raises(ValueError, match=expected_message):
        service.process(filename, b"valid content")


def test_process_rejects_non_bytes_content():
    service, _ = make_service()

    with pytest.raises(TypeError, match="content must be bytes"):
        service.process("report.txt", bytearray(b"text"))  # type: ignore[arg-type]


def test_process_rejects_non_dictionary_metadata():
    service, _ = make_service()

    with pytest.raises(TypeError, match="metadata must be a dictionary"):
        service.process("report.txt", b"text", metadata=["invalid"])  # type: ignore[arg-type]


def test_process_propagates_text_extraction_errors():
    service, _ = make_service()

    with pytest.raises(DocumentExtractionError, match="Text extraction failed"):
        service.process("report.txt", b"\xff\xfe")


@pytest.mark.parametrize("max_file_size_bytes", [0, -1])
def test_service_rejects_non_positive_max_file_size(max_file_size_bytes):
    with pytest.raises(
        ValueError, match="max_file_size_bytes must be greater than zero"
    ):
        DocumentProcessingService(
            embedding_provider=FakeEmbeddingProvider(),
            max_file_size_bytes=max_file_size_bytes,
        )


def test_service_rejects_non_integer_max_file_size():
    with pytest.raises(TypeError, match="max_file_size_bytes must be an integer"):
        DocumentProcessingService(
            embedding_provider=FakeEmbeddingProvider(),
            max_file_size_bytes=100.5,  # type: ignore[arg-type]
        )
