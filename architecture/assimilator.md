# Assimilator

The assimilator builds and maintains the unified SQLite knowledge graph (a structured database of interconnected facts) from digest YAML files. The digester produces one digest per record (extraction); the assimilator folds those digests into a single cross-corpus graph, resolves entities across records, scores evidence, and maintains the graph over time. It is the stage between the digester and the assembler:

```
ingester -> digester (digest YAML) -> assimilator (knowledge graph) -> assembler -> content -> site
```

The split from the digester is recorded in [decision 0034](../decisions/0034-split-digester-extraction-from-assimilation.md): extraction (digester) and graph assimilation (assimilator) are genuinely different jobs - per-record and AI-heavy versus cross-corpus and stateful.

## Inputs

Digest YAML files (the interchange format, [decision 0027](../decisions/0027-digest-interchange-format.md)), each holding the nodes, claims, and provenance extracted from one record. The assimilator reads them via the shared `anomalica-common` library (`anomalica_common.digest`), which single-sources the format so the digester (producer) and assimilator (consumer) cannot drift.

## Outputs

Two SQLite databases at `~/.local/share/assimilator/` (overridable via `ASSIMILATOR_DB`), with identical schema, split by claim category at import: `knowledge.db` (domain claims - the publishable knowledge graph) and `infrastructure.db` (infrastructure claims - source-graph cross-references). The assembler reads `knowledge.db` only; "the knowledge graph" as a public artefact means the domain database. The full table schema is in [graph-schema.md](graph-schema.md). Both are derived data, rebuilt deterministically from the digests (the source of truth); if deleted, rebuilt from the digests. Embedding vectors are a separate derived index (sqlite-vec), kept out of the relational contract and out of the primary download.

## What it does

### Import
Folds digest YAML into the graph. `assimilate <dir>` is the incremental path (folds new and changed digests into the existing graph); `rebuild <dir>` builds from a clean slate; `import <digest>` takes a single digest file. (Module: `import_markdown`.)

### Entity resolution and matching
Resolves nodes across records: "David Grusch" in one transcript and "Grusch" in another become the same node, via alias matching. This is the cross-corpus step the per-record digester cannot do - it sees only one record at a time. (Module: `matching`.)

### Provenance chains
Every claim carries a provenance chain showing how it reached the graph. When multiple records carry the same claim, the assimilator traces whether they are genuinely independent or derived from a common origin. If CNN, BBC, and Reuters all report the same Pentagon press release, that is one first-hand claim with three second-hand repetitions, not four independent corroborations. Two claims corroborate each other only if their provenance chains do not share a root.

### Scoring
Evidence scores are algorithmic, not editorial - no human assigns a score. Inputs: the count of independent corroborating sources (provenance chains must not share a root), attestation depth, source track record, contradictions, and evidence type. (Module: `scoring`.) The scoring model itself remains an open design (the algorithmic-evidence-scoring draft). Scoring also derives the source properties - track record, correction behaviour, independence - defined in [data-model.md](data-model.md).

### Corroborate (AI-assisted)
`corroborate` is the one AI-assisted graph pass wired today: cross-record same-fact verification (does a claim in record A assert the same fact as a claim in record B?). A related AI-assisted claim de-duplication function, `deduplicate_claims`, exists in the `consolidate` module but is not yet wired to a command.

### Embeddings and hybrid search
Generates vector embeddings for nodes and claims and provides hybrid (vector plus keyword) search over the graph. (Modules: `embeddings`, `search`; commands: `embed`, `search`.) Embeddings are stored separately from the core data.

### Obsidian export
Exports the graph to an Obsidian vault for browsing. (Module: `obsidian_export`; command: `export-obsidian <dir>`.)

### Digest-maintenance passes
Cross-corpus passes that maintain the digests and graph as conventions evolve - the one-off migrations that follow a taxonomy or format change: `reclassify-documents`, `normalise-names`, `migrate-refs-delimiter`, `rewire-refs`, `backfill-record-fields`. (Modules include `backfill`, `reclassify`.)

## Modules

`database`, `import_markdown`, `matching`, `consolidate`, `scoring`, `embeddings`, `search`, `obsidian_export`, `backfill`, `reclassify`, `cli`.

## Command-line surface

`assimilate <dir>` (incremental), `import <digest>`, `rebuild <dir>` (clean slate), `stats`, `show <name>`, `embed`, `corroborate`, `search <query>`, `export-obsidian <dir>`, plus the maintenance passes above.

## Shared library

The assimilator depends on `anomalica-common`:

- `anomalica_common.digest` (`models.py`, `yaml_format.py`) - the digest data model and YAML read/write (0027), used to read digests. Single-sourced so the format cannot drift between the digester and the assimilator.
- `anomalica_common.llm` (`transport.py`, `cost.py`, `gate.py`) - the Claude transport with the subscription-default / metered-API toggle, the cost estimator, and the spend gate. The AI-assisted passes (corroborate, and consolidate once wired) call through it, so the assimilator enforces the same billing policy and spend gate as the digester.
