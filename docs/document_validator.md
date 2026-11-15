# Document Validator

## 1. Overview

The document validator is responsible for checking document input before it enters the document extraction pipeline.

It ensures that incoming document metadata satisfies the application's basic validation requirements.

The validator currently supports PDF and plain text documents.

## 2. Responsibility

The validator is responsible for:

- Checking that the filename is a string.
- Ensuring the filename is not empty.
- Checking whether the file extension is supported.
- Validating the document file size.
- Validating the configured maximum file size.
- Ensuring the document does not exceed the permitted size.

The validator does not extract or inspect the actual contents of a document.

## 3. Supported Formats

| Format     | Extension |
| ---------- | --------- |
| PDF        | `.pdf`    |
| Plain text | `.txt`    |

File extension matching is case-insensitive.

## 4. Function Interface

### `validate_document()`

**Module:** `app.modules.documents.validator`

**Parameters:**

| Parameter        | Type  | Description                               |
| ---------------- | ----- | ----------------------------------------- |
| `filename`       | `str` | Name of the document being validated.     |
| `file_size`      | `int` | Document size in bytes.                   |
| `max_size_bytes` | `int` | Maximum permitted document size in bytes. |

**Return:** `None` when validation succeeds.

The function raises an exception when an input violates the validation requirements.

## 5. Validation Rules

The following validation rules are enforced:

1. The filename must be a string.
2. The file size must be an integer.
3. The maximum permitted file size must be an integer.
4. The filename must not be empty or contain only whitespace.
5. The filename must have a supported extension.
6. The file size must be greater than zero.
7. The maximum permitted file size must be greater than zero.
8. The file size must not exceed the configured maximum.

The validator uses strict integer type checking for file sizes, rejecting booleans and floating-point values.

## 6. Error Handling

| Condition                             | Exception    |
| ------------------------------------- | ------------ |
| Filename has an invalid type          | `TypeError`  |
| File size has an invalid type         | `TypeError`  |
| Maximum file size has an invalid type | `TypeError`  |
| Filename is empty                     | `ValueError` |
| Unsupported file extension            | `ValueError` |
| File size is zero or negative         | `ValueError` |
| Maximum file size is zero or negative | `ValueError` |
| File exceeds maximum permitted size   | `ValueError` |

## 7. Design Considerations

### Separation of concerns

Validation is independent of document extraction. This allows the application to reject invalid document metadata before invoking format-specific extraction logic.

### Reusability

The validator can be called by different application entry points, including API endpoints, background processing tasks and other document ingestion workflows.

### File content verification

Checking a filename extension does not guarantee that the underlying file contains valid data of that format.

Actual content verification and extraction errors are handled by the extraction component.

## 8. Testing

The validator is tested using pytest.

Test coverage includes:

- Valid document metadata.
- Invalid filename types.
- Empty filenames.
- Supported extensions.
- Unsupported extensions.
- Case-insensitive extension matching.
- Invalid file-size types.
- Zero and negative file sizes.
- Invalid maximum file sizes.
- Documents exceeding the permitted size.
- Documents exactly at the maximum permitted size.

## 9. Current Limitations

The validator currently performs basic metadata and file-size validation.

It does not yet implement:

- File signature or magic-byte verification.
- Malware scanning.
- MIME type verification.
- Content-based file format detection.
- Duplicate document detection.
- User-specific document permissions.

These responsibilities can be introduced as the document ingestion requirements evolve.

---

**Implementation status:** Implemented and tested.
