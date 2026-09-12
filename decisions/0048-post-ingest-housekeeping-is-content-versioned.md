# 0048. Post-ingest housekeeping is content-versioned

Date: 2026-09-11
Status: accepted

## Context

Housekeeping already produces reviewable sidecars and never applies its own
proposals. Its scheduler trigger and completion identity were not settled. The
existing `checker_version` skip rule ignores edits and in-place re-extraction,
because a record's stable `content_hash` identifies its source and selection,
not the Markdown bytes currently stored.

The scheduler also cannot safely infer an ingester's output from an intake hash.
Duplicate handling, supersession and source-based identity mean the produced
live record may not have that name. The ingester is the component that knows
which committed record resulted.

The first deterministic body correction is the known acronym error `OSSAP` to
`AAWSAP`. Housekeeping version 1 permits frontmatter operations only. Adding a
body operation without a narrower mechanical guard would silently reverse its
strongest safety property.

## Decision

### The ingester reports its committed result

Every successful ingest or no-op duplicate resolution emits one structured
`anomalica/ingest-result/1` result after verifying the repository commit that
contains the live record. It names a scheduler-supplied run UUID, outcome,
produced repository-relative record path, canonical `content_hash`, commit SHA
and completion time. It is written atomically to the scheduler-supplied result
file outside the ingests Git repository and emitted on stdout with the fixed
`ANOMALICA_INGEST_RESULT ` prefix. The scheduler rejects a pre-existing result
path; a failed exchange retries under a new run UUID and resolves an already
committed record as a verified no-op.

Failure, partial output and uncommitted output emit no result. A no-op still
names and verifies one existing live record; the scheduler never derives that
record from the intake hash. Before acceptance, the scheduler independently
reads `record_path` from the tree named by `commit_sha` and requires its parsed
`content_hash` to match the result. The exact wire is
[ingest-result-format.md](../architecture/ingest-result-format.md).

### Reconciliation makes every changed record due

The scheduler owns housekeeping reconciliation. On scheduler startup and at
least every five minutes, it scans every live `store/*.md` record at one Git
`HEAD`, computes the complete-file hash, reads the deployed algorithm version and
ensures a deterministic, proposal-only job exists for every incomplete tuple.
A valid committed or no-op ingest result runs the same check immediately as a
latency fast path; it is not the only trigger.

That independently verified result also completes its scheduler-owned transient
intake intention: the scheduler removes the exact untracked, frontmatter-only
`queue/*.md` stub that launched the run rather than stamping or committing it.
Failed, rejected, partial or unverified work leaves that stub pending. Existing
committed legacy queue files remain untouched pending a separate migration.
Queue state is not corpus history, and cleanup does not depend on the immediate
housekeeping fast path succeeding.

The job identity is:

```
(content_hash, input_sha256, algorithm_version)
```

`content_hash` locates the stable record. `input_sha256` hashes the complete raw
bytes of the ingest Markdown file the worker examines. `algorithm_version`
identifies the complete check and guard algorithm. The canonical deployed value
comes from `housekeeping-algorithm.json` at the root of the ingests repository;
scheduler owns this formatter-canonical `anomalica/housekeeping-algorithm/1`
manifest, whose exact wire is the 77 UTF-8 bytes
`{ "algorithm_version": "1", "schema": "anomalica/housekeeping-algorithm/1" }\n`, and
scheduler and Workbench read it from the same Git ref as the record and sidecar.
The worker reports its implemented version before dispatch and the scheduler
fails closed if the manifest is missing/malformed or differs from the worker.
Any check, match, proposal-shape or apply-guard change bumps the worker version
and deployed manifest together. The worker reruns if and only if
the exact input hash or algorithm version differs from a completed sidecar.
Queue retries of the same tuple are idempotent; reviewer decisions, sidecar
bytes and timestamps do not create a new run key. Dispatch re-reads the current
ref and tuple and restages rather than running stale work.

The worker currently reads filesystem paths, so the manifest, record and
sidecar it will consume must be byte-identical to their pinned `HEAD` blobs.
Dirty, missing or colliding untracked tuple inputs hold that record; a dirty or
missing manifest fails the scan. Unrelated dirty paths do not block.

A completed pass writes `anomalica/housekeeping/2`, even when `items` is empty.
No sidecar is completion evidence for a failed or partial pass. Housekeeping
does not apply proposals and does not block pre-digest, digestion or review.

### Whole-token body corrections are narrow proposals

