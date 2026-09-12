# Housekeeping proposal format

The interchange contract between the housekeeping worker (which proposes) and the
workbench (which lets a human decide). One file per record:

```
ingests/store/{bare-content-hash}.housekeeping.json
```

The filename key is the 64 lowercase hexadecimal characters without the
`sha256:` prefix; the `content_hash` field inside the sidecar retains the prefix.

The deployed algorithm version has one cross-component source:

```
ingests/housekeeping-algorithm.json
```

```json
{ "algorithm_version": "1", "schema": "anomalica/housekeeping-algorithm/1" }
```

The scheduler owns this manifest as part of deploying its worker. Its canonical
wire is the 77 UTF-8 bytes shown above: one-line formatter output with one space
after `{`, around each `:`, after `,` and before `}`, keys sorted lexically, and
one trailing LF. No additional fields or other whitespace are permitted.
Scheduler and Workbench read it at the same Git ref as the record and sidecar.
Before dispatch, the worker reports
`anomalica_common.housekeeping.ALGORITHM_VERSION`; a missing or malformed
or non-canonical manifest, unknown field, or a value that differs from the
worker fails closed and writes no sidecar. The worker owner must bump
`ALGORITHM_VERSION` whenever any check,
matching rule, proposal shape or apply guard changes; deployment updates the
manifest to that exact value in the same release.

Beside `{content_hash}.md` and `{content_hash}.verification.json`, following the
sidecar precedent already in the store. Committed to `ingests`, which is how a
proposal written on Mark's machine reaches the deployed workbench.

See [housekeeping.md](housekeeping.md) for what the pass is and why. This document
is the file shape.

## Worked example

The real record `1d24cbe9…` is the case the whole component exists for. Its
frontmatter today:

```yaml
title: 'UFOs in Australia – Eyewitnesses Talk to Dr. James E. McDonald During His Investigative Tour (1967)'
publisher: 'Eyes On Cinema'
source_url: 'https://www.youtube.com/watch?v=8NIy61DkTWw'
date_published: '2026-08-11'
source_type: 'video'
```

Three things are wrong, and they are wrong in a way no rule can fix. `Eyes On Cinema`
is a channel that reposts archival footage, so it is the **copy**, not the publisher.
`2026-08-11` is when that channel uploaded it, not when the work was published - the
title says 1967. And the actual publisher is unknown until someone looks.

The sidecar that proposes the correction:

```json
{
  "schema": "anomalica/housekeeping/2",
  "content_hash": "sha256:1d24cbe9e49ad5279cd4975a2b37b3b3ab60a260be30a9264e34ef168d7f9e0e",
  "input_sha256": "sha256:7a9486d9d7e8ac90dbb185b86d24d60920c8cb3c97dba6a68a9f116fdd9e5812",
  "checked_at": "2026-08-19T19:40:11Z",
  "algorithm_version": "1",
  "outcome": "completed",
  "usage": {
    "transport": "subscription",
    "model": "claude-sonnet-5",
    "input_tokens": 4180,
    "output_tokens": 610
  },
  "items": [
    {
      "id": "1d24cbe9-posted-by",
      "check": "redistributor-filed-as-publisher",
      "field": "publisher",
      "operation": "move",
      "to_field": "posted_by",
      "current": "Eyes On Cinema",
      "proposed": "Eyes On Cinema",
      "confidence": "high",
      "evidence": {
        "reasoning": "The channel republishes archival broadcast footage it did not produce. The title dates the work to 1967, decades before the channel existed.",
        "sources": ["https://www.youtube.com/@EyesOnCinema/about"],
        "record_spans": ["title"]
      },
      "status": "proposed"
    },
    {
      "id": "1d24cbe9-posted-date",
      "check": "redistributor-filed-as-publisher",
      "field": "date_published",
      "operation": "move",
      "to_field": "posted_date",
      "current": "2026-08-11",
      "proposed": "2026-08-11",
      "confidence": "high",
      "evidence": {
        "reasoning": "This is the upload date of the copy, not the publication date of the 1967 work.",
        "sources": ["https://www.youtube.com/watch?v=8NIy61DkTWw"],
        "record_spans": ["date_published"]
      },
      "status": "proposed"
    },
    {
      "id": "1d24cbe9-date-published",
      "check": "work-date-from-title",
      "field": "date_published",
      "operation": "set",
      "current": null,
      "proposed": "1967",
      "confidence": "medium",
      "evidence": {
        "reasoning": "The title states the investigative tour took place in 1967. Year precision only; no month or day is evidenced.",
        "sources": [],
        "record_spans": ["title"]
      },
      "status": "proposed"
    }
  ]
}
```

Note the third item is `medium` and the first two are `high`. Moving a known
redistributor out of `publisher` is safe; asserting the work's date from a title is a
reading. A reviewer can take the first two and leave the third.

