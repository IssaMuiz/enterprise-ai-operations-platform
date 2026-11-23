import math
from collections.abc import Sequence
from typing import Protocol

from .entities import DocumentChunk, EmbeddedChunk


class EmbeddingProvider(Protocol):
    model: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def embed_chunks(
    chunks: Sequence[DocumentChunk],
    provider: EmbeddingProvider,
    batch_size: int = 32,
) -> list[EmbeddedChunk]:
    """Embed document chunks in bounded batches and retain their source data."""
    if isinstance(chunks, (str, bytes)) or not isinstance(chunks, Sequence):
        raise TypeError("chunks must be a sequence of DocumentChunk objects")
    if any(not isinstance(chunk, DocumentChunk) for chunk in chunks):
        raise TypeError("every item in chunks must be a DocumentChunk")
    if type(batch_size) is not int:
        raise TypeError("batch_size must be an integer")
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    if not isinstance(provider.model, str) or not provider.model.strip():
        raise ValueError("provider.model must be a non-empty string")
    if not chunks:
        return []

    embedded_chunks = []
    expected_dimension = None
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = provider.embed([chunk.content for chunk in batch])
        if len(vectors) != len(batch):
            raise ValueError(
                f"provider returned {len(vectors)} vectors for {len(batch)} chunks"
            )

        for chunk, vector in zip(batch, vectors, strict=True):
            if not vector:
                raise ValueError("provider returned an empty embedding vector")
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in vector
            ):
                raise ValueError("embedding vectors must contain finite numbers")

            if expected_dimension is None:
                expected_dimension = len(vector)
            elif len(vector) != expected_dimension:
                raise ValueError(
                    "provider returned vectors with inconsistent dimensions"
                )

            embedded_chunks.append(
                EmbeddedChunk(
                    chunk=chunk,
                    vector=tuple(float(value) for value in vector),
                    model=provider.model,
                )
            )

    return embedded_chunks