Version 2 retains frontmatter `set`, `clear` and `move` operations and adds one
body operation, `replace-token`. It records differing non-empty ASCII word
tokens, every case-sensitive whole-token occurrence in the body as zero-based
half-open UTF-8 byte spans into the complete raw Markdown file, and the expected
count. Here the deterministic proposal is `OSSAP` to `AAWSAP`.

Record fences may use LF or CRLF. Body start is the first byte after the actual
closing-fence line ending; complete-file hashes and byte spans preserve the
original bytes and line endings.

ASCII word bytes are `A-Z`, `a-z`, `0-9` and `_`; a whole-token match has no word
byte immediately before or after it. Occurrences are ordered, unique,
non-overlapping, body-only and exhaustive for the old token. The worker only
proposes. A human approves or rejects the item.

Apply first verifies that the current file's raw-byte SHA-256 equals the
sidecar's `input_sha256`, then revalidates the complete occurrence set, slices,
boundaries and count. It splices approved spans from last to first, decodes UTF-8
strictly, and proves that no bytes outside those spans changed. Any mismatch
refuses without changing either file, so every selected item remains
`proposed`. The record edit and sidecar decision are one Git commit; `approved`
is persisted only with a successful apply. Edge applies use one
tree/commit/ref compare-and-swap, not two independent file commits. Local
applies hold an exclusive repository writer lock from re-read through write,
shared by every local ingests writer at
`<git-common-dir>/anomalica-write.lock`, use a dedicated temporary index and
explicit record/sidecar pathspec, and
compare-and-swap the expected HEAD/ref. A conflict re-reads and revalidates; no
path from an unrelated index may enter the commit.

This operation corrects extraction or transcription. If the source itself says
`OSSAP`, the ingest preserves that wording and the reviewer rejects the
proposal; housekeeping is not a source-normalisation pass.

### Workbench warns without locking

An outstanding proposal is a `status: proposed` item in a completed v2 sidecar
whose `input_sha256` and `algorithm_version` both match the current record and
manifest. Before entering or saving ingest editing, the Workbench reads its
`anomalica/housekeeping-view/1` response, whose five `viewed_*` identities bind
the manifest, record and sidecar at one Git ref. It shows an advisory count and affected scopes with a
link to `/housekeeping?record=<64-lowercase-hex-content-hash>`, or warns that
housekeeping is due. Editing remains available. Changed bytes make prior
proposals inapplicable; the reconciliation scan discovers the new tuple without
relying on an edit event.

For a possession-gated record, the unauthorised view is a summary containing
only state, due reason, count, scopes and deep link, with `sidecar: null` and no
`viewed_*`, item, token, span, evidence or preview data. Successful possession
returns the full view and raw sidecar. Previews are a separate derived envelope
map and never mutate the committed sidecar object.

A decision request contains `schema: anomalica/housekeeping-decision/1`, only
item IDs and decisions, and the `viewed_sidecar_sha`, `viewed_ref`,
`viewed_content_hash`, `viewed_input_sha256` and `viewed_algorithm_version`
served with the viewed sidecar. The authenticated reviewer endpoint requires
every identity to remain current, reloads each operation from the committed
sidecar and rejects v1, changed, missing or already-decided items.
It never trusts operation fields from the client. A stale or concurrent request
returns conflict without changing either file or item status.

Ordinary ingest editing has the same stale-browser protection independently of
housekeeping: the edit read supplies `base_record_sha` and `base_ref`, the PUT
echoes both, and a changed blob or ref is refused before writing.

## Consequences

The scheduler uses an explicit post-commit result rather than guessing an output
path for the immediate fast path, while reconciliation also discovers in-place
re-extraction and human edits. Those changes invalidate housekeeping without
changing record identity. Algorithm changes invalidate exactly the records
checked by an older algorithm. Empty completed runs remain durable, so absence
of proposals is not confused with absence of work.

`anomalica/housekeeping/2` is a breaking interchange revision because v1
consumers skip solely by `checker_version` and cannot safely apply body-scoped
items. Version 1 sidecars are always due, cannot be decided or applied, and are
replaced by v2 after a successful pass. Decisions never carry across input or
algorithm tuple changes; each changed tuple receives fresh proposals and human
decisions.

The additional body operation increases implementation work in both Python and
the edge Workbench. The narrow byte guard, input binding and atomic commit are
the cost of preserving the stronger rule: only the exact human-approved source
correction may alter the body.

## Related

- [Housekeeping architecture](../architecture/housekeeping.md)
- [Housekeeping proposal format](../architecture/housekeeping-format.md)
- [Ingest result format](../architecture/ingest-result-format.md)
- [0040: Pipeline versioning and supersession](0040-pipeline-versioning-and-supersession.md)
