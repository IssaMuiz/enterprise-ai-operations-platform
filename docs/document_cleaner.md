# Document Cleaner

## 1. Overview

The document cleaner is responsible for normalizing extracted document text while preserving the document's existing page structure and extracted layout information.

It operates on application-level `Document` entities rather than directly accessing PDF files or using PyMuPDF.

The cleaner currently supports documents represented using the application's `Document` and `DocumentPage` entities.

## 2. Responsibilities

The cleaner is responsible for:

- Normalizing line endings.
- Removing unnecessary trailing whitespace.
- Removing unnecessary leading and trailing document whitespace.
- Reducing excessive consecutive blank lines.
- Cleaning individual document pages.
- Preserving page numbers and line information.
- Preserving extracted text spans and their formatting information.
- Returning a new `Document` without modifying the original document.

The cleaner does not extract text, interpret document structures, identify headings, or classify content.

## 3. Architecture

The cleaning process follows this structure:

```text
Extracted Document
        |
        v
   Document
        |
        v
 Iterate Through Pages
        |
        v
    clean_text()
        |
        v
 Normalize Page Content
        |
        v
 Preserve Page Information
        |
        v
 Preserve Original Spans
        |
        v
 Create New DocumentPage
        |
        v
 Create New Document
        |
        v
 Return Cleaned Document
```

## 4. Text Normalization

The cleaner uses Python's `re` module to normalize extracted text.

### 4.1 Line-ending normalization

Different operating systems represent line endings differently.

The cleaner converts:

- Windows line endings (`\r\n`) into `\n`.
- Old Mac-style line endings (`\r`) into `\n`.

This provides a consistent line-ending representation.

### 4.2 Trailing whitespace removal

The cleaner removes trailing whitespace from individual lines.

This prevents unnecessary spaces at the end of extracted lines.

### 4.3 Surrounding whitespace removal

The cleaner uses `strip()` to remove unnecessary whitespace at the beginning and end of the complete text.

### 4.4 Consecutive blank-line reduction

The cleaner reduces three or more consecutive newline characters to two.

This preserves paragraph separation while removing excessive blank lines.

## 5. Document Cleaning

### `clean_text(text)`

Accepts a string and returns its normalized representation.

The function performs the text normalization operations described above.

### `clean_document(document)`

Accepts a `Document` entity and returns a new cleaned `Document`.

For every page, it:

1. Normalizes the page's complete text using `clean_text()`.
2. Preserves the page number.
3. Preserves the original line information.
4. Preserves the extracted text spans.

The function creates new `DocumentPage` instances and a new `Document` instance.

## 6. Span Preservation

The `DocumentPage` entity contains both:

- `content`: the complete extracted page text.
- `spans`: individual extracted text segments containing formatting and positional information.

The cleaner normalizes `content` but deliberately preserves the original spans.

This distinction is important.

The span text is not independently normalized because individual spans may represent different formatting runs, and whitespace may exist between spans.

Changing individual span text could affect the ability to reconstruct the original document layout.

The two representations therefore serve different purposes:

| Representation       | Purpose                                                 |
| -------------------- | ------------------------------------------------------- |
| Cleaned page content | Downstream text processing, chunking and retrieval      |
| Original text spans  | Layout-aware structural parsing and formatting analysis |

This is an intentional design decision.

## 7. Data Preservation

The cleaner creates new page and document objects instead of modifying the original objects.

The original document remains available after cleaning.

The cleaner also creates a separate spans list for each cleaned page while preserving the existing `TextSpan` objects.

This prevents the original and cleaned pages from sharing the same mutable list.

## 8. Error Handling

The cleaner currently relies on its input contract:

- `clean_text()` expects a string.
- `clean_document()` expects a valid `Document` entity.

The cleaner does not handle file-reading, PDF-decoding, or extraction errors because these responsibilities belong to the extractor.

## 9. Testing Strategy

The cleaner is tested independently of PyMuPDF.

Mock `Document` and `DocumentPage` entities are used to provide representative extracted document data.

The test suite covers:

- Windows line-ending normalization.
- Old Mac-style line-ending normalization.
- Surrounding whitespace removal.
- Trailing whitespace removal.
- Multiple blank-line reduction.
- Multi-page PDF document cleaning.
- Text span preservation.
- Original document preservation.
- Empty page handling.
- Documents without pages.
- TXT document cleaning.
- Metadata preservation.

The tests verify that cleaning produces the expected normalized content without modifying the original document or losing its extracted layout information.

## 10. Current Limitations

- Cleaning operates on complete page text rather than individual text spans.
- The cleaner does not identify headings or paragraphs.
- The cleaner does not reconstruct document layout.
- It does not process tables or images.
- It does not perform OCR.
- It does not correct spelling or interpret document meaning.

These responsibilities belong to other stages of the document-processing pipeline.

## 11. Downstream Integration

The cleaner receives the `Document` produced by the document ingestion process.

Its output can subsequently be passed to the document parser.

The parser will use the preserved span information to identify structural elements such as headings and paragraphs.

The cleaned page content will also be available for subsequent document-processing operations, including chunking and retrieval.
