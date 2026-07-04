# Relevance tuning mode: highlight-graded extraction

Status: SUPERSEDED by [0042](../0042-pre-digest-stage-and-eval-only-highlights.md) (2026-07-04). The completeness-required ("reviewed in full") highlighting proposed here is replaced by partial-first-class, evaluation-only highlights; the highlights sidecar and density-guided section sampling are folded into 0042. Kept for its reasoning trail. Owners: workbench (annotation UI + storage), digester (grading). Raised by: anomalica/digester, for Mark.

## Problem

The digester prompt has never defined what is *relevant* to extract. Every model
guesses, so output ranges from tight substantive facts to a tiny snippet inflated
into a filler sentence. Comparing model versions by claim count just ranks the
junk; a one-off human review of thousands of claims does not scale and is not
repeatable. We need a durable, source-anchored definition of "what a good
extraction should contain" that (a) lets us grade any model automatically and
(b) survives prompt changes so we can tune continuously.

## Mechanism

A **tuning mode** in the workbench, separate from review mode. Two panels:

- **Left**: the ingest source (the record body the digester extracts from).
- **Right**: controls + results.

The reviewer reads the whole document and **highlights every span relevant to the
subject (UAP and the people / organisations / programmes / events / evidence
around it)**, then ticks **"reviewed in full"**. That completeness flag is
load-bearing: only when the document is attested complete can an extracted item
that falls *outside* every highlight be counted as over-extraction (the padding
we want to eliminate) rather than merely un-reviewed. Without it we can measure
recall but not precision.

Highlights are stored as a sidecar on the record. Models are then run over the
same body and graded by span overlap against the highlights:

- **recall** = highlighted spans covered by at least one model item / total highlights
- **precision** = model items whose source span sits inside a highlight / total items
- **F1** per (model, document); plus the missed-highlights list and the
  off-target-items list for inspection.

Because every claim already carries its `quote` and `location`, and every node
its source mention, model output maps back to source spans directly (via the
existing re-aligner for fuzzy quote->span matching). One metric, no typing burden
on the annotator.

## Design decisions

- **No domain/infrastructure split at highlight time.** The annotator highlights
  only "relevant" - they do not classify. The distinction stays in the *model's
  output schema* (the assembler still needs `category=domain|infrastructure` to
  keep provenance like "aired on 60 Minutes, 2021-05-17" out of article prose),
  but it must not burden annotation.
- **Nodes generous, claims strict.** The digester cannot know corpus-level
  importance (a tangential person who matters because another source builds them
  up); that is the assimilator's job. So highlight/extract entities completely,
  but only substantive, non-filler claims. The junk is claims-side.
- **Fable pre-highlights a draft, the human corrects it.** Blank-page
  highlighting a 14-minute transcript is 20-30 minutes; correcting a draft is a
  few. The draft is advisory, never authoritative - the human's confirmed
  highlights are ground truth.
- **Accept/reject loop grows the ground truth.** After a run, surface model items
  that fall outside the highlights; the reviewer accepts (a genuine miss -> add to
  highlights) or rejects (over-extraction). The gold set tightens from what models
  surface, not only the first human pass.
- **Scope: a small eval set.** A handful of diverse, fully-annotated documents as
  a regression suite - not the whole corpus. Prompts are tuned against those few.
- **We do not train models** - we tune extraction prompts to hit the highlights.

## Data contract

Highlights sidecar, alongside the record in `ingests/store/`:

```
{hash}.highlights.json
{
  "schema": "anomalica/highlights/1",
  "record_hash": "<sha256>",         // the store filename hash (does NOT pin the body)
  "body_sha256": "<sha256>",         // sha256 of the exact text the offsets index
  "complete": true,
  "reviewed_by": "<pseudonymous reviewer id>",
  "reviewed_at": "<iso8601>",
  "spans": [                          // sorted by start, non-overlapping, text == body[start:end]
    {"start": <code-point offset>, "end": <code-point offset>, "text": "<span>", "note": "<optional>"}
  ],
  "rejected": [                       // optional: over-extractions already adjudicated as junk
    {"start": <code-point offset>, "end": <code-point offset>, "text": "<span>"}
  ]
}
```

Contract decisions (agreed with workbench, 2026-07-02):

- **Offsets index the RAW STORED BODY** - everything after the closing frontmatter
  fence, verbatim: no `.strip()`, no fence removal, no `{{t:}}` token stripping.
  This is self-contained against `record-format.md` and does not require the
  workbench to replicate the digester's internal cleaning. The digester owns the
  raw->clean derivation, so its grader maps model quotes (drawn from the cleaned
  body) back to raw-body spans via the re-aligner.
- **`body_sha256` pins the body.** `record_hash` does not - for audio/pdf it is
  over the source-file bytes, and workbench review edits the body in place without
  changing the filename. The grader warns/refuses on `body_sha256` mismatch; the
  workbench re-anchors spans via their `text` and rewrites the sidecar.
- **Offset unit: Unicode code points** (Python `str` indexing). The workbench
  converts from JS UTF-16 on its side.
- **`rejected`** lets the UI suppress already-judged over-extractions and the
  grader report known-junk separately from new junk.

Copyright: sidecars carry verbatim span text from possibly-copyrighted bodies -
they live in the same store and are served behind the same access gate as the
record body (no new exposure surface).

## Grading results contract

The digester emits results the workbench reads **read-only** (home: digester repo;
the ingests store stays records-only). Data flow is one-directional: the workbench
writes back only to the highlights sidecar (accept -> add to `spans`; reject ->
add to `rejected`).

```
grading/{body_sha256}.grading.json
{
  "schema": "anomalica/grading/1",
  "record_hash": "...", "body_sha256": "...",
  "graded_at": "<iso8601>",
  "models": [
    {
      "model": "...",
      "recall": <float>, "precision": <float>, "f1": <float>,
      "missed":    [{"start","end","text"}],                         // highlights no item covered
      "off_target":[{"start","end","text","kind":"claim|node","summary","overlap_fraction"}]
    }
  ]
}
```

Grading metric (digester's call): **overlap fraction, not strict containment.** An
item counts as in-highlight if >= 0.8 of its characters fall inside some highlight
span, after boundary normalisation (trim trailing whitespace/punctuation on both
sides). Raw fractions are reported so the threshold is tunable. `recall` = fraction
of highlight spans covered by any item; `precision` = fraction of items in-highlight.

## Work split

- **Workbench** (frontend + backend): the tuning-mode page, span-selection UI,
  the highlights sidecar read/write, the "reviewed in full" flag, and the
  accept/reject loop UI. Owns the annotation experience.
- **Digester** (this repo): the grader (quote/mention -> span mapping via the
  re-aligner, overlap metrics, per-model F1), the model-run harness (already built
  for the OpenRouter sweep), and folding the resulting relevance rules into the
  extraction prompt.

## MVP (on the navy-pilots record, in progress)

1. Segment 1 (first ~2 min) highlighted - Fable-drafted, Mark confirms.
2. Grader: overlap of model claim quotes vs highlight spans -> recall/precision/F1.
3. Run 3-4 models on the segment, grade each against the highlights, show the table.

Proves the mechanism end to end before the workbench UI is built.
