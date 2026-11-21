# Document Extractor

## 1. Overview

The document extractor is responsible for extracting text and layout information from supported document formats and converting the extracted information into application-level `DocumentPage` entities.

It currently supports:

- PDF (`.pdf`)
- Plain text (`.txt`)

For PDF documents, the extractor retrieves both the complete page text and individual text spans with their formatting and positional information.

For TXT documents, it extracts the text content and records the original line range.

## 2. Responsibilities

The extractor is responsible for:

- Validating the filename and file content types.
- Checking supported file extensions.
- Extracting text from PDF and TXT documents.
- Extracting PDF text spans and their layout information.
- Preserving page ordering and page numbers.
- Recording line information for TXT documents.
- Converting extraction results into `DocumentPage` entities.
- Handling expected extraction and decoding failures.

The extractor does not clean, normalize, classify, or parse the extracted document content.

## 3. Architecture

The extraction process follows this structure:

```text
Uploaded File
     |
     v
Input Validation
     |
     v
File Extension Detection
     |
     +----------------------+
     |                      |
     v                      v
    PDF                    TXT
     |                      |
     v                      v
Open with PyMuPDF       Decode UTF-8
     |                      |
     v                      v
Extract Page Text       Identify Line Range
     |                      |
     v                      v
Extract Text Spans      Create DocumentPage
     |                      |
     v                      |
Create DocumentPage <------+
     |
     v
Return List[DocumentPage]
```

## 4. PDF Extraction

PDF extraction uses PyMuPDF.

The extractor opens PDF content from bytes and iterates through its pages.

For every page, it extracts:

### 4.1 Complete page text

The complete text is obtained using:

```python
page.get_text("text")
```

This provides the page's text content for subsequent processing.

### 4.2 Text span extraction

The extractor uses:

```python
page.get_text("dict")
```

PyMuPDF represents PDF text using a hierarchy:

```text
Page
 └── Blocks
      └── Lines
           └── Spans
```

The extractor traverses this hierarchy and collects individual text spans.

Whitespace-only spans are excluded from the current extraction output.

Each extracted span is represented by a `TextSpan` entity.

### 4.3 TextSpan attributes

| Attribute   | Description                   |
| ----------- | ----------------------------- |
| `text`      | Extracted text content        |
| `font`      | Font name                     |
| `font_size` | Font size                     |
| `flags`     | PyMuPDF font-style flags      |
| `bbox`      | Text bounding box coordinates |

The bounding box is represented as:

```python
(x0, y0, x1, y1)
```

These attributes preserve useful layout information for downstream document parsing.

### 4.4 Page representation

Each extracted PDF page becomes a `DocumentPage` containing:

- Complete page text.
- Page number.
- Extracted text spans.

The page number starts at 1.

## 5. TXT Extraction

TXT files are decoded using UTF-8.

The extractor:

1. Decodes the supplied bytes.
2. Checks whether the content is empty.
3. Determines the number of lines.
4. Creates a `DocumentPage` containing the original text and line range.

TXT documents do not contain PDF-style font or positional metadata, so their spans list remains empty.

For non-empty TXT documents, the page starts at line 1 and ends at the number of extracted lines.

An empty TXT file returns an empty list of pages.

## 6. Input Validation

The extractor validates:

- Filename must be a string.
- File content must be bytes.
- Filename must not be empty after trimming whitespace.
- File extension must be supported.

Unsupported extensions and invalid input values raise appropriate validation exceptions.

## 7. Error Handling

The extractor defines:

```python
class DocumentExtractionError(Exception):
    """Raised when document extraction fails."""
```

Expected extraction failures are wrapped in this application-specific exception.

Current handled failures include:

- Invalid or malformed PDF data resulting in `pymupdf.FileDataError`.
- Invalid UTF-8 text resulting in `UnicodeDecodeError`.

## 8. Public Functions

### `extract_document_pages(filename, content)`

Extracts supported document content and returns a list of `DocumentPage` entities.

### `extract_text_span(page)`

Extracts individual text spans from a PyMuPDF page and returns a list of `TextSpan` entities.

## 9. Testing Strategy

The extractor is tested using actual PDF documents generated programmatically with PyMuPDF.

The test suite covers:

- Invalid filename types.
- Empty filenames.
- Invalid content types.
- Unsupported extensions.
- Multi-page PDF extraction.
- PDF text extraction.
- PDF span extraction.
- Malformed PDF files.
- TXT extraction.
- Empty TXT files.
- Invalid UTF-8 content.

Generated PDF fixtures allow the extractor to be tested against real PDF structures without depending on external document files.

## 10. Current Limitations

- PDF extraction focuses on text and span information.
- Tables and complex document structures are not currently interpreted.
- TXT files do not provide PDF-style layout information.
- PDF metadata extraction is not currently part of the `extract_document_pages()` function.
- Scanned PDFs requiring OCR are not currently supported.

## 11. Downstream Integration

The extractor produces `DocumentPage` entities consumed by the document cleaner.

The cleaner normalizes the complete page text while retaining the original extracted span information for later structural parsing.

The extracted spans will also support the document parser when identifying headings and paragraphs.
