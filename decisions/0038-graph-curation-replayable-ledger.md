# 0038. Human graph-curation as a replayable ledger

Date: 2026-06-21
Status: accepted

## Context

The knowledge graph is DERIVED: the assimilator builds it by importing digests, and it can be dropped and rebuilt from those digests at any time. Entity resolution is currently weak - the graph has never merged two nodes, because the merge operation was never built (`retired_at` is read everywhere but written nowhere; "merge" today means only an import-time alias attach). As a result single real-world entities are split across many nodes - the 2004 USS Nimitz encounter is spread over seven-plus nodes. Fixing this needs a real node-merge operation and a human merge tool in the workbench.

But a merge applied only to the live database is LOST on the next rebuild: both nodes are recreated from their digests and the merge is gone. Human curation cannot live only in the derived store.

## Decision

Human graph-curation persists as a **replayable curation ledger**: a durable, versioned, reversible, git-tracked record of curation decisions (initially node merges) that the assimilator re-applies deterministically on every graph rebuild, after import. The live graph stays fully rebuildable; the ledger is the durable source that makes human decisions survive the rebuild. The entry schema is in [architecture/curation-ledger-format.md](../architecture/curation-ledger-format.md).

### Replay-on-rebuild

A rebuild is: drop the graph, import all digests (nodes recreated from digests, claims attached), THEN replay the curation ledger in deterministic order. A merge replay resolves its survivor and victims, reattaches the victims' claim references and aliases to the survivor, records the victims' names as aliases on the survivor, and retires the victims (this is what finally writes `retired_at`). Same digests + same ledger => identical graph, every time.

### Reversible, append-only

The ledger is append-only. A merge is undone not by deleting its entry but by appending a compensating reversal entry that references it; replay applies entries in order and honours reversals. Nothing is edited in place, so the full decision history survives - git commits carry the meta-audit (who, when), the entry fields carry the in-band audit (actor, timestamp).

### This extends the one-directional data-flow principle

The project already persists downstream human edits as durable artefacts at the consuming stage's input boundary, replayed forward, never written back into an earlier stage's derived output: workbench record-edits -> commits in `ingests` (replayed by the digester); site edits -> directives in `content` (replayed by assembly). That principle currently lives only in `architecture/overview.md` and the repository guide, in no record. Graph-curation is its third instance and the first to be pinned: workbench graph-curation -> the curation ledger (replayed by the assimilator).

### Physical home: a dedicated curation store, NOT the digests

The ledger is a dedicated, git-versioned store - its own data repo (`curation`), a sibling of `ingests`/`digests`/`content` - written by the workbench's merge tool and read+replayed by the assimilator. It does NOT go inside per-record digests, for three reasons:

- A merge is a CROSS-record, graph-level decision; it has no natural per-record digest home.
- It is a distinct data lifecycle - human-authored graph curation, applied at the graph-build boundary - so it follows the established pattern of its own data-artefact repo.
- Keeping it out of `digests` keeps that repo's contract clean (a digest is per-record extraction) and removes any chance of a digest regeneration touching irreplaceable human curation.

(The lighter alternative - a top-level curation directory inside the digests repo, since the assimilator already reads that repo - is workable but mixes per-record extraction with cross-record curation, and was rejected in favour of the dedicated `curation` repo.)

It is git-tracked human-readable text (YAML), NOT SQLite: the decisions must be diffable and reviewable, and reversibility, versioning, and actor/timestamp come from git plus in-band fields. (Contrast the AI-operation ledger, [0037](0037-ai-operation-ledger.md), which is local operational telemetry in SQLite; this is durable human source.)

## Node identity: the replay key

Replay references the entities a merge acted on, so those entities must be re-identifiable after a fresh import. Synthetic node ids are NOT rebuild-stable: a node's id is a per-extraction `uuid4` (minted fresh each time the digester runs), and the importer keeps whichever id the FIRST digest to introduce the entity carried, with later mentions matching by name/fuzzy/acronym and inheriting it (the variant name becomes an alias). Identity has therefore always been carried by NAME, not id - and import order is order-sensitive on top (at least one import loop iterates an unsorted `glob`). A merge keyed purely on synthetic ids could reference different entities after a rebuild.

Resolved (the assimilator's call): the authoritative replay key is the **natural identity** - `canonical_name` + `node_type` + the recorded `prior_names`. This is what the importer already resolves on, so it adds no new scheme. The synthetic ids are recorded too, but as an at-merge-time AUDIT snapshot only, not the replay key. Content-deterministic ids (deriving the id from name + type) were considered and parked: they would be a new parallel identity scheme with its own collision handling and a schema-wide id ripple, for no benefit - fragmentation is name-based and names already carry identity. They remain a possible later improvement only if ever needed.

Independently of the keying choice, the import `glob` should be sorted so import order is deterministic.

## Why

- **Curation must outlive the derived store.** The graph is rebuildable; a decision held only in it is not durable. A replayed ledger is.
- **Deterministic and reversible by construction.** Append-only plus ordered replay gives a reproducible graph and a complete, revertible decision history.
- **One pattern for human edits.** It reuses the established persist-as-artefact-and-replay flow, not a new mechanism.
- **Closes the `retired_at` gap.** Merge replay is the writer the read-only `retired_at` field has been waiting for.

## Consequences

- Unblocks the assimilator's merge-backend build: it proceeds on the principle (durable, reversible, replayed-after-import) while this pins the contract.
- The workbench gains a human merge tool that writes the ledger - a new commit target alongside its ingests/digests corrections.
- Node identity must be made rebuild-stable first (the prerequisite above) - the load-bearing dependency.
- A new data-artefact store joins `ingests`/`digests`/`content`.
- `retired_at` gains its writer.

## Scope

A new durable curation layer, a replay step, and the workbench merge tool. It pins the curation instance of the one-directional data-flow principle (previously only in overview.md), follows the data-artefact-repo pattern, and names rebuild-stable node identity as its prerequisite. Schema in [architecture/curation-ledger-format.md](../architecture/curation-ledger-format.md). The first curation op is node merge; the ledger is designed to admit further graph-level curation ops (split, rename, type-correction) on the same replay machinery. The machinery also extends from NODES to CLAIMS: claim dedup / supersede / corroboration-linking (driven by provenance-overlap, see [decision 0039](0039-multi-model-digestion-canonical-reconciliation.md)) are curation ops in the same ledger - the assimilator maintains the graph, it does not merely import it.
