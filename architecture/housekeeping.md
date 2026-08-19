# Housekeeping

A recurring pass that improves the **frontmatter** of already-ingested records and
proposes the changes for human approval. It never edits body prose, and it never
applies a change itself.

Status: specified 2026-08-19, not yet built. This document is the contract; the
implementation notes at the end say what exists and what does not.

## Why it exists

Two problems the pipeline has no answer for today.

**Records carry frontmatter nobody has ever checked.** 288 records were ingested by
four different handlers over five months, with the format changing underneath them.
Fields are missing, mistyped, or wrong, and the only mechanism for fixing them is a
human opening each record.

**The work-versus-copy distinction is specified but not applied.** The provenance
block in [ingest-format](ingest-format.md) added `posted_by`, `posted_date` and
`container_title` on 2026-08-18 to separate *the work* from *the copy the fetcher
saw*: a 1987 broadcast reposted to YouTube by "Eyes On Cinema" has that channel as
`posted_by`, not as `publisher`. Existing records predate the field and file the
redistributor as the originator. That document is explicit that the correction is
**not mechanical corpus-wide** - moving `publisher` to `posted_by` is right where the
channel is a redistributor and destroys a true publisher where it is not. It needs
per-record judgement on 288 records.

Per-record judgement at corpus scale, where being wrong is cheap to catch and
expensive to miss, is what an AI proposal with human approval is for.

It also aims at the real bottleneck. 214 of 288 records have never been reviewed, and
that - not throughput upstream - is why nothing reaches the site. Anything that
reduces the per-record cost of review is worth more than anything before it.

## Shape

```
scheduler ──stages a housekeeping job──▶ worker (local, subscription only)
                                              │
                                              │ reads  ingests/store/{hash}.md
                                              │ writes ingests/store/{hash}.housekeeping.json
                                              ▼
                                        proposal sidecar (committed to ingests)
                                              │
                                              ▼
                              workbench ──Housekeeping tab──▶ human approves
                                              │                per ITEM, not per record
                                              ▼
                                   approved items applied to the record,
                                   committed as a SEPARATE commit
```

Four properties, in priority order:

1. **The worker proposes; it never applies.** Every change reaches a record through
   a human approving it in the workbench.
