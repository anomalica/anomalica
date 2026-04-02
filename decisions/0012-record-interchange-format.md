# 0012. Markdown with YAML annotations as record interchange format

Date: 2026-03-24
Status: accepted

## Context

The ingester converts raw source material (PDFs, audio, video, ebooks, web pages) into a normalised format that the digester consumes. This format must handle:

- Government documents with headings, tables, redacted sections, and page boundaries
- Interview transcripts with speaker labels and timestamps
- News articles with standard prose
- Books with chapter structure

We evaluated DoclingDocument (IBM), Unstructured.io's element model, TEI, Apache Tika XHTML, Pandoc AST, WebVTT, WARC, NewsML-G2, and various JSON schemas from NLP pipelines (LlamaIndex, Haystack, JSON-NLP). We also prototyped with DoclingDocument and found it adds significant structural bloat (self-references, duplicated fields, tree of JSON pointers) without benefit to the digester.

## Decision

Use markdown files with YAML frontmatter and inline YAML annotation blocks. The format is:

- **YAML frontmatter** for document-level metadata (title, date, authors, source, content hash)
- **Markdown body** for content as it naturally reads
- **YAML annotation blocks** (fenced with `---`) for block-level markers: page boundaries, speaker turns, image descriptions, block-level redactions
- **Double curly brace inline annotations** (`{{YAML}}`) for the rare cases where an annotation falls mid-sentence, such as `{{redacted: ~3 words}}` or `{{illegible}}`

The full specification lives in `architecture/record-format.md`.

## Why not existing formats

- **DoclingDocument**: typed hierarchical model with 65 type definitions. Duplicates every text field (`orig` and `text`), uses JSON pointer cross-references for a tree structure the digester doesn't need. The body section is just self-referential pointers. Designed for visual document layout preservation (bounding boxes, coordinate systems), which is irrelevant to knowledge extraction.
- **Unstructured.io elements**: flat JSON array of typed elements. Closer to what we need but still breaks natural prose into separate objects. No built-in support for speaker turns or timestamps. Tightly coupled to their processing pipeline.
- **Custom JSON schema** (our initial approach): works but produces output that isn't human-readable. A 3-page statement becomes hundreds of lines of JSON with structural overhead. Nobody can glance at the output and verify it looks right.
- **TEI XML**: enormously complex, designed for scholarly annotation. Thousands of pages of guidelines for a format that would carry mostly empty elements for our use case.

Markdown with YAML annotations is human-readable, git-friendly, trivially parseable, and carries everything the digester needs. Someone can open the file and read the document. The digester can parse the YAML blocks for metadata and markers, and read the text between them for content.

## Consequences

- The ingester produces `.md` files
- The digester parses markdown with YAML block detection
- The format is inspectable by humans without tooling
- The specification is controlled by the project and can be extended as needed
- No external dependency on any other project's schema
- The parser is simple: split on `---` fences, try YAML parse, everything else is content
- Inline annotations use double curly braces (`{{YAML}}`) to avoid collisions with single braces in source text. The content inside is valid YAML, keeping the format consistent throughout.
- The `---` fence is overloaded (frontmatter, annotations, and potentially content that contains triple dashes). The spec addresses this with normalisation rules but it remains a source of ambiguity
