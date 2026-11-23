# Document Processing Service

## Overview

`DocumentProcessingService` coordinates the document pipeline for one uploaded
file. It combines existing stages; it does not replace their individual
responsibilities or persist results.

## Processing flow

For each file, `process()`:

1. Checks the content and optional metadata input types.
2. Validates the filename and actual byte length against the configured file
   size limit.
3. Extracts pages from PDF or UTF-8 TXT content.
4. Builds a `Document` and cleans its page text.
5. Parses headings and paragraphs.
6. Chunks parsed elements while retaining page and heading context.
7. Embeds chunks in batches through the injected `EmbeddingProvider`.
8. Returns a `DocumentProcessingResult` containing the cleaned document, parsed
   document, chunks, and embedded chunks.

The service derives file size from `len(content)` instead of trusting a size
supplied by the caller. The configured maximum is required when constructing
the service, so upload limits are explicit.

## Configuration and dependencies

The embedding provider is injected, allowing the service to use Ollama in the
application and a small fake provider in unit tests. The constructor also
accepts chunk size, overlap, and embedding batch size; their validation is
performed by the corresponding pipeline functions when processing begins.

```python
from app.infrastructure.ai.embeddings import OllamaEmbeddingProvider
from app.modules.documents.service import DocumentProcessingService

service = DocumentProcessingService(
    embedding_provider=OllamaEmbeddingProvider(),
    max_file_size_bytes=10 * 1024 * 1024,
)
result = service.process("policy.txt", file_bytes)
```

## Result and errors

The result keeps intermediate document representations available for review
and future persistence. Each embedded chunk also retains its source chunk.

Input validation, extraction, chunking, and embedding errors propagate to the
caller. The service does not hide failures or convert them into API responses;
an API layer can map them to HTTP status codes later. Processing is currently
synchronous and in memory. Background jobs, storage, and retry policies belong
to later stages.

## Known constraint

Chunk size is currently measured in characters while BGE Small enforces a
token context limit. The Ollama provider disables silent truncation, so
token-dense chunks can fail at embedding time. A future token-aware chunker or
explicit split-and-retry policy can address that if real documents expose it.
