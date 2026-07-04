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

The assimilator imports ONLY the canonical. Model-variants stay linked to the ingest and are inspectable (workbench, audit) but are INERT - they never add claims, nodes, or evidence to the graph. IMPORT stays mechanical: replace-by-record (a changed canonical drops that record's old claims and imports the new); claim_hash content-addressing plus the staleness loop propagate improvements to articles automatically. But the assimilator MAINTAINS the graph, it is not merely an importer: claim dedup, supersede, and corroboration-linking are a curation pass over the graph (see [Claim dedup](#claim-dedup-provenance-overlap-not-hash)). The "genuinely better" judgement lives in reconciliation (across model-variants) and graph maintenance (across claims), not in import.

### The independence rule (load-bearing)

Multi-model extraction of ONE source produces ALTERNATIVES, not corroboration - it adds ZERO independence. The evidence/corroboration score must count independence by SOURCE / provenance-root, never by claim-count. The same rule kills wire-story-reprint inflation (one wire report reprinted across fifty outlets is one independent source, not fifty). This is a hard requirement on the evidence-scoring model (still undefined - [algorithmic-evidence-scoring draft](drafts/algorithmic-evidence-scoring.md), where it is also recorded).

### Claim dedup: provenance-overlap, not hash

How does the graph dedup semantically-equivalent claims, when a content hash cannot (different phrasing, same fact)? The PRIMARY signal is PROVENANCE OVERLAP, not semantics. Each claim already carries its `record_id` and `location_in_record` (the lines/timestamp it was extracted from); these are the inputs:

- **Same source + overlapping location = a DUPLICATE.** Same extraction, different phrasing - including the multi-model variants of one source. Collapse by SUPERSEDE (the worse claim retired, the better kept as canonical). This is NOT corroboration; it adds zero independence.
- **Different sources, same fact = CORROBORATION.** Keep BOTH claims, both linked to their entity nodes, counting as independent support. Must NOT be collapsed. (This already has a home: the `corroborations` table, populated by the `corroborate` pass, and `scoring.py` already counts independent RECORDS, not raw claims.)

Provenance overlap thus deterministically separates dedup (same-source) from corroboration (cross-source) - this IS the independence rule operationalised (count independence by provenance root). It is cheap and needs no model for the common case.

For the cases provenance cannot settle - same source, different lines, but the same fact; or judging whether two cross-source claims are the same fact for linking - a cheap-model judge surfaces candidate claim-duplicate CLUSTERS, which go through the SAME curation machinery as entity merges, pointed at claims (propose -> confirm -> supersede), recorded as reversible curation in the ledger and replayed on rebuild ([0038](0038-graph-curation-replayable-ledger.md), extended from nodes to claims).

SUPERSEDE semantics: a superseded claim is retired like a merged node - kept linked and inert for audit, never feeding the synthesiser. (Claims have no retired/superseded column today; it is net-new, landing with the build, mirroring nodes' `retired_at`.) The synthesiser also guards at SELECTION - it refuses two same-source-overlapping claims on one page - belt-and-braces over the maintenance pass.

This is also what reconciliation (above) IS for the multi-model case: the model-variants of one source are same-source + overlapping-location, so they are duplicates, superseded down to the one canonical.

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

## Amendment (2026-07-02): the digest selector - selection, not fusion

Reverses the 2026-06-27 "digest fuser" framing (which never shipped): multi-model reconciliation is now **selection of the single best per-model digest**, not claim-level fusion. A source is digested by several models (1..N), one digest per model; the **digest selector** picks the single best of those whole digests. It does NOT merge them - the earlier "collapse equivalent claims into one canonical claim" step is dropped in favour of choosing one whole digest.

- **Naming.** The reconciliation stage is the **digest selector**; its output is the **selected digest** (one per source); the inputs are the **per-model digests** (one per model, 1..N). (Reconciliation / canonical remain valid synonyms in the body above; the diagram uses selector / selected digest.)
- **Selection is whole-digest, not claim-level.** The selector chooses one entire per-model digest as the best; it does not match or merge claims across models. Simpler than the fusion it replaces, and it removes the cross-model claim-matching step. (Cross-SOURCE claim dedup and corroboration - a different job - still use the claim-clustering machinery above; only cross-MODEL reconciliation becomes selection.)
- **Selection stays rebuildable.** The selected digest is a pure function of the current per-model digests - recomputed, idempotent, never stateful - so it is always rebuildable from them. The supersession diff (the selected digest changed from model A's to model B's) is a diff of derived artefacts, itself reproducible.
- **The selector's materiality judgement is the staleness signal.** Whether a selection change is material (meaning moved) or cosmetic decides whether a downstream page regenerates - a staleness *degree* feeding the brief-hash staleness loop. Unchanged from the fuser framing.
- **Two stores.** The digester emits **per-model digests** (one per model, 1..N per source); the selector produces the **selected digest**. Only the selected digest is assimilated; the per-model digests are the rebuildable inputs. Pipeline: digester -> per-model digests -> selector -> selected digest -> assimilator.
- **Review influences the selector; it does not edit digests.** Reviewers review the selection - which model's digest was picked - and express a preference ("this model's digest is better"), a **replayable record the automated selector replays** (the graph-curation pattern, [0038](0038-graph-curation-replayable-ledger.md)). Rebuildable = automated selection + replayed human preference.

The digester's fuser->selector CODE rename is a follow-up, not done here.

Architecture diagram source (the selector node): `reference/pipeline.mmd` + `reference/architecture.yaml` in the meta-repo.

## Amendment (2026-07-04): variant naming carries the prompt identity

The storage layout was built ahead of the deferred reconciliation, as the
"stop overwriting on re-digest" step. The 0039 variant name `{model-id}-{version}.yaml`
(model version only) predates prompt-provenance (`prompts` block in the digest;
see [digest-format.md](../architecture/digest-format.md)). A re-digest is
usually the SAME model with a TUNED prompt - the tuning loop's common case - so
a model-only key would overwrite exactly the prior output we mean to preserve.

Variants are therefore named
`variants/{friendly-name}/{model-id}.{prompt-sha8}.yaml`, where `prompt-sha8` is
an 8-char digest of the passes' combined prompt sha256s. (model X, prompt v2)
and (model X, prompt v3) coexist as comparable variants; an identical
model+prompt run overwrites only its own file (correct redo semantics).

Canonical fill, until reconciliation lands: `records/{friendly-name}.yaml` is
latest-written by a PRODUCTION run. A run with a prompt override in effect (any
`prompts` entry at `version: override`) writes its variant only and never
touches the canonical, so tuning-loop experiments cannot leak into the graph.
A `--variant-only` flag forces variant-only even for an active-prompt side-run
(benchmarks). Implemented in `digester/digest_store.py`, wired into the
`extract` / `batch-extract` CLI via `--digests-root`.
