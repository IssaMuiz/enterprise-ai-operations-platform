# Document Parser

## Overview

The parser converts a cleaned `Document` into a `ParsedDocument` containing
page-level headings and paragraphs. It does not read files or call an AI model.

## Input and output

`parse_document(document)` accepts a `Document` and returns a new
`ParsedDocument`. It preserves the document's filename, file type, size, page
numbers, and metadata. Each parsed element contains its text and the original
PDF spans associated with that text.

## Paragraph boundaries

One or more blank lines end a block. Non-empty lines inside a block are joined
with newline characters. Empty pages produce no elements. For TXT documents,
every block is a paragraph because plain text has no formatting metadata for
reliable heading detection.

## PDF heading heuristic

PDF lines are classified using their associated text spans:

- A line is a heading when spans covering at least half its text use a font at
  least 1.15 times the lower-quartile positive font size on that page. Using a
  lower-quartile baseline helps when a wrapped heading occupies multiple lines.
- A line is also a heading when all its associated spans are bold and the line
  is at most 120 characters long.
- Adjacent lines with the same classification are grouped into one element.
- The parser leaves `level` unset because these signals do not reliably
  distinguish heading levels.

Span offsets are used when available. If offsets are missing, the parser
associates spans by matching normalized span text against each line. This
fallback is approximate when the same short text appears repeatedly or PDF
text extraction changes whitespace.

## Limitations

Heading detection is heuristic and can misclassify emphasized body text or
miss headings in PDFs without useful font metadata. TXT headings are not
inferred. Tables, lists, OCR, semantic classification, and nested heading
levels are outside the parser's current scope.
