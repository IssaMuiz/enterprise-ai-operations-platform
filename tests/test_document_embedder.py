import math

import httpx
import pytest

from app.infrastructure.ai import embeddings as ollama_embeddings
from app.infrastructure.ai.embeddings import (
    DEFAULT_OLLAMA_MODEL,
    OllamaEmbeddingError,
    OllamaEmbeddingProvider,
)
from app.modules.documents.embedder import embed_chunks
from app.modules.documents.entities import DocumentChunk


def make_chunk(content: str, chunk_index: int = 0) -> DocumentChunk:
    return DocumentChunk(
        content=content,
        chunk_index=chunk_index,
        filename="report.pdf",
        file_type="pdf",
        page_number=2,
        section_heading="Summary",
        metadata={"department": "finance"},
        source_element_types=("heading", "paragraph"),
    )


class FakeEmbeddingProvider:
    model = "fake-embedding-model"

    def __init__(self):
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[float(len(text)), 1.0] for text in texts]


def make_httpx_response(url: str, payload: object, status_code: int = 200):
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("POST", url),
    )


def test_embed_chunks_preserves_source_data_and_returns_float_vectors():
    chunks = [make_chunk("first chunk")]
    provider = FakeEmbeddingProvider()

    result = embed_chunks(chunks, provider)

    assert len(result) == 1
    assert result[0].chunk is chunks[0]
    assert result[0].vector == (11.0, 1.0)
    assert result[0].model == provider.model
    assert result[0].chunk.page_number == 2
    assert result[0].chunk.metadata == {"department": "finance"}


def test_embed_chunks_batches_inputs_and_preserves_order():
    chunks = [make_chunk(f"chunk {index}", index) for index in range(5)]
    provider = FakeEmbeddingProvider()

    result = embed_chunks(chunks, provider, batch_size=2)

    assert provider.calls == [
        ["chunk 0", "chunk 1"],
        ["chunk 2", "chunk 3"],
        ["chunk 4"],
    ]
    assert [item.chunk for item in result] == chunks
    assert [item.chunk.chunk_index for item in result] == [0, 1, 2, 3, 4]


def test_embed_chunks_returns_empty_result_without_calling_provider():
    provider = FakeEmbeddingProvider()

    assert embed_chunks([], provider) == []
    assert provider.calls == []


@pytest.mark.parametrize("batch_size", [0, -1])
def test_embed_chunks_rejects_non_positive_batch_size(batch_size):
    with pytest.raises(ValueError, match="batch_size must be greater than zero"):
        embed_chunks([], FakeEmbeddingProvider(), batch_size=batch_size)


@pytest.mark.parametrize("batch_size", [True, 1.5, "2"])
def test_embed_chunks_rejects_invalid_batch_size_type(batch_size):
    with pytest.raises(TypeError, match="batch_size must be an integer"):
        embed_chunks([], FakeEmbeddingProvider(), batch_size=batch_size)


def test_embed_chunks_rejects_non_chunk_inputs():
    with pytest.raises(TypeError, match="every item in chunks must be a DocumentChunk"):
        embed_chunks(["plain text"], FakeEmbeddingProvider())  # type: ignore[list-item]


def test_embed_chunks_rejects_provider_returning_wrong_vector_count():
    class WrongCountProvider(FakeEmbeddingProvider):
        def embed(self, texts: list[str]) -> list[list[float]]:
            return []

    with pytest.raises(ValueError, match="returned 0 vectors for 1 chunks"):
        embed_chunks([make_chunk("text")], WrongCountProvider())


def test_embed_chunks_rejects_empty_vector():
    class EmptyVectorProvider(FakeEmbeddingProvider):
        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[] for _ in texts]

    with pytest.raises(ValueError, match="empty embedding vector"):
        embed_chunks([make_chunk("text")], EmptyVectorProvider())


def test_embed_chunks_rejects_vectors_with_different_dimensions():
    class DifferentDimensionsProvider(FakeEmbeddingProvider):
        def embed(self, texts: list[str]) -> list[list[float]]:
            if texts[0] == "second":
                return [[1.0, 2.0, 3.0]]
            return [[1.0, 2.0]]

    chunks = [make_chunk("first"), make_chunk("second", 1)]

    with pytest.raises(ValueError, match="inconsistent dimensions"):
        embed_chunks(chunks, DifferentDimensionsProvider(), batch_size=1)


