# 0046. Digestion before review, for non-transcript formats

Date: 2026-08-22
Status: accepted

## Context

The project has held that the knowledge graph must not be built from
unreviewed material. Review throughput has made that untenable: 288
records stand against one reviewer, and the graph, the article pipeline,
and every signal derived from them wait on a queue that cannot drain at
the rate the corpus grows.

Two things about the existing position matter before reversing it.

**It was a principle, not a mechanism.** Measured 2026-07-29: nothing in
the digester enforces a review verdict. `assess_record` is reached only
from the `coverage` reporting command; extraction never consults it. So
unreviewed material has always been digestible in practice, and this
record does not remove a safeguard - it decides deliberately what was
previously true by accident, and adds the visibility that was missing.

**Review is not one thing across formats.** For a PDF or a web article,
review is verification: a human confirming an extraction that is already
faithful. For a whisper-derived transcript it is *completion* - speaker
naming and diarisation repair are what make the artefact digestible at
all. Those are different acts, and treating them under one rule is what
made the single gate wrong in both directions.

## Decision

**Non-transcript formats - `pdf`, `web`, `ebook`, `image` - may be
digested before human review.** Digestion is auto-queued after ingest.

**Audio and video remain gated.** A whisper-derived transcript requires
human review before digestion, because the review is part of producing
the material rather than checking it. This is not a quality preference
and must not be relaxed on throughput grounds; the artefact is
incomplete until a human has named the speakers.

**A digest records the source's review state at extraction time.** The
field is provenance - "this extraction ran on unreviewed material" - and
sits with `prompts`, `pre_digest` and `ai_usage` as an extraction-time
fact. Field contract in
[digest-format.md](../architecture/digest-format.md#review_state).

**Nothing resolves current review state from that snapshot.** The ingest's
review sidecar is the single source of truth, and anything that gates
behaviour - the assimilator's page gate, the assembler, review-priority
ranking - resolves the *current* state from the record at import or
rebuild. So a review upgrades the graph immediately, with no
re-digestion, and no snapshot goes stale into a decision.

**Nothing downstream refuses a preliminary digest yet.** Pages still
build. The point of this record is visibility, not enforcement.

**The graph gains a review-priority signal**: an unreviewed or partially
reviewed record whose claims feed published pages ranks high for human
attention. A reviewer cannot read 288 records; this says which ones
matter.

**Digestion of unreviewed non-transcript records is low priority.** The
scheduler dispatches it only when nothing higher is pending - reviewed
content, and transcription - so it consumes leftover capacity and never
displaces work that is already verified.

## Consequences

Three things follow that are easy to get wrong.

**"Preliminary" is a statement about provenance, not quality.** An
extraction from an unreviewed PDF is unverified, not inferior; the same
prompt and model produced it. If it ever becomes a weight in scoring,
that is an editorial position and belongs in
[editorial-style.md](../guides/editorial-style.md) with its reasoning,
never as a coefficient - a number that silently discounts unreviewed
material would be exactly the buried judgement that guide forbids.

**Absent is not unreviewed.** A digest written before this record carries
no review-state field at all, and that must not read as "ran on
unreviewed material". The field distinguishes *unreviewed*, *reviewed*,
and *not recorded*, or it recreates the absence-as-a-value failure this
project has met repeatedly.

**Review is not binary, so neither gate nor signal can be.** Coverage is
measured per section ([ingest-format.md](../architecture/ingest-format.md#review-units-a-book-is-not-a-big-article)),
so a record is reviewed in parts. The audio gate therefore needs a stated
threshold rather than a true/false verdict, and the priority signal is
naturally continuous - a record whose reviewed sections are precisely the
ones feeding published claims needs no further attention, while one
reviewed everywhere except there is the most urgent case in the corpus.

One scoping note for the priority signal: page-*worthiness* is gated on
evidence scoring ([0041](0041-proposals-and-the-two-brief-pipeline.md)),
so keying the signal on "feeds a published page" - which is concrete and
available now - avoids blocking it on a threshold that has not landed.