Note also there is no proposal to fill `publisher`. Nothing evidenced it, so nothing
is proposed - the same not-evidenced convention [ingest-format](ingest-format.md)
uses for date precision. An unproposed field is a better outcome than a guessed one.

## Fields

### Record level

| Field | Meaning |
|---|---|
| `schema` | `anomalica/housekeeping/2`. Version 1 is always due and cannot be decided or applied. |
| `content_hash` | The record this describes, in full `sha256:` form. |
| `input_sha256` | SHA-256, in full `sha256:` form, of the complete exact raw bytes of the ingest Markdown file examined. It is not `content_hash`. |
| `checked_at` | When the pass ran. |
| `algorithm_version` | Non-empty ASCII token matching `[A-Za-z0-9._-]+` and identifying the complete check suite, including matching and apply-guard semantics. It must equal the root manifest. |
| `outcome` | `completed`. A failed or partial pass writes no sidecar. |
| `usage` | Optional. Transport, model and token counts for model calls that contributed proposals. `transport` must be `subscription`; deterministic-only passes omit it. |
| `items` | The independently-decidable proposals. May be empty - an empty current completed sidecar means "checked, nothing to propose", which is a result, not a failure. |

### Item level

| Field | Meaning |
|---|---|
| `id` | Stable within the file. The workbench addresses an approval by this. |
| `check` | Which check produced it. Lets a whole class be re-run or discounted. |
| `operation` | Tagged union: frontmatter `set`, `clear` or `move`; body-scoped `replace-token`. Fields from another variant are forbidden. |
| `confidence` | `high`, `medium`, `low`. Advisory to the reviewer; it does not gate anything. |
| `evidence` | Why. `reasoning` in a sentence, `sources` as URLs where research was involved, `record_spans` naming what in the record supports it. **An item with no evidence must not be emitted.** |
| `status` | `proposed` (worker) → `approved` or `rejected` (reviewer). |
| `depends_on` | Optional list of non-empty item IDs from the same sidecar. Approving this item requires every listed prerequisite also to be approved in the same atomic decision request. Unknown IDs, self-dependencies and cycles therefore fail closed because their prerequisite set cannot be satisfied. Omitted means no prerequisite. It is immutable proposal data and participates in same-tuple decision carry identity. |

Frontmatter `set`, `clear` and `move` items retain the v1 fields: `field`,
`current`, `proposed`, and `to_field` for `move`.

A `replace-token` item has exactly these operation-specific fields:

| Field | Meaning |
|---|---|
| `scope` | Required literal `body`. Every occurrence must lie after the record's frontmatter. |
| `old_token`, `new_token` | Required differing non-empty ASCII tokens matching `[A-Za-z0-9_]+`. |
| `case_sensitive` | Required literal `true`. |
| `token_boundary` | Required literal `ascii-word`. A match has no `[A-Za-z0-9_]` byte immediately before or after it. |
| `occurrences` | Required ordered list of `{start_byte, end_byte}`. Offsets are zero-based half-open positions in the complete raw ingest Markdown UTF-8 bytes. They are unique, non-overlapping, body-only, and enumerate every matching occurrence of `old_token`. |
| `expected_count` | Required positive integer equal to `len(occurrences)`. |

The opening and closing frontmatter fence lines accept either LF or CRLF. The
body starts at the first byte after the actual line ending that terminates the
record's first closing `---` frontmatter fence. Every occurrence satisfies
`start_byte >= body_start`; exhaustive matching searches only `[body_start,
len(raw_bytes))`. The source file must decode as strict UTF-8 before proposal
generation. Boundary tests still inspect the immediately adjacent raw byte when
one exists; start and end of file count as boundaries. Hashes and spans use the
original bytes without line-ending normalisation.

The first deterministic body proposal replaces whole-token `OSSAP` with
`AAWSAP`. It is an extraction/transcription correction proposal, not automatic
normalisation: if the source itself says `OSSAP`, the reviewer rejects it.

## Due and complete

A record is complete only when its sidecar has schema
`anomalica/housekeeping/2`, `outcome: completed`, an `input_sha256` matching the
complete current record bytes, and an `algorithm_version` matching the manifest
at the same Git ref. Anything else is due. Version 1 cannot be decided or
applied because it has no exact input-byte binding.

The job applicability identity is `(content_hash, input_sha256,
algorithm_version)`. `content_hash` locates the stable record; it does not hash
the Markdown. A record reruns if and only if its exact bytes or algorithm version
changes. Sidecar status changes, review decisions and timestamps do not create a
new run key. Version 1 sidecars are always due. Decisions are not carried across
a changed `input_sha256` or `algorithm_version`; the new tuple receives fresh
proposals and decisions.

Every entry point applies this currentness rule. In particular, a single-record
`housekeeping propose <content-hash>` invocation is a no-op when the sidecar is
current: it must not rewrite `checked_at`, proposals, research-only items or
decisions. There is no force mode that bypasses currentness.

