# Digester

The digester takes a reviewed ingest and runs two-pass artificial-intelligence extraction over it, producing a digest: a YAML file of the nodes, claims, and provenance found in that one record. It does extraction only - it builds no knowledge graph. Folding digests into the unified graph (import, cross-record entity resolution, scoring, corroboration, search, maintenance) is the assimilator's job (see [decision 0034](../decisions/0034-split-digester-extraction-from-assimilation.md) and [assimilator.md](assimilator.md)).

## Inputs

Reviewed ingests from the access-controlled ingests repository - markdown files with YAML frontmatter and annotation blocks in the record interchange format ([decision 0019](../decisions/0019-record-interchange-format.md)). The digester reads them (`record_parser`) and checks digestibility via `review_gate` (the observed-coverage check behind the `coverage` command); it does not process raw source material (the ingester does that).

Each ingest may have associated media at `media/{record_hash}/` (extracted images). When the digester reaches an image annotation with a `file` field, it loads the image bytes and passes them to a vision-capable model alongside the surrounding text, so claims can be extracted from charts, photographs, and figures, not just prose. The digester also populates the `description` field on image annotations (a factual description for consumers that lack vision), writing it back into the ingest.

## Processing

Two-pass artificial-intelligence extraction - a nodes pass and a claims pass:

### Node identification

Identifies the domain nodes the record mentions: person, organisation, project, place, event, object, document, topic (the taxonomy and classification rules are in [node-types.md](node-types.md)). This is per-record - the digester sees one record at a time and does not resolve nodes across records; that cross-corpus matching is the assimilator's.

### Claim extraction

Decomposes the record into atomic claims - the smallest independently verifiable assertions - each linked to its location in the record (timestamp range, page, paragraph) and its speaker, with a claim type and optional attestation and claim role. The claim-text conventions (SI units, assertion-not-reported-speech, question-and-answer handling) are in [node-types.md](node-types.md).

### Timestamp realignment

For word-timestamped audio and video records, extraction runs against a timestamp-stripped view and claim locations are realigned to the word timestamps afterwards (module: `realign`).

## Outputs

One digest YAML file per ingest ([decision 0027](../decisions/0027-digest-interchange-format.md)), written to the public digests repository. A digest contains no copyrighted content - only atomic facts, structured metadata, and references back to the original record. The digester writes no database and no graph; the assimilator imports the digests and builds the graph.

## Modules and command-line surface

Modules: `extract` (two-pass extraction), `record_parser` (reads records), `realign` (quote-to-timestamp re-alignment), `review_gate` (the digestibility / observed-coverage gate behind the `coverage` command), and `cli`. Command-line surface: `extract`, `batch-extract`, `coverage`.

The data model and the transport are not the digester's own: it reads and writes digests through `anomalica_common.digest`, and calls the model through `anomalica_common.llm` (the shared Claude transport), so the format and the transport stay identical to the assimilator's.

## Testing

Extraction is tested against a small, focused corpus centred on records from a few people who represent different source types - an eyewitness, a whistleblower, an insider who went public, and an investigative journalist - exercising claim extraction, attestation, claim types, and vision extraction across formats (transcripts, audio, web, ebooks and PDFs). The corpus is intentionally small (roughly 20-30 records) so output can be verified by hand. Graph-level behaviour (cross-record resolution, provenance independence, corroboration, scoring) is tested in the assimilator, not here.
