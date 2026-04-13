# Inline metadata format

Date: 2026-04-11
Status: draft

## Context

The ingest format embeds YAML metadata blocks inline within the markdown body to mark page boundaries, speaker turns, and other structural annotations. These blocks are delimited with `---`, which collides with standard markdown's horizontal rule (thematic break) syntax.

This collision means markdown editors and renderers interpret inline metadata blocks as horizontal rules followed by plain text. The content cannot be edited in a WYSIWYG markdown editor, and renders incorrectly in any standard markdown viewer.

Options considered:

- **Keep triple-hyphen delimiters.** Accept the collision and work around it in custom tooling. Every tool that touches the content needs special handling.
- **HTML comments without a marker** (`<!-- speaker: Ross Coulthart -->`). No collision with markdown, but requires content heuristics to distinguish metadata comments from regular HTML comments.
- **HTML comments with an `anomalica` marker** (`<!-- anomalica\nspeaker: Ross Coulthart\n-->`). No collision, unambiguous parsing via a single regex, no false matches.
- **JSON inside comments.** Parseable but less readable and inconsistent with YAML-based frontmatter.
- **Custom fenced code blocks.** Renders as visible code blocks in editors, which is noisy.

## Decision

Use HTML comments with the `anomalica` marker for all inline metadata blocks:

```
<!-- anomalica
speaker: Ross Coulthart
time: 00:15:32
-->
```

The regex `<!--\s*anomalica\n(.*?)-->` captures every metadata block unambiguously. The YAML content inside is identical to the previous format - only the delimiters change.

Standard markdown frontmatter (the first `---` pair at the top of the file) is unchanged. Only inline blocks within the body are affected.

## Consequences

- Markdown editors and renderers handle the content correctly. HTML comments are invisible when rendered and preserved by editors.
- Every component that parses inline metadata needs updating: the ingester, the workbench (transcript parser, page marker preprocessor, document store operations), and the digester (when built).
- Migration of existing records is mechanical: replace inline `---` delimiters with `<!-- anomalica` and `-->`.
- The `anomalica` marker makes the format self-documenting. A reader encountering these comments can immediately identify them as structured metadata.