The scheduler reconciles on startup and at least once every 300 seconds. One
scan pins the ingests repository's `HEAD`, validates the manifest there,
enumerates all live `store/*.md` blobs from that tree and stages each due tuple idempotently. A valid post-commit
ingest result runs the same due check immediately but does not replace the scan.
Immediately before dispatch, the scheduler re-resolves the ref, manifest and
record bytes; changed work is discarded and the new tuple is staged instead.
Because the worker reads filesystem paths, its manifest, record and sidecar
paths must be byte-identical to their pinned `HEAD` blobs. A dirty, missing or
untracked collision holds that record without writing; a dirty or missing
manifest fails the whole housekeeping scan. Unrelated dirty paths do not block.

**Rejected items are kept, not deleted.** A rejection is the durable record that a
human considered this exact proposal for this exact tuple and declined it. It
prevents repeat decisions while that sidecar remains current. It does not carry
into a changed input or algorithm tuple.

## Applying an approved item

Every decision request is bound to the committed state the reviewer saw. It
carries `schema: anomalica/housekeeping-decision/1`, `viewed_sidecar_sha`,
`viewed_ref`, `viewed_content_hash`, `viewed_input_sha256`,
`viewed_algorithm_version` and a non-empty list of `{item_id, status}` where
status is `approved` or `rejected`. `viewed_sidecar_sha` is the Git blob id of
the committed sidecar backing the raw or access-gated view; `viewed_ref` is the
commit whose one tree supplied manifest, record and sidecar. The two viewed hashes retain their full
`sha256:` prefixes. These are the only client-supplied decision fields;
operation data is forbidden. The endpoint requires an authenticated reviewer.
The server requires the current ref and every reloaded identity to match,
reloads named proposed items from that sidecar, and verifies the tuple again.
Unknown, duplicate, missing, v1, already-decided or mismatched input is a
conflict or validation failure, never a partial decision.

Every apply then hashes the complete current raw record and requires it to equal
the sidecar's `input_sha256` and request `viewed_input_sha256`. A mismatch is stale: apply nothing and
make the new input tuple due. Every selected item remains `proposed` on any
stale, guard, validation or ref failure.

For a frontmatter item, splice only the source/destination field byte ranges
named by that operation (or its single insertion point), preserve the original
line endings and require every other frontmatter byte plus all body bytes to be
identical. For `replace-token`, validate that the occurrence spans
are the complete whole-token match set, that each slice equals `old_token`, and
that all spans remain ordered, unique, non-overlapping and body-only. Splice from
last to first, decode UTF-8 strictly, and prove that no bytes outside the approved
spans changed. Any hash, slice, boundary, count, overlap, decode or postcondition
mismatch aborts without changing the record or sidecar.

The changed record and sidecar decision are committed atomically in one Git
commit, separately from the ingest commit. `approved` is persisted only when the
guarded record apply succeeds in that same commit; `rejected` changes only the
sidecar. Edge code uses one Git tree, commit and expected-ref compare-and-swap;
two independent Contents API commits are not atomic. Local code holds an
exclusive repository writer lock from the initial ref/byte re-read through the
write. Every Anomalica process that mutates the local ingests repository uses
the same lock at `<git-common-dir>/anomalica-write.lock`. Apply uses a dedicated
temporary index based on the expected HEAD and stages
only the explicit record and sidecar pathspec, then compare-and-swaps the branch
ref against that HEAD. It constructs the blobs, tree and commit in that
temporary index before CAS and does not replace either working-tree file first.
After successful CAS it materialises only those committed paths while retaining
the lock. It never uses or absorbs the user's index. A ref conflict therefore
leaves both working-tree files unchanged and requires re-reading and
revalidating the new tip, never replaying the old tree against it. A detached or
unborn HEAD is refused.

## What it must never do

- Make a general body edit. `replace-token` is the only body operation. Speaker
  renaming, heading repair, partial occurrence replacement and arbitrary text
  replacement remain unsupported until they receive equally narrow guards.
- Apply worker output through a generic record-write route or accept an
  unauthenticated or client-supplied operation. Only the bound reviewer decision
  endpoint may cause a proposal to change either file.
- Set a field it has no evidence for. Absent beats guessed.
- **Invent a plausible real name for someone it cannot identify.** Where a proposal
  names a person - a speaker, a creator - and the evidence does not identify them,
  it must propose a bracketed description (`[interviewer 2]`) or propose nothing.
  Never a guess that looks like a name. This is the one failure of this component
  that nothing downstream can catch: a fabricated name is structurally identical to
  a correct one, passes every check, and once approved becomes the record's own
  account of who was speaking. The test for whether a value names anybody, and the
  notation for when it does not, are in
  [ingest-format.md](ingest-format.md#square-brackets-mean-this-is-a-description-not-a-name).
- Mark a record as human-reviewed. Housekeeping examines metadata; review verifies the
  body against the source. Independent states.
- Run on the metered API or OpenRouter. Subscription only, pinned at dispatch.
