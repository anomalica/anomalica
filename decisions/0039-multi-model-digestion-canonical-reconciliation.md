# 0039. Multi-model digestion and canonical reconciliation

Date: 2026-06-21
Status: accepted (direction recorded; build deferred)

## Context

Today the digester produces ONE digest per ingest (`digests/records/{friendly-name}.yaml`, carrying `model: sonnet` - a single model, bare alias). Extraction quality varies by model and no single model is uniformly best. The project wants the option to digest one ingest with several models (Opus, Haiku, Sonnet, later non-Claude such as DeepSeek) and reconcile their outputs into one best digest - without the multiple outputs inflating evidence.

This makes the digester->digest relationship 1:N. The build is deferred (the model-comparison feature and a single-best-model come first; the ensemble lands once proven needed); this records the direction so the format and the evidence model are designed for it now.

## Decision

### 1:N model-digests

One ingest may be digested by N models. Each model's output is a full digest (schema `anomalica/digest/N`), stored as a separate, VERSION-named file so a new model release writes a new file and never silently overwrites a prior one. The model id carries its version (`claude-haiku-4-5`, `claude-opus-4-8`), matching the AI-ledger's model_id/model_version provenance ([0037](0037-ai-operation-ledger.md)).

### Canonical reconciliation

A reconciliation stage builds ONE canonical digest per ingest from all current model-variants:

- a small model clusters equivalent claims ACROSS the variant outputs (the same claim-clustering machinery used for entity consolidation, pointed at claims);
- it dedups same-fact-different-words and picks the best phrasing per fact.

The canonical is DERIVED: recomputed from all current model-variants whenever the variant set changes - order-independent and idempotent, NOT a stateful running merge. This mirrors the rebuildable-from-parts philosophy: the canonical is to the model-variants what the knowledge graph is to the digests ([0038](0038-graph-curation-replayable-ledger.md)). The model-variants are the primary, irreplaceable artefacts; the canonical can always be rebuilt from them.

### Only the canonical is assimilated

The assimilator imports ONLY the canonical. Model-variants stay linked to the ingest and are inspectable (workbench, audit) but are INERT - they never add claims, nodes, or evidence to the graph. Assimilation stays mechanical: replace-by-record (a changed canonical drops that record's old claims and imports the new); claim_hash content-addressing plus the staleness loop propagate improvements to articles automatically. The "genuinely better" judgement lives in reconciliation, not assimilation.

### The independence rule (load-bearing)

Multi-model extraction of ONE source produces ALTERNATIVES, not corroboration - it adds ZERO independence. The evidence/corroboration score must count independence by SOURCE / provenance-root, never by claim-count. The same rule kills wire-story-reprint inflation (one wire report reprinted across fifty outlets is one independent source, not fifty). This is a hard requirement on the evidence-scoring model (still undefined - [algorithmic-evidence-scoring draft](drafts/algorithmic-evidence-scoring.md), where it is also recorded).

## Naming and storage (reconciled with the live contract)

The live contract is one digest at `digests/records/{friendly-name}.yaml`, recursively globbed by the assimilator (`records.rglob("*.yaml")`) and joined to the ingest by the workbench on the friendly name. To add variants without disturbing that:

- **Canonical: `digests/records/{friendly-name}.yaml` - UNCHANGED.** Every downstream consumer (the assimilator glob, the workbench join, site references) keeps working byte-for-byte; the canonical IS "the digest" downstream.
- **Model-variants: `digests/variants/{friendly-name}/{model-id}-{version}.yaml`** - a top-level `variants/` tree, NOT under `records/`. This is deliberate: the assimilator globs `records/` RECURSIVELY (rglob, so a slashed record title can nest), so a variants subdirectory placed under `records/` would be silently imported. Keeping variants outside `records/` means the import never sees them, satisfying "only the canonical is assimilated" with zero change to the importer.

This rejects two parts of the first-cut proposal: the `.digest` extension (the workbench join, the round-trip tests, and every consumer expect `.yaml`; a rename is a gratuitous break) and a flat `{name}.{model}.yaml` alongside the canonical (it would pollute the `records/*.yaml` glob). The version-in-the-filename requirement is met by the `{model-id}-{version}.yaml` variant names; the per-record `variants/{friendly-name}/` directory follows the existing `{stem}.compare/{model}.{ext}` lineage of the model-comparison tooling.

## Schema impact

A digest schema bump (`anomalica/digest/2`) lands WITH the build, not now:

- `model` carries the versioned id (today it is the bare alias `sonnet`);
- the canonical gains `reconciled_from` (the set of model-variant ids+versions it was built from) - its presence distinguishes a canonical from a model-variant;
- optionally, per-claim variant provenance (which variant(s) a claim came from, which phrasing won) for audit and the AI-ledger.

Until the build, digests stay `anomalica/digest/1`, one per record, `model: <alias>`.

## What does NOT change

- **The ingest contract ([record-format.md](../architecture/record-format.md)) is untouched.** The 1:N is entirely digester-output-side; one ingest per source as before.
- **Assimilation stays mechanical** (replace-by-record); the new judgement is confined to reconciliation.
- **claim_hash / staleness** unchanged - they propagate canonical improvements automatically.

## Cross-component impact

- **AI-ledger ([0037](0037-ai-operation-ledger.md))**: reconciliation is an AI call - its operation enum gains `reconcile` (small model, subscription/api). Each model-variant digestion is an `extract` call, already ledgered per model_id/version.
- **Reconciliation reuses the claim-clustering machinery** used for consolidation/corroboration - pointed at cross-variant claims rather than cross-record entities.
- **Evidence scoring** must implement the independence rule before any multi-model or multi-reprint corpus is scored.

## Build status

Direction accepted; build deferred. Order: the model-comparison feature and single-best-model first; the ensemble (N-model + reconciliation) once proven needed. The format, the storage layout, and the evidence model are designed now so the build is additive.

## Scope

A pipeline-contract change (digester->digest becomes 1:N plus a reconciliation stage), a derived canonical with rebuildable-from-parts semantics, a storage layout reconciled with the live digest contract, a deferred `anomalica/digest/2` bump, and a hard independence requirement on evidence scoring. The living docs (overview, data-model, digest-format) carry the direction; this record carries the decision.
