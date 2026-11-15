# Document Extractor

## 1. Overview

The document extractor is responsible for retrieving textual content from supported document formats and converting the extracted content into structured application-level entities.

It provides the text extraction capability used by subsequent document processing stages.

The current implementation supports PDF and plain text documents.

## 2. Responsibility

The extractor is responsible for:

- Accepting document filenames and binary content.
- Identifying supported document formats through file extensions.
- Extracting text from PDF documents.
- Extracting text from plain text documents.
- Preserving PDF page boundaries.
- Recording relevant source-location metadata.
- Converting extracted content into `DocumentPage` entities.
- Handling expected extraction failures.

The extractor does not perform document validation based on maximum file size, advanced text cleaning, classification or semantic processing.

## 3. Supported Formats

| Format     | Extension | Extraction library    |
| ---------- | --------- | --------------------- |
| PDF        | `.pdf`    | PyMuPDF               |
| Plain text | `.txt`    | Python UTF-8 decoding |

File extension matching is case-insensitive.

## 4. Function Interface

### `extract_document_pages()`

**Module:** `app.modules.documents.extractor`

**Parameters:**

| Parameter  | Type    | Description                     |
| ---------- | ------- | ------------------------------- |
| `filename` | `str`   | Original document filename.     |
| `content`  | `bytes` | Binary content of the document. |

**Return type:**

`list[DocumentPage]`

The function returns a list of extracted document content entities.

## 5. PDF Extraction

PDF extraction is implemented using PyMuPDF.

The extraction process:

1. Opens the PDF from its in-memory binary content.
2. Iterates through the document's physical pages.
3. Extracts text from each page.
4. Creates a `DocumentPage` entity for each physical page.
5. Assigns page numbers starting from 1.
6. Returns the collection of extracted pages.

### Output representation

Each physical PDF page is represented by a separate `DocumentPage`.

For example, a PDF containing three physical pages produces three extracted entities:

| Entity | Page number | Content                    |
| ------ | ----------: | -------------------------- |
| First  |           1 | Extracted text from page 1 |
| Second |           2 | Extracted text from page 2 |
| Third  |           3 | Extracted text from page 3 |

The extractor preserves the text returned by PyMuPDF, including trailing newline characters where present.

## 6. Plain Text Extraction

TXT extraction uses Python's UTF-8 decoding functionality.

The extraction process:

1. Decodes the binary content using UTF-8.
2. Checks whether the decoded content is empty.
3. Determines the number of logical lines.
4. Creates one `DocumentPage` entity containing the complete text.
5. Records the starting and ending line numbers.

### Output representation

Unlike PDF extraction, the entire TXT file is represented by one `DocumentPage`.

For a non-empty text file:

- `start_line` begins at 1.
- `end_line` represents the number of lines returned by `splitlines()`.
- `content` preserves the decoded text.

An empty TXT file returns an empty list.

## 7. DocumentPage Entity

The extractor uses the `DocumentPage` data class defined in `entities.py`.

Its fields are:

| Field         | Type          | Description                                            |
| ------------- | ------------- | ------------------------------------------------------ |
| `content`     | `str`         | Extracted textual content.                             |
| `page_number` | `int \| None` | Physical PDF page number, when applicable.             |
| `start_line`  | `int \| None` | Starting line number for TXT content, when applicable. |
| `end_line`    | `int \| None` | Ending line number for TXT content, when applicable.   |

Optional metadata fields are set to `None` when they do not apply to the extracted format.

## 8. Error Handling

The extractor defines a custom exception:

### `DocumentExtractionError`

This exception represents expected failures during document extraction.

| Condition                    | Exception                 |
| ---------------------------- | ------------------------- |
| Filename has an invalid type | `TypeError`               |
| Content has an invalid type  | `TypeError`               |
| Filename is empty            | `ValueError`              |
| Unsupported file extension   | `ValueError`              |
| Malformed or unreadable PDF  | `DocumentExtractionError` |
| Invalid UTF-8 content        | `DocumentExtractionError` |

The extractor uses exception chaining to preserve the original underlying exception, making debugging easier.

## 9. Dependencies

The current implementation uses:

- **PyMuPDF:** PDF document opening and text extraction.
- **pathlib:** File extension identification.
- **dataclasses:** Structured representation through the `DocumentPage` entity.

## 10. Testing

The extractor is tested using pytest.

Test coverage includes:

- Invalid filename types.
- Empty filenames.
- Invalid binary content types.
- Unsupported file extensions.
- Multi-page PDF extraction.
- PDF page numbering.
- Malformed PDF input.
- Plain text extraction.
- TXT line metadata.
- Empty TXT documents.
- Invalid UTF-8 content.

PDF test documents are generated programmatically using PyMuPDF, avoiding dependence on external PDF fixtures.

## 11. Current Limitations

The extractor currently provides basic text extraction.

It does not yet support:

- OCR for scanned PDFs and image-based documents.
- Image extraction.
- Table extraction.
- DOCX, XLSX or other document formats.
- Advanced text cleaning and normalization.
- Structured content parsing.
- Document classification.
- Text chunking.
- Embedding generation.

These capabilities will be considered in subsequent document processing stages.

---

**Implementation status:** PDF and TXT text extraction implemented and tested.
