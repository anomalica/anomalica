# 0027. Digest interchange format

Date: 2026-05-20
Status: accepted

## Context

The digester produces, for each source record, a single intermediate
artefact that holds every node and every claim extracted by the
artificial-intelligence pipeline. The deterministic import step reads
this artefact to populate the SQLite database, the workbench reads it
to display "what was extracted from this record", and the assembler
reads through the database to produce articles. The artefact is the
contract between everything that follows the artificial-intelligence
extraction step.

Until now this artefact was a markdown file at
`anomalica-digests/extracts/{name}.extract.md`. The format was never
written down. It existed as the implicit contract between the writer
in `digester/markdown_format.py` and the parser in the same file. The
parser depends on strict line conventions - level-three headings of
the form `### {uuid} {type}: {name}`, body lines of the form
`refs: A; B; C`, and so on - and the writer must produce these
verbatim or the parser silently fails.

The structural problem: the markdown skin gave the impression of a
human document while in fact carrying machine-structured data
(typed enums, lists, universally unique identifiers, references).
This produced two failure modes during recent development.

First, escaping pitfalls. The refs list was originally
comma-delimited, which broke the moment person names switched to
`Last, First` form because the comma now appeared inside the names
themselves. The fix was a separate one-off migration to a
semicolon delimiter. A format with a real list type avoids the class
of bug entirely.

Second, the format had no version identifier. Backwards-compatible
extensions were possible only by adding optional lines the old parser
happened to ignore. A breaking change would have required either a
flag day or simultaneous reader/writer updates with no detection of
mismatch.

Markdown remains the right choice for the ingester output, where the
body is genuinely a text document with annotation blocks. It is not
the right choice for the digester output, where the body is
exclusively structured data.

The workbench is about to be extended to show a third column - the
digest alongside the source and the ingest. Locking the format now,
before the workbench is built against it, avoids relitigating later.

## Decision

The digester output is a YAML file at
`anomalica-digests/records/{friendly-name}.yaml`, conforming to schema
`anomalica/digest/1`. The full specification lives in
[`architecture/digest-format.md`](../architecture/digest-format.md).

Key shape choices, with the rationale:

- **YAML rather than JSON or markdown.** YAML is line-oriented and
  diff-friendly, supports block scalars for multi-line strings
  without escaping, and reads acceptably to humans. JSON's lack of
  multi-line strings and forced quoting make it noisier in diffs and
  in editors. Markdown imposes formatting conventions on machine data,
  which is what 0019 (record interchange format) does correctly on the
  *ingester* side where the body really is text.

- **Explicit schema version at the top.** `schema: anomalica/digest/1`.
  Future breaking changes bump the integer; consumers refuse what they
  do not understand. Mirrors the record format on the ingester side.

- **Folder named `records/`, file extension `.yaml` only.** Avoids the
  repetition of `anomalica-digests/extracts/...digest.yaml`. The
  parallel structure with `anomalica-ingests/records/{name}.md` makes
  the workbench join obvious: same filename in two repositories,
  different extension reflecting different content.

- **References use both id and name.** Every claim's `speaker` and each
  entry in `refs` carries `{id, name}`. The id is the canonical join
  key, robust to node renames. The name is included so a human reading
  the file can verify references without an identifier lookup, and so
  the file is useful as a standalone diagnostic artefact. Workbench
  joins on id.

- **Domain and infrastructure claims are separate top-level lists.**
  The two artificial-intelligence passes that produce them run
  independently, each populates its own database, and downstream code
  treats them as different things. Merging them into one list with a
  discriminator field would force every consumer to filter.

- **Dates: `date` (single) or `date_range` (interval), never both.**
  A two-element list is clearer than nullable end-date fields and
  matches the same shape any caller would build anyway.

- **Null and empty fields are omitted.** A digest with no
  infrastructure claims has no `infrastructure_claims` key, not
  `infrastructure_claims: []`. The schema is "what the file contains";
  absence is not a value.

- **Fixed field order.** At the root: `schema`, `extracted_at`,
  `model`, `record`, `nodes`, `domain_claims`,
  `infrastructure_claims`. Per node: `id`, `type`, `name`, optional
  `metadata`. Per claim: `id`, `type`, `attestation`, `speaker?`,
  `location?`, `date|date_range?`, `refs?`, `quote?`, `text`.
  Consistency makes the files diffable.

## Migration

The legacy markdown extracts in `anomalica-digests/extracts/` are
converted to YAML by the script `extract_to_yaml.py` in the digester
repository. The conversion preserves all universally unique
identifiers from the markdown source, so the rebuild produces a
byte-identical database before and after.

After conversion, the markdown extracts in `extracts/` are kept until
the workbench has been built against the YAML format, then removed.
The conversion is one-way; the digester no longer produces markdown.

## Consequences

- The interchange contract is now a written specification with a
  version identifier. Breaking changes bump the version and a new
  spec document is written; older consumers can detect mismatch.
- Refs and speakers carry both id and name, eliminating the
  comma-in-name escaping class of bug and giving the workbench a
  rename-robust join key.
- Producer and consumer code is simpler: standard YAML libraries
  replace a custom line-regex parser.
- The workbench can now be built against a stable, documented
  format. Mounting `anomalica-ingests/records/` and
  `anomalica-digests/records/` side by side, keyed by friendly
  filename, is sufficient for the "source -> ingest -> digest"
  three-column view.
- The one-off taxonomy fixers in `digester/reclassify.py` still
  operate on the legacy markdown format. They will be rewritten
  against YAML if and when a new taxonomy fix is needed; until then
  their work is already baked into the converted YAML corpus.
