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

## Extensibility

The first operation is `merge`. The same append-only-plus-replay machinery admits further graph-level curation ops (for example `split`, `rename`, `retype`) as new `op` values, each with its own replay rule, run in the same after-import replay pass.
