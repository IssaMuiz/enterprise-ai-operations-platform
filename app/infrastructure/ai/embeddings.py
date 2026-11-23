import math
from collections.abc import Sequence

import httpx

DEFAULT_OLLAMA_MODEL = "hf.co/CompendiumLabs/bge-small-en-v1.5-gguf:Q4_K_M"


class OllamaEmbeddingError(RuntimeError):
    """Raised when Ollama cannot return a valid embedding response."""


class OllamaEmbeddingProvider:
    """Generate embeddings through a local Ollama server's HTTP API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout_seconds: float = 120.0,
    ) -> None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url must be a non-empty string")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ):
            raise TypeError("timeout_seconds must be a number")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.timeout_seconds = float(timeout_seconds)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Send one batch of texts to Ollama and return its vectors in order."""
        if isinstance(texts, (str, bytes)):
            raise TypeError("texts must be a sequence of strings, not one string")
        if not isinstance(texts, Sequence):
            raise TypeError("texts must be a sequence of strings")
        if not texts:
            return []
        if any(not isinstance(text, str) for text in texts):
            raise TypeError("every input text must be a string")
        if any(not text.strip() for text in texts):
            raise ValueError("input texts cannot be empty")

        body = {
            "model": self.model,
            "input": list(texts),
            "truncate": False,
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/embed",
                json=body,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            message = f"Ollama returned HTTP {exc.response.status_code}"
            if detail:
                message = f"{message}: {detail}"
            raise OllamaEmbeddingError(message) from exc
        except httpx.RequestError as exc:
            raise OllamaEmbeddingError(
                f"Could not reach Ollama at {self.base_url}"
            ) from exc
        except ValueError as exc:
            raise OllamaEmbeddingError("Ollama returned invalid JSON") from exc

        if not isinstance(payload, dict) or not isinstance(
            payload.get("embeddings"), list
        ):
            raise OllamaEmbeddingError(
                "Ollama response did not contain an embeddings list"
            )

        embeddings = payload["embeddings"]
        if len(embeddings) != len(texts):
            raise OllamaEmbeddingError(
                f"Ollama returned {len(embeddings)} vectors for {len(texts)} texts"
            )

        vectors = []
        for embedding in embeddings:
            if not isinstance(embedding, list) or not embedding:
                raise OllamaEmbeddingError(
                    "Ollama returned an invalid embedding vector"
                )
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in embedding
            ):
                raise OllamaEmbeddingError(
                    "Ollama returned a vector containing invalid numeric values"
                )
            try:
                vectors.append([float(value) for value in embedding])
            except (TypeError, ValueError) as exc:
                raise OllamaEmbeddingError(
                    "Ollama returned a vector containing non-numeric values"
                ) from exc
        return vectors
