# Housekeeping

A proposal-only pass over newly ingested or changed records. It improves
frontmatter and may propose one narrowly guarded whole-token body correction;
it never applies a change itself.

Status: version 2 specified 2026-09-11 by [decision 0048](../decisions/0048-post-ingest-housekeeping-is-content-versioned.md). Partly built - see [Implementation state](#implementation-state).

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

**Fix the source first.** A corpus survey on 2026-08-19 found this is not a backlog
to clear once - it is still being created. `ingester/acquire/workspace/manifest_meta.py:38-40`
writes `out["publisher"] = channel` for every video, and
`ingester/acquire/workspace/acquire.py:315` does the same, so all 178 video records
have a YouTube channel as `publisher`. [ingest-format](ingest-format.md) line 112
states "the handler no longer writes them from channel metadata"; that change was
specified and never made. `posted_by`, `posted_date` and `container_title` appear on
0 of 288 records and in no producer code at all.

Housekeeping cleaning a corpus the ingester keeps re-dirtying is mopping with the tap
running. The handler fix comes first; housekeeping then clears what already exists.

It also aims at the real bottleneck. 214 of 288 records have never been reviewed, and
that - not throughput upstream - is why nothing reaches the site. Anything that
reduces the per-record cost of review is worth more than anything before it.

## Shape

```
ingester ──post-commit fast path──▶ scheduler ──stages housekeeping──▶ worker
                                       ▲
                                       │ startup + ≤5-minute full reconciliation
                                       │ of live ingest records
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
2. **Body edits are closed and mechanically guarded.** Version 2 permits only
   exhaustive whole-token `replace-token` proposals; arbitrary prose changes are
   unrepresentable. Enforced, not promised - see [Safety](#safety).
3. **Each proposed change is approved or rejected on its own.** A record with seven
   proposals can have three accepted. A patch is not all-or-nothing.
4. **Deterministic first; subscription only when assisted.** The post-ingest
   checks spend nothing. A research-backed check runs on Mark's Claude plan and
   must never reach the metered API or OpenRouter.

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

- **`input_sha256` + `algorithm_version`** - the record-level applicability
  marker. The first hashes the complete exact ingest Markdown bytes examined;
  the second identifies the complete check and guard algorithm. A completed
  sidecar is current only when both match. `content_hash` remains the stable
  source/selection locator and is not the input digest.
- **`housekeeping-algorithm.json`** - the scheduler-owned root manifest in the
  ingests repository (`anomalica/housekeeping-algorithm/1`) is the canonical deployed algorithm version. Scheduler and
  Workbench read it at the same Git ref as the record and sidecar; a missing,
  malformed or worker-mismatched manifest fails closed.
- **Per-item `status`** - `proposed` | `approved` | `rejected`. Set by the reviewer,
  not the worker. A rejected item stays in the current tuple's file as the record
  of that decision. It never carries into changed input or algorithm tuples.
- **Per-item `evidence`** - what justified the change. For a research-backed item this
  includes the source URL. An item with no evidence is not a proposal, it is a guess,
  and the worker must not emit one.
- **Per-item `confidence`** and the model/prompt provenance, so a reviewer can weight
  a proposal and so a bad prompt version can be found later.

## Safety

**Only approved byte scopes may change.** Every apply first verifies the whole
record against the sidecar's `input_sha256`. Frontmatter operations still require
the body to remain byte-identical. `replace-token` revalidates every recorded
whole-token byte span and then proves every byte outside those spans is
unchanged. Record and sidecar decision commit atomically. The exact guard is in
[housekeeping-format.md](housekeeping-format.md).

**Concurrency is part of the guard.** Edge applies use one tree/commit/ref CAS.
Local applies hold the repository writer lock across re-read, validation and
write, build from the expected HEAD in a dedicated temporary index, stage only
the record and sidecar pathspec, and update the ref by expected-old CAS. Neither
path may absorb the user's index or replay against a changed tip.

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
3. **Deterministic field hygiene.** Required-field presence per `source_type`, date
   precision written per the quoting rule, `creators` that parse as a list. No model.
4. **Known whole-token extraction errors.** Propose `OSSAP` to `AAWSAP` for
   every case-sensitive whole-token body occurrence. The item records exhaustive
   raw-byte spans and remains human-approved; if the source itself says `OSSAP`,
   reject it rather than normalising the source.

**Unidentified-speaker substitution is not a version 2 check.** It would change
speaker comments throughout the body and reconcile the frontmatter roster.
`replace-token` cannot represent those coupled semantics, so no worker may emit
or apply that change until a separately decided closed operation and byte guard
exist.

## Future structure repair (books)

Heading repair remains a design case, not an operation in
`anomalica/housekeeping/2`. Version 2 supports only frontmatter operations and
`replace-token`; adding heading repair requires its own closed byte-scope guard.

Mark's case, 2026-08-19: *The Fourth Mind* (Whitley Strieber) has 27 headings in its
body and every one is a flat `#` in capitals. The book's own structure is two parts
and seventeen numbered chapters:

```
in the record          the book's own contents page
# BODIES AND POWERS    I. Bodies and Powers      <- a PART
# THE SECRECY          1. The Secrecy            <- a CHAPTER, same heading level
# FAR FROM HOME        2. Far From Home
```

Three things are lost at once: the part/chapter hierarchy, the numbering, and the
case. Two headings are `# UNTITLED`.

**This belongs in housekeeping rather than the ingester**, and not only because
re-running an extraction to fix a heading is expensive. `content_hash` is the
record's identity and it is NOT the body hash - verified on this record, whose body
hashes to `334d4ffb…` while its identity is `524f46e5…`. So a body edit is safe,
whereas the practical instinct to "re-ingest it properly" produces a *new* record and
orphans the digest and every claim built on it. The reviewable-patch shape is the
safer one.

**Most of it needs no model.** The book's own contents page is in the record, at the
`# CONTENTS` heading. Matching body headings against it on a normalised key recovers
the number, the correct case and the part-versus-chapter distinction for the great
majority - a first crude pass matched 19 of 27, with the misses being the title page,
the author, CONTENTS itself, the bibliography and the two `# UNTITLED`. Only the
untitled ones need judgement.

### What this costs, stated plainly

Version 1 guarantees that body prose is untouchable. Decision
[0048](../decisions/0048-post-ingest-housekeeping-is-content-versioned.md)
widens that boundary only for exhaustive whole-token `replace-token` proposals,
not for headings. A future heading operation would need to record exact approved
byte spans and prove every other byte unchanged. Its review preview would show:

```
- # THE SECRECY
+ ## 1. The Secrecy
```

That future guard is not implied by the token operation and remains unimplemented.
The reason a reviewer can trust a housekeeping commit is that each body operation
has a closed mechanical guard, not a general permission to edit prose.

## Decisions from 2026-08-20

**The chapter check uses a model, and reads the contents page.** An earlier note here
argued most of it was deterministic. Overruled by Mark, and he is right on the
evidence: a normalised match against the contents page got 19 of 27 headings, and the
remainder - the two `# UNTITLED`, and telling a part from a chapter where the book
does not number the parts - is judgement. The model reads the contents page to work
out which chapter is which.

**Scope: our markings, not the author's words.** The heading TEXT belongs to the
book. What is broken is *our* markup around it - where a chapter begins, what level
it sits at, whether it carries its number. The check corrects the marking and takes
the title from the book's own contents page. It never rewrites a title into something
the book does not say.

**Request housekeeping from a record.** A reviewer looking at a record can ask
the scheduler to run reconciliation immediately for it rather than waiting up
to five minutes. This is not a force flag: an already current tuple does not
rerun.

**A stale proposal must not apply.** The current record's complete raw-byte hash
must equal `input_sha256`; operation-specific old values and spans must also
match. Any mismatch refuses the whole apply and makes the new input tuple due.
Do not lock reviewers out while a pass is pending - editing remains available
and deliberately invalidates the prior proposal.

**Keep the name.** Mark talked himself out of and back into "housekeeping" in one
breath. It is right: not a review, just tidying.

## Open questions

- **Whether `posted_by` / `posted_date` should join `GATED_FRONTMATTER_ALLOW`.**
  They are the direct successors of `publisher` and `date_published`, which are both
  already allowed, so a gated record can currently show the wrong field but not the
  proposal to correct it. Adding them is a *widening* of the copyright gate, which
  is Mark's call and not a side effect of building a tab. Impact today is nil: all
  19 gated records are books and papers, and the redistributor check only fires on
  YouTube channels, which are `publicly_accessible`.
- **Housekeeping's own ceiling number.** Set to session 70 / weekly 80 against the
  global 90 / 95. Chosen, not measured; a real pass should inform it.

**Resolved 2026-08-19: web research on the subscription path.** `claude -p` takes
`--tools WebSearch`, so research and a locked-down tool surface are compatible and
check 1 is buildable as specified. The catch, measured rather than assumed:
`--tools` restricts only the BUILT-IN set, so with `--tools WebSearch` alone the
model reports 46 tools - Gmail including `send_message`, Google Calendar,
Cloudflare, context7, and workspace-bus including `ask_mark`. Record bodies and web
results are both untrusted input, so that is an injection with a working mail
sender attached. `--strict-mcp-config` plus `--setting-sources ""` reduces it to
exactly one tool. All three flags are load-bearing and live in
`anomalica_common.llm.call_with_research`.

## Relationship to review

Housekeeping is not human review and does not substitute for it. A record that has
been housekept has had its metadata examined; its body has not been verified against
the source. The two states are independent and a housekeeping pass must never mark a
record as reviewed.

Reconciliation checks every live record whose exact tuple is due, regardless of
review state. The worker still changes nothing. Any proposal approved after
human sign-off is an explicit later reviewer action and a clearly separate
commit, never a silent mutation of what was approved.

## Implementation state

As of 2026-08-19 evening.

**Done.**

- **The root cause is fixed.** `ingester` commit 523d1c0: the acquirer now writes
  `posted_by` / `posted_date` and leaves `publisher` / `date_published` absent, in
  both `acquire.py` (the live path) and `manifest_meta.py`. The audio handler no
  longer fabricates a `date_published` from today, and `validator.py` requires one
  of `date_published` or `posted_date` rather than `date_published` unconditionally
  - that unconditional requirement was what forced the fabrication. 273 tests.
- **The deterministic pass.** `scheduler/backend/housekeeping.py`: sidecar read and
  write, the legacy `checker_version` re-check marker and then-built carry mechanism
  (both forbidden for version 2), the two
  model-free checks, and the guarded apply. Finds 61 proposals across 29 of 288
  records at no allowance cost. Version 2 replaces both legacy lifecycle rules;
  decisions do not carry across tuple changes.
- **The runner.** `scheduler/backend/housekeeping_cli.py`: `scan`, `propose`,
  `show`. Refuses any metered configuration outright. The ceiling (session 70 /
  weekly 80, against the global 90 / 95) gates `--research` only - the model-free
  checks spend nothing, so holding them because the plan is busy would stop free
  work for a reason that does not apply to it.
- **Shared, not duplicated.** The model, the sidecar and `apply_items` live in
  `anomalica_common.housekeeping`, because the scheduler proposes and the workbench
  applies and both must agree on what applying means. Duplicating the one function
  that enforces permitted byte scopes would let it drift.
- **The legacy read + decide routes** in `workbench/backend/server.py`, and the
  **Housekeeping tab**. Version 1 sent `{item_id, status}` pairs only. Version 2
  additionally requires the five `viewed_*` identities defined above; the
  server, which can read the record, performs the guarded splice -
  `PUT /api/ingests/{hash}` cannot be reused because it needs the whole record from
  a client that does not have a gated body. Record and sidecar commit together.
- **A first pass over the corpus**, committed to `ingests`: 61 proposals across 29
  records, 259 empty sidecars marking records as examined. No allowance spent.
- **The production decide route** in `workbench/edge/main.ts`, DEPLOYED to Bunny
  edge script 79602 on 2026-08-19 (the previous release was 2026-07-23, so the route
  was committed but not live until then - committing edge code does not ship it).
  Verified after: the decide route answers 401 rather than 404, the existing
  endpoints still answer 200, and a sweep of all 19 gated records shows 0 leaking. `edge/lib/housekeeping.ts`
  is a hand port of `apply_items`, which is a standing liability - it duplicates the
  function enforcing the permitted byte scopes, and exists only because
  production runs no Python. Two things hold it: the Python cases are ported
  alongside it, and `backend/test_housekeeping_parity.py` runs BOTH over the same 35
  inputs (the 29 real sidecars plus 6 synthetic shapes) and compares output text
  exactly. Verified that the parity test bites by sabotaging the TypeScript side.

**Not done.**

- **The model-backed checks themselves.** Their transport now exists
  (`anomalica_common.llm.call_with_research`); no check uses it yet.
- **The scheduler job type.** The CLI runs; it is not yet a lane the scheduler
  stages and dispatches.
- **The version 2 interchange, reconciliation and post-commit fast path.** This
  implementation snapshot predates them. Version 1 sidecars use
  `checker_version` only. Decision 0048 supersedes that skip rule with exact
  ingest bytes plus algorithm version and adds the guarded `replace-token`
  operation.
- **`container_title`.** Speaker naming is excluded from version 2 until it has a
  separately decided closed body operation.

**Known, deliberately not done.**

`manifest_meta.py` advertises itself as the single source of truth for the acquirer's
provenance mapping and has no production caller - `acquire.py` duplicates the mapping
inline. Both were corrected together in 523d1c0. Wiring one to the other is a tidy-up
that was kept out of a correctness fix.