2. **Body prose is untouchable.** The worker reads the body as evidence and writes
   only frontmatter. Enforced, not promised - see [Safety](#safety).
3. **Each proposed change is approved or rejected on its own.** A record with seven
   proposals can have three accepted. A patch is not all-or-nothing.
4. **Subscription only.** Housekeeping runs on Mark's Claude plan. It must never
   reach the metered API or OpenRouter, and it must stay well under the plan
   allowance so it cannot consume what he needs for his own work.

## Why these homes

**Worker in the `scheduler` repo, not a new repo.** The Claude subscription is a
local CLI login, so the worker has to run on Mark's machine - "run it in the cloud"
is not available for the model calls. The scheduler already has the queue, the
staging model, the usage-gated dispatch and the allowance ceilings, and already runs
locally. A sixteenth repo would duplicate all of it, and the project already carries
a bind-mount problem across the repos it has.

**Proposals as sidecars in `ingests`, not a new data repo.** `{hash}.verification.json`
already establishes the pattern of a per-record sidecar beside the record. Sidecars
commit to `ingests`, and `ingests` is what the workbench reads - so a proposal
written locally reaches the online reviewer with no new transport.

**Review in the `workbench`, as a new tab.** It is already deployed, already reads
`ingests`, and already commits reviewer corrections back. Approval is a review
action; it belongs with the other review actions.

## The proposal sidecar

`ingests/store/{content_hash}.housekeeping.json`. One per record. Holds the
record-level "has been checked" marker and a list of independently-decidable items.

The authoritative schema is in [housekeeping-format.md](housekeeping-format.md).
The properties that matter architecturally:

- **`checker_version`** - the record-level marker that prevents re-checking. A record
  whose sidecar carries the current version is skipped. Bumping the version is how you
  force a corpus-wide re-check after improving the checks; there is no separate
  "re-run" flag to get out of sync.
- **Per-item `status`** - `proposed` | `approved` | `rejected`. Set by the reviewer,
  not the worker. A rejected item stays in the file: it is the record of a decision,
  and it stops the next run from proposing the same thing again.
- **Per-item `evidence`** - what justified the change. For a research-backed item this
  includes the source URL. An item with no evidence is not a proposal, it is a guess,
  and the worker must not emit one.
- **Per-item `confidence`** and the model/prompt provenance, so a reviewer can weight
  a proposal and so a bad prompt version can be found later.

## Safety

**Frontmatter only, enforced mechanically.** Applying an approved item parses the
record, replaces a frontmatter value, and re-serialises. Before committing, the body
is compared byte-for-byte with the body before the edit. Any difference aborts the
apply. The worker therefore cannot alter prose even if a model returns it, and the
guarantee does not depend on reviewing diffs carefully.

**Subscription pinned at dispatch.** The scheduler already forces `INGEST_USE_API=0`
and `DIGESTER_USE_API=0` and strips `INGEST_SPEND_CONFIRMED` and `ANOMALICA_USE_API`
from the child environment. Housekeeping is pinned the same way and additionally
must refuse any OpenRouter model id outright, rather than relying on it not being
selected.

**Its own allowance ceiling, below the global one.** The plan ceilings exist so a
runaway job cannot hard-throttle the plan and take every session down with it.
Housekeeping is background work competing with Mark's own use, so it stops earlier
than the global ceiling rather than at it.

**Deterministic checks never call a model.** A missing required field, a date written
at the wrong precision, a `creators` list that failed to parse - these are decidable
from the file. Spending allowance on them is waste, and a model asked an
already-answered question is an opportunity to be wrong.

## Checks

Ordered by value, not by ease. The first is the reason the component exists.

1. **Redistributor filed as publisher.** Where `publisher` names a channel that
   reposts other people's work, propose moving it to `posted_by`, and clearing
   `date_published` where the existing value is the repost date rather than the
   work's. Needs judgement and often research: deciding that "Eyes On Cinema" is a
   redistributor and that the underlying work is a 1987 broadcast is exactly the call
   [ingest-format](ingest-format.md) says cannot be made mechanically.
2. **Missing `container_title`.** The journal, book or programme a work appeared in.
3. **Unidentified speakers.** Diarised transcripts carry `<!-- speaker: Speaker 1 -->`
   markers. Where the transcript names the speakers, propose the mapping. The model
   returns a mapping only - `{"Speaker 1": "Ross Coulthart"}` - and code performs the
   substitution, so the model never emits document text. Names must resolve against
   the known-entity list or be flagged as new rather than written. The mapping must
   support many-to-one (diarisation splits one person across labels) and must have an
   explicit "unknown" so a second guest is not invented to fill a label.
4. **Deterministic field hygiene.** Required-field presence per `source_type`, date
   precision written per the quoting rule, `creators` that parse as a list. No model.

## Open questions

- **Web research on the subscription path.** The transport calls `claude -p` with
  tools disabled, which is what makes it a clean single-shot completion. Research
  checks need search. Whether search can be enabled without giving the pass a general
  agentic tool surface decides whether check 1 is buildable as specified, or whether
  research has to be a separate deterministic fetch step feeding the model.
- **Approval write path in the deployed workbench.** The public workbench is a static
  snapshot plus an edge function. Reviewer writes today go through a path that needs
  establishing before the tab is built; approval must reuse it rather than add a
  second writer.
- **Housekeeping's own ceiling number.** Lower than the global session/weekly
  ceilings. The value should come from measuring a real pass, not from a guess.

## Relationship to review

Housekeeping is not human review and does not substitute for it. A record that has
been housekept has had its metadata examined; its body has not been verified against
the source. The two states are independent and a housekeeping pass must never mark a
record as reviewed.

Housekeeping runs on records that have **not** yet been human-reviewed, or its
proposals are applied as a clearly separate commit. Landing metadata edits on a
record after sign-off silently changes something already approved.
