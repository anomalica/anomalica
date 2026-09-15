# Curation ledger format

The curation ledger is the durable, replayable record of human graph-curation decisions - initially node merges. Its producer is the workbench's merge tool; its consumer is the assimilator, which replays it on every graph rebuild, after import. See [decision 0038](../decisions/0038-graph-curation-replayable-ledger.md) for the why.

It is git-tracked human-readable YAML in the `curation` repo (a dedicated data repo, sibling to `ingests`/`digests`/`content`) - NOT SQLite. The decisions must be diffable and reviewable; reversibility, versioning, and the who/when audit come from git commits plus the in-band `actor`/`timestamp` fields. (Contrast the operational AI-ledger in [0037](../decisions/0037-ai-operation-ledger.md), which is local SQLite telemetry.)

## Shape

An append-only sequence, one entry per curation operation. Entries are NEVER edited in place: an operation is undone by appending a compensating reversal entry, not by deleting the original. The assimilator replays entries in deterministic order - `timestamp`, tie-broken by `id` - after importing all digests.

## Merge entry

| Field | Description |
|-------|-------------|
| `op` | `merge`. |
| `id` | Stable entry identifier (content hash or sortable id). Referenced by a later reversal. |
| `survivor` | The node kept: `{ id, name, node_type }` - a snapshot at merge time. |
| `victims` | The nodes collapsed into the survivor: a list of `{ id, name, node_type }` snapshots. |
| `canonical_name` | The survivor's canonical name after the merge. |
| `prior_names` | Every name the merged entities were known by. The rebuild-stable natural key (see Identity keying), and the set recorded as aliases on the survivor at replay. |
| `node_type` | The shared type of the merged entities. |
| `proposal_ids` | Optional unique sorted `rename-proposal:<id>` values whose name clash this merge resolves. A new merge created from one or more rename proposals must include them. |
| `actor` | Who made the decision. |
| `timestamp` | ISO 8601. |
| `note` | Optional free-text justification. |

## Reversal entry

| Field | Description |
|-------|-------------|
| `op` | `unmerge`. |
| `id` | This entry's identifier. |
| `reverses` | The `id` of the merge entry being undone. |
| `actor` | Who reversed it. |
| `timestamp` | ISO 8601. |

## Replay semantics

After import, for each live (not later reversed) merge entry, in order:

1. Resolve the survivor and victim nodes by natural identity (`name` + `node_type`, against the recorded `prior_names`) - the authoritative replay key (see Identity keying).
2. Reattach the victims' `claim_node_refs` and `aliases` to the survivor.
3. Add the victims' names and the entry's `prior_names` as aliases on the survivor.
4. Set the victims' `retired_at` (this is the writer for that field, which is read everywhere but written nowhere today).

Same digests + same ledger => identical graph. Chained merges (a victim of one entry named in a later entry) resolve correctly because replay is ordered.

## Identity keying

Per [0038](../decisions/0038-graph-curation-replayable-ledger.md), the authoritative replay key is the natural identity - `canonical_name` + `node_type` + `prior_names` - because synthetic node ids are not rebuild-stable (a per-extraction `uuid4`, first-importer-wins) and the importer already resolves entities by name. The synthetic ids in `survivor`/`victims` are an at-merge-time audit snapshot, not the replay key. (Content-deterministic ids were considered and parked - see 0038.)

## Rename ledger version 2

`renames.yaml` is an append-only YAML stream with logical schema
`anomalica/rename-ledger/2`. Version 2 keeps every existing document unchanged,
derives an authoritative identity for each legacy rename from its immutable
content, and requires explicit identities and references on new events. A raw
legacy `rename_id` remains audit data; it is not an authoritative replay or
disposition key. Exceptional outcomes use the separate
[curation replay disposition contract](curation-replay-dispositions.md).

### Operation identity

For a legacy `op: rename`, serialise this exact object as UTF-8 compact JSON,
with keys in the shown order, non-ASCII unescaped and no trailing newline:

```json
{"schema":"anomalica/legacy-rename-operation-id/1","op":"rename","rename_id":"legacy-id","at":"2000-01-01T00:00:00Z","by":"actor-or-null","new_name":"New name","node":{"name":"Old name","node_type":"type","prior_names":[]}}
```

`at` is normalised to UTC `Z`; `by` is a string or JSON null; and
`node.prior_names` is deduplicated and sorted lexicographically. The canonical
operation id is `rename-ledger:sha256:<64 lowercase hex>`, where the digest is
SHA-256 of those exact bytes. File position, document ordinal, Git history and
consumer state never participate.

A new base event has schema `anomalica/rename-ledger-event/2`, `op: rename`,
`operation_id`, `at`, `by`, `new_name`, `node`, and `proposal_id`.
`operation_id` uses the same prefix and is verified as SHA-256 of compact
canonical JSON over `{schema, op, at, by, new_name, node, proposal_id}` in that
key order, excluding `operation_id`. `proposal_id` is either null for a direct
rename or the exact `rename-proposal:<id>` operation id of the proposal it
fulfils. A rename created from a proposal must carry the latter; matching old
and new names is not an authoritative proposal link.

An operator may reject a proposal without renaming or merging by appending a
version 2 event with `op: reject_proposal`, `operation_id`, `proposal_id`, `at`,
`by` and non-empty `reason`. Its operation id is verified as SHA-256 of compact
canonical JSON over `{schema, op, proposal_id, at, by, reason}` in that key
order, excluding `operation_id`. A name clash alone does not create this event
or authorise rejection.

