from pathlib import Path

from .chunker import chunk_document
from .cleaner import clean_document
from .embedder import EmbeddingProvider, embed_chunks
from .entities import Document, DocumentProcessingResult
from .extractor import extract_document_pages
from .parser import parse_document
from .validator import validate_document


class DocumentProcessingService:
    """Coordinate document ingestion through embedding as one application use case."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        max_file_size_bytes: int,
        max_chunk_chars: int = 1500,
        chunk_overlap: int = 200,
        embedding_batch_size: int = 32,
    ) -> None:
        if type(max_file_size_bytes) is not int:
            raise TypeError("max_file_size_bytes must be an integer")
        if max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be greater than zero")

        self.embedding_provider = embedding_provider
        self.max_file_size_bytes = max_file_size_bytes
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap = chunk_overlap
        self.embedding_batch_size = embedding_batch_size

    def process(
        self,
        filename: str,
        content: bytes,
        metadata: dict[str, str | None] | None = None,
    ) -> DocumentProcessingResult:
        """Validate, extract, clean, parse, chunk, and embed one uploaded file."""
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary")

        normalized_filename = filename.strip() if isinstance(filename, str) else filename
        file_size = len(content)
        validate_document(
            filename=normalized_filename,
            file_size=file_size,
            max_size_bytes=self.max_file_size_bytes,
        )

        file_type = Path(normalized_filename).suffix.lower().lstrip(".")
        pages = extract_document_pages(normalized_filename, content)
        document = Document(
            filename=normalized_filename,
            file_type=file_type,
            file_size=file_size,
            metadata=dict(metadata) if metadata is not None else {},
            pages=pages,
        )
        cleaned_document = clean_document(document)
        parsed_document = parse_document(cleaned_document)
        chunks = chunk_document(
            parsed_document,
            max_chars=self.max_chunk_chars,
            overlap=self.chunk_overlap,
        )
        embedded_chunks = embed_chunks(
            chunks,
            self.embedding_provider,
            batch_size=self.embedding_batch_size,
        )

        return DocumentProcessingResult(
            document=cleaned_document,
            parsed_document=parsed_document,
            chunks=chunks,
            embedded_chunks=embedded_chunks,
        )
