# Document Chunker

## Overview

The chunker converts a `ParsedDocument` into ordered `DocumentChunk` objects
that can later be stored, embedded, and retrieved. It does not call an embedding
model or write to a database.

## Chunk size and overlap

`chunk_document(document, max_chars=1500, overlap=200)` uses character counts.
Each result's content is bounded by `max_chars`. When text exceeds the limit,
the chunker searches backward for a space near the limit and starts the next
chunk with up to `overlap` characters of preceding text. If a single word is
longer than the limit, it uses a hard character boundary.

Character limits keep this stage deterministic and avoid introducing a
tokenizer dependency. Character count is only an approximation of model token
count; a later embedding integration should validate chunks against the chosen
model's actual token limit.

## Page and section handling

- Chunks never cross page boundaries.
- A heading starts a new section and is retained as `section_heading` metadata.
- The heading is also prefixed to that section's chunk text to keep context
  available to downstream retrieval.
- Consecutive paragraphs in a section are joined with a blank line before
  splitting.
- A heading without following paragraphs still produces a chunk.
- Chunk indexes start at zero and increase across the document.

Each chunk also carries the source filename, file type, page number, document
metadata, and the parsed element types represented by its section.

If a heading is so long that it cannot fit as a repeated prefix, the complete
section text is split within the limit instead. In that case the heading remains
available in `section_heading`, though it may not appear in every chunk's text.

## Input validation

The function rejects values that are not a `ParsedDocument`, non-integer size
parameters, non-positive `max_chars`, negative overlap, and overlap greater
than or equal to the maximum chunk size. For a long heading prefix, overlap is
capped to the available body budget so splitting continues to make progress.