Every `operation_id` must be unique. Different payloads producing the same id,
or an explicit id reused with different content, are fatal collisions. Repeated
identical payloads are reported as `duplicate_encoding` and block replay until
an operator resolves the source defect; a consumer must not collapse them by
dictionary overwrite or invent occurrence ids.

### Compensation

A new reversal is a version 2 compensation event:

```yaml
schema: anomalica/rename-ledger-event/2
op: compensate
id: rename-compensation:sha256:<64 lowercase hex>
at: 2000-01-01T00:00:00Z
by: operator
reason: Why the operations no longer apply
reverses:
  - rename-ledger:sha256:<64 lowercase hex>
```

`reverses` is a non-empty, unique, lexicographically sorted list of prior active
operation ids. The compensation id is SHA-256 of UTF-8 compact canonical JSON
over `{schema, op, at, by, reason, reverses}` in that key order, with the same
string prefix shown above. Unknown, duplicate, already-compensated or later
references fail closed. One compensation may withdraw several operations
atomically. Restoring one requires a new operator-reviewed rename; version 2
does not reverse a compensation.

A legacy `op: unrename` that names only a raw `rename_id` resolves only when
that value selects exactly one legacy base operation. Zero or multiple matches
are invalid and block replay; it never means every entry that reused the string.

### Legacy collision migration

The historical stream contains 133 distinct `op: rename` entries carrying raw
`rename_id: rn-1`. Their complete canonical payloads and timestamps differ, so
the identity rule above mechanically produces 133 distinct operation ids. The
old documents remain unchanged. Repository history confirms that all 133 came
from `test_embedding_invariant.py` leaking production `rename_node` writes across
curation commits `46debf9` and `99f2dee`; none is authoritative curation. An
operator-reviewed migration appends one version 2 compensation listing all 133
derived ids and cites that provenance. The consumer must not infer the decision
merely from their shared id, repeated old/new names, or `by: test`. Replacement
remains blocked until the reviewed compensation exists and validates.

### Proposal inventory and ordering

Every well-formed `rename-proposals/*.json` file is a distinct durable base
request with operation id `rename-proposal:<id>` and timestamp `proposed_at`.
The filename timestamp, `node_id`, and SQLite proposal status are audit or
derived data, never replay identity. A proposal file is not a reversal merely
because its requested name undoes an earlier request. A future applied rename
links it through the version 2 `proposal_id` field above; historical outcomes
without that link require separately validated replay-disposition evidence.
A confirmed merge may instead resolve one or more proposals through its
`proposal_ids`. Adding a proposal id to a merge request never confirms the
merge: the normal explicit merge-confirmation block remains mandatory before
the entry is durable or affects proposal status.

Rename events replay by `(at, operation_id)` after merges and rejection
materialisation. Proposal requests are evaluated by `(proposed_at,
rename-proposal:<id>)`. These orders operate inside the fixed curation phases;
timestamps do not interleave dependent phases.

## Tag entry (2026-09-03)

`op: tag` - a record is about a node, asserted by a person. Fields: `tag_id`,
`at`, `by`, `node: {name, node_type, prior_names}` (natural key; `node_type`
required), `record: {content_hash, title}` (the hash is the key), `note`.
Compensating `op: untag` names the `tag_id`. Replay resolves the node by name
then aliases within type on the deterministic tiers, creates a **topic** that
has no node (never any other type), resolves the record by hash, and writes one
`record_nodes` row plus a `record_tags` row carrying the outcome (`pending`,
`applied`, `lost`) readable by `tag_id`. Runs after renames. Record-level only:
no `claim_node_refs`, so a tag does not count toward the page gate, scoring or
corroboration. Span tags (a selection resolving to overlapping claims) are a
later op on the same machinery. Lives in `tags.yaml` beside the other ledgers.

## Claim-reference status entries

`claim-ref-status.yaml` has schema `anomalica/claim-ref-status-ledger/1` and an
`entries` sequence. It is the durable source for a person's decision that one
claim does or does not belong on one node; the SQLite `claim_ref_status` table is
only its replayed materialisation. Entries are append-only and replay in
`(set_at, id)` order.

A set entry has `op: set`, a deterministic `id`, `record_content_hash`,
`claim_fingerprint`, `node: {name, node_type, prior_names}`, `status`
(`verified` or `suspect`), `reason`, `set_at`, `set_by`, `salience`, and
`source: {claim_id, node_id}`. The record hash scopes
`anomalica_common.digest.fingerprint_of_claim`, which is computed from the
digest-local claim text, type, quote and location. The source identifiers are an
at-decision audit snapshot, never replay keys. A compensating `op: unset` entry
has its own deterministic `id`, names the set entry in `reverses`, and records
`set_at`, `set_by` and an optional `reason`; an old entry is never edited or
deleted. If more than one active set entry addresses the same record, claim and
node identity, the latest replay-order entry wins. A contradictory tie fails
closed.

Replay runs after merges and renames. It resolves the record by content hash,
requires exactly one claim with the scoped fingerprint, and resolves the node by
its natural identity. A missing record after an intentional canonical-input
contraction is an explicit reported drop. A missing or ambiguous claim or node
for a retained record fails closed. Replay normally requires the imported
`claim_node_refs` edge to exist. A `verified` decision may restore that edge with
the recorded salience because the decision itself asserts that the exact claim
belongs on the exact node; a `suspect` decision never creates an edge.

## Extensibility

The first operation is `merge`. The same append-only-plus-replay machinery admits further graph-level curation ops (for example `split`, `rename`, `retype`) as new `op` values, each with its own replay rule, run in the same after-import replay pass.
