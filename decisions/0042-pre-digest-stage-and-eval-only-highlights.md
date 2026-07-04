# 0042. The pre-digest stage, and highlights as evaluation-only

Date: 2026-07-04
Status: accepted

Supersedes the [relevance-tuning-mode draft](drafts/relevance-tuning-mode.md) - its highlight-completeness grading is replaced by the eval-only model below; the rest (the highlights sidecar, section sampling) is folded into this record.

## Context

The digester reads an ingest and extracts claims. But the model never sees the ingest verbatim: deterministic prep is applied first - irrelevant regions removed, footnotes inlined, word-timestamps stripped. Today that prep, where it happens, is a transform hidden inside the digester, so the exact text the model read is not inspectable. Every other pipeline stage is a materialised, inspectable artefact (ingest, digest, graph, brief, content); the model input is the one exception.

Separately, the relevance-tuning draft proposed grading extraction against human highlights, but required a reviewer to highlight a document IN FULL ("reviewed in full") before precision could be derived. That is a high bar that does not match how people actually highlight - casually and partially.

## Decision

### The pre-digest: a materialised model-input stage

A new derived, read-only artefact between the ingest and the digest: **the ingest after all DETERMINISTIC model-prep**. It IS exactly what the digester extracts from - there is no further hidden transform inside the digester.

The prep is deterministic:

- **Irrelevant regions removed** - from the human `[irrelevant]` marks: prose `<!-- irrelevant: start -->` / `end` regions and transcript `<!-- speaker: [irrelevant] -->` segments ([record-format.md](../architecture/record-format.md#irrelevant-content)).
- **Footnotes inlined** at their reference points - deterministic, from standard Markdown `[^N]` / `[^N]:` syntax.
- **Word-timestamps stripped** (transcripts).

Properties:

- **Read-only + derived.** Corrections never edit the pre-digest; a reviewer fixes the SOURCE (the ingest marker) and the pre-digest is re-derived. One-way data flow is preserved - the pre-digest is a consuming stage's output, never written back into.
- **Reproducible + auditable.** The digest records the pre-digest's content hash; `(pre-digest hash + prompt version + model)` makes a digest exactly reproducible and auditable. This composes with the prompt-provenance already shipped (the `prompts` block, [0039 amendment 2026-07-04](0039-multi-model-digestion-canonical-reconciliation.md)).

### Stored, not regenerated-on-demand

The pre-digest is MATERIALISED per record and stored, not regenerated-on-demand with only its hash recorded. Reasons, strongest first:

- **The stage's own motivation is materialisation.** "Every stage is a materialised artefact, so make the model-input one too" is the whole point; a regenerate-on-demand pre-digest would be the single non-materialised stage, defeating it.
- **Exact audit.** The digest's recorded pre-digest hash always verifies against a stored file. Regeneration reproduces the exact input only if every historical version of the prep logic stays runnable; when the prep improves, regeneration drifts and the recorded hash becomes unverifiable. Storing removes that risk.
- **The inspectable journey.** The exact input that produced a historical digest can be diffed, because old pre-digests are preserved rather than overwritten.

Cost is negligible (derived text). It stays derived - rebuildable from the ingest plus the versioned prep - so a lost pre-digest is regenerable; the stored copy is the authoritative record of what the model actually saw. It is content-addressed by its own hash and recorded in the digest; the exact store path and prep-version field land in [record-format.md](../architecture/record-format.md).

### Highlights are evaluation-only, never shown to the model

Highlights are an EVAL signal only - never part of the pre-digest, so the model never sees them. This avoids biasing the model and avoids aided/unaided variants.

- **Casual, PARTIAL highlighting is first-class.** The "reviewed in full" completeness requirement is dropped. People highlight whatever catches their eye.
- **Use 1 - corpus-wide COVERAGE check:** did highlighted content survive into the digest output? A recall/coverage signal ONLY. Precision cannot be derived from partial highlights - an unhighlighted extraction is not wrong, it was merely not flagged.
- **Use 2 - highlight-density-guided SAMPLING:** dense-highlight regions surface bounded SECTIONS (a book page, a 5-minute video segment) as candidates for a human to fully hand-digest into a gold standard, which gives real precision AND recall on that section - not on whole documents. This also rewards more highlighting (a virtuous cycle).
- **Grader consequence.** The digester's grader (`benchmarks/relevance/put_and_grade.py`) computes precision assuming complete highlights. Under casual highlights the corpus-wide check becomes coverage-only and precision moves to the section gold standards; the digester adjusts the grader accordingly.

### Inspection surface

A read-only **`pre-digest` tab** in the workbench, beside ingest / edit / raw / diff / meta. RENDERED (bullets, headings, page boundaries - not raw), showing the model input, with the exact versioned prompt displayed alongside (collapsible, in a distinct colour). The tab is the complete, honest picture of everything the model receives.

## Why

- **Inspectability is the point.** A silent in-digester transform cannot be audited; a materialised pre-digest can - and it is the exact model input, not a reconstruction.
- **Reproducibility composes.** `(pre-digest hash + prompt version + model)` pins a digest exactly, extending the prompt-provenance work.
- **Eval-only, partial highlights match reality.** They avoid biasing the model, and precision comes from bounded gold-standard sections rather than an unrealistic complete-highlight bar.

## Consequences

- The digester materialises the pre-digest (deterministic prep) and extracts from it; the digest records the pre-digest hash.
- [record-format.md](../architecture/record-format.md) gains the pre-digest artefact and its store layout; [overview.md](../architecture/overview.md) gains the ingest -> pre-digest -> digest step in the data-flow story.
- The architecture diagram gains a pre-digest node between the ingest and the digester (`reference/pipeline.mmd` + `reference/architecture.yaml`) - deferred until the shape is confirmed, to avoid churning the just-revised diagram.
- The workbench gains the read-only pre-digest tab.
- The digester's grader shifts to coverage-only corpus-wide plus section gold standards.
- Supersedes the relevance-tuning-mode draft's completeness-required highlighting; folds its highlights model into this accepted record.

## Scope

A new materialised pipeline artefact (the pre-digest) between ingest and digest - stored per record, content-addressed, hash-recorded in the digest for exact reproducibility - and a reframing of highlights as a partial-first-class, evaluation-only signal (coverage corpus-wide, precision from sampled gold-standard sections). Builds on record-format.md (the irrelevant marks and footnote/timestamp handling it derives from) and 0039 (prompt-provenance, digest reproducibility); supersedes relevance-tuning-mode.md.
