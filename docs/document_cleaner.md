# Document Cleaner

## Overview

The document cleaner normalizes extracted document text before it moves to subsequent document-processing stages.

It operates on individual page contents while returning a new `Document` containing the cleaned pages.

The cleaner is responsible for text normalization, not document structure interpretation.

## Module

`app/modules/documents/cleaner.py`

## Public Functions

### `clean_text(text: str) -> str`

Cleans a single text string.

**Responsibilities:**

- Normalize Windows (`\r\n`), Unix (`\n`) and old Mac (`\r`) line endings to `\n`.
- Remove trailing whitespace from each line.
- Remove leading and trailing whitespace from the complete text.
- Collapse three or more consecutive newline characters into two.

**Input:** A string containing extracted text.

**Output:** A normalized string.

### `clean_document(document: Document) -> Document`

Cleans all pages belonging to a document.

**Responsibilities:**

- Process each page independently using `clean_text()`.
- Create new `DocumentPage` objects.
- Preserve page metadata, including page numbers and line information.
- Preserve document metadata, including filename, file type and file size.
- Return a new `Document` without modifying the original.

**Input:** A `Document` instance.

**Output:** A new `Document` containing cleaned pages.

## Processing Flow

1. Receive an extracted `Document`.
2. Iterate through its pages.
3. Normalize each page's text.
4. Create a new page with the cleaned text and original metadata.
5. Create and return a new document containing the cleaned pages.

## Design Decisions

### Page-level cleaning

Each page is cleaned independently to preserve the boundaries between pages.

### Immutability

The cleaner does not modify the original document or its page objects. It constructs new objects instead.

This helps prevent unintended side effects when different processing components need access to the original extracted content.

### Separation of responsibilities

The cleaner handles text normalization only.

Paragraph detection, heading identification, document structure interpretation and OCR are outside its current scope.

## Testing

The cleaner is tested for:

- Different line-ending formats.
- Leading and trailing whitespace.
- Trailing whitespace on individual lines.
- Multiple consecutive blank lines.
- PDF document cleaning.
- TXT document cleaning.
- Empty pages and documents without pages.
- Preservation of document and page metadata.
- Preservation of the original document and page objects.

Test module: `tests/test_cleaner.py`

## Current Limitations

- Does not reconstruct paragraph boundaries.
- Does not identify headings or sections.
- Does not perform OCR on scanned documents.
- Does not interpret document layout.
- Does not implement language-specific normalization.

These capabilities may be addressed by future document-processing components.
