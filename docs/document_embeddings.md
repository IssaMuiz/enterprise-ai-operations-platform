# Document Embeddings

## Overview

The embedding stage converts `DocumentChunk` text into numeric vectors and
returns `EmbeddedChunk` objects that retain the source chunk. It is split into
two parts:

- `OllamaEmbeddingProvider` in `app.infrastructure.ai.embeddings` makes the
  local HTTP request to Ollama.
- `embed_chunks()` in `app.modules.documents.embedder` batches document chunks,
  validates provider output, and attaches each vector to its source chunk.

The provider interface is expressed as a Python `Protocol`. This lets the
document use case accept Ollama today and a fake or different provider later,
without importing Ollama-specific networking code into the document module.

## Model and local setup

The default model is a community GGUF conversion of
`BAAI/bge-small-en-v1.5`, hosted as
`hf.co/CompendiumLabs/bge-small-en-v1.5-gguf:Q4_K_M`. Download it through
Ollama with:

```bash
ollama run hf.co/CompendiumLabs/bge-small-en-v1.5-gguf:Q4_K_M
```

Start the local Ollama server before calling the provider. The default API base
URL is `http://localhost:11434`; it can be changed when constructing the
provider. Local embedding requests do not require a hosted API key.

## Generating embeddings

```python
from app.infrastructure.ai.embeddings import OllamaEmbeddingProvider
from app.modules.documents.embedder import embed_chunks

provider = OllamaEmbeddingProvider()
embedded_chunks = embed_chunks(chunks, provider)
```

`embed_chunks()` sends at most 32 texts per request by default. Set
`batch_size` to change this. The Ollama request sets `truncate` to `false`, so
an input exceeding the model's context is reported by Ollama instead of being
silently shortened.

## Output and validation

Each `EmbeddedChunk` contains:

- The original `DocumentChunk`, including its source and page metadata.
- The embedding vector as a tuple of floats.
- The model identifier used to produce the vector.

The application verifies vector count, non-empty finite numeric values, and a
consistent dimension across the complete operation. Retaining the model name
helps identify which model created stored vectors. A vector database schema
must use the selected model's dimension; changing models later requires
re-embedding existing chunks.

The embedding stage does not persist vectors, calculate similarity, or perform
retrieval. Those belong to later storage and retrieval stages.