@pytest.mark.parametrize("invalid_value", [True, math.inf, math.nan, "1.0"])
def test_embed_chunks_rejects_non_finite_or_non_numeric_values(invalid_value):
    class InvalidVectorProvider(FakeEmbeddingProvider):
        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[invalid_value]]

    with pytest.raises(ValueError, match="finite numbers"):
        embed_chunks([make_chunk("text")], InvalidVectorProvider())


def test_ollama_provider_sends_batch_to_local_embed_endpoint(monkeypatch):
    captured = {}

    def fake_post(url, *, json, timeout):
        captured["url"] = url
        captured["body"] = json
        captured["timeout"] = timeout
        return make_httpx_response(url, {"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    monkeypatch.setattr(ollama_embeddings.httpx, "post", fake_post)
    provider = OllamaEmbeddingProvider()

    result = provider.embed(["first", "second"])

    assert captured["url"] == "http://localhost:11434/api/embed"
    assert captured["body"] == {
        "model": DEFAULT_OLLAMA_MODEL,
        "input": ["first", "second"],
        "truncate": False,
    }
    assert captured["timeout"] == 120.0
    assert result == [[0.1, 0.2], [0.3, 0.4]]


def test_ollama_provider_normalizes_base_url_and_accepts_custom_model(monkeypatch):
    def fake_post(url, *, json, timeout):
        assert url == "http://ollama.local:11434/api/embed"
        return make_httpx_response(url, {"embeddings": [[1.0]]})

    monkeypatch.setattr(ollama_embeddings.httpx, "post", fake_post)
    provider = OllamaEmbeddingProvider(
        base_url="http://ollama.local:11434/",
        model="custom-model",
        timeout_seconds=30,
    )

    assert provider.embed(["content"]) == [[1.0]]
    assert provider.model == "custom-model"
    assert provider.timeout_seconds == 30.0


def test_ollama_provider_does_not_call_server_for_empty_batch(monkeypatch):
    def unexpected_post(*_args, **_kwargs):
        pytest.fail("HTTPX should not be called for an empty input")

    monkeypatch.setattr(ollama_embeddings.httpx, "post", unexpected_post)

    assert OllamaEmbeddingProvider().embed([]) == []


@pytest.mark.parametrize("texts", ["single string", ["", "valid"]])
def test_ollama_provider_rejects_invalid_text_inputs(texts):
    provider = OllamaEmbeddingProvider()
    error = TypeError if isinstance(texts, str) else ValueError
    message = "sequence of strings" if isinstance(texts, str) else "cannot be empty"

    with pytest.raises(error, match=message):
        provider.embed(texts)  # type: ignore[arg-type]


def test_ollama_provider_rejects_wrong_number_of_vectors(monkeypatch):
    monkeypatch.setattr(
        ollama_embeddings.httpx,
        "post",
        lambda url, **_kwargs: make_httpx_response(url, {"embeddings": [[0.1]]}),
    )

    with pytest.raises(OllamaEmbeddingError, match="1 vectors for 2 texts"):
        OllamaEmbeddingProvider().embed(["first", "second"])


def test_ollama_provider_wraps_server_http_errors(monkeypatch):
    def fake_post(url, **_kwargs):
        return httpx.Response(
            404,
            text="model not found",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(ollama_embeddings.httpx, "post", fake_post)

    with pytest.raises(OllamaEmbeddingError, match="HTTP 404: model not found"):
        OllamaEmbeddingProvider().embed(["text"])


def test_ollama_provider_rejects_malformed_json_response(monkeypatch):
    monkeypatch.setattr(
        ollama_embeddings.httpx,
        "post",
        lambda url, **_kwargs: httpx.Response(
            200,
            content=b"not-json",
            request=httpx.Request("POST", url),
        ),
    )

    with pytest.raises(OllamaEmbeddingError, match="invalid JSON"):
        OllamaEmbeddingProvider().embed(["text"])


@pytest.mark.parametrize(
    ("base_url", "model", "timeout", "error"),
    [
        ("", DEFAULT_OLLAMA_MODEL, 10, ValueError),
        ("http://localhost:11434", "", 10, ValueError),
        ("http://localhost:11434", DEFAULT_OLLAMA_MODEL, 0, ValueError),
        ("http://localhost:11434", DEFAULT_OLLAMA_MODEL, True, TypeError),
    ],
)
def test_ollama_provider_validates_configuration(base_url, model, timeout, error):
    with pytest.raises(error):
        OllamaEmbeddingProvider(
            base_url=base_url,
            model=model,
            timeout_seconds=timeout,
        )
