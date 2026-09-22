# Architecture Overview

How the pipeline fits together, end to end. A living document.

**The architecture diagram is not drawn here.** Its single source lives in this meta-repo - `reference/pipeline.mmd` (the topology) and `reference/architecture.yaml` (per-node detail), which the site mounts and renders as the interactive `/architecture/` page. Earlier versions of this document kept an ASCII copy of that diagram; it only drifted, so it is gone. Change the pipeline shape in those two files, not here.

**The repository map and the per-component documentation index live in the [README](../README.md)**, not here. Per-component detail is in the docs the README links (ingester, digester, assimilator, assembler, data model, node types).

What remains below is the one thing neither the diagram nor the per-component docs carry: the connected story of how data moves between the stages.

**Every step in order, with what makes it due and what it costs, is in [pipeline-stages.md](pipeline-stages.md)** - the answer to "when does the quote check happen" or "what runs after an import".

**Freshness from record through deployment is defined in
[freshness.md](freshness.md).** It keeps each stage's native drift measure and
inherited upstream reasons rather than inventing one end-to-end percentage. The
assimilator emits the canonical reason groups in a queue-bound
`anomalica-freshness/v1` manifest; the deployment contract requires that input to
be guarded by its exact expected SHA-256, although the Site consumer is not yet
shipped. Deterministic import and synthesis must converge around blocked model
work, while every remote-model dispatch, including first generation, remains
separately approval-bound.

## knowledge.db is three files (WAL, since 2026-08-25)

The assimilator's graph at `~/.local/share/assimilator/knowledge.db` runs in SQLite
**WAL mode**. That means it is not one file:

    knowledge.db
    knowledge.db-wal     recent committed transactions live here, not in the main file
    knowledge.db-shm     shared-memory index for the above

**Anything that copies, backs up or ships the graph must take all three**, or run
`PRAGMA wal_checkpoint(TRUNCATE)` first, or copy with `sqlite3 source ".backup dest"`.
A copy of `knowledge.db` alone is a torn snapshot missing whatever is still in the
`-wal`.

The failure mode is the dangerous kind: when the database is idle the last writer
checkpoints and **both sidecars disappear**, so a copy taken at a quiet moment is
complete and a copy taken under load is silently short. It passes testing and fails
in production.

**A commit no longer changes the file's mtime or size.** The write goes to the
`-wal`; the main file is untouched until a checkpoint. Measured 2026-08-25:

    before write            db.mtime_ns …168287   wal absent
    after committed write   db.mtime_ns …168287   wal 4152 bytes   <- main file unchanged
    after checkpoint        db.mtime_ns …075750   wal 0

So **anything that caches or polls on `knowledge.db`'s mtime is broken**: it serves
stale data for as long as the graph is busy, and starts working the moment the graph
goes idle and checkpoints. Right under test, wrong under load - the same shape as the
copy problem. An mtime check is the obvious way to ask "has the graph changed since I
last looked", so this population is larger than the set of things that copy the file.

Fingerprint the `-wal` as well as the main file. Not the `-shm`: readers touch that,
so including it rebuilds the cache on every read rather than every write.

**Why it was changed.** The previous `journal_mode=delete` means a reader holds a
shared lock that blocks every writer. Three processes write to this graph - the
hourly assimilate timer, the scheduler's dispatch runner, and manual commands - and
a long analytical read made it unwritable for the read's whole duration. Measured
2026-08-25: a 30,020-query nearest-neighbour scan caused a merge pass to fail on its
first statement with "database is locked" despite a 300-second busy timeout. Under
WAL a reader does not block a writer; verified by running that exact case, where a
write completed in 0.00s with a reader mid-scan of every claim.

`infrastructure.db` is deliberately unchanged and still in delete mode: it is small
and has shown no contention.

## Data flow

The following is the accepted 0051 target data flow. It is not yet the deployed
cross-repository path: Ingester still writes `record/1` or `/2`, Digester writes
`digest/1` scalar locations, Assimilator lacks Asset-derived relations, Workbench
lacks structural and per-Asset challenge APIs, and Assembler lacks stable Record
shells. Those implementation gaps fail closed rather than being inferred from
legacy fields.

Acquisition stores immutable Assets by byte SHA-256. An ordered Selection over one
or more Assets defines a stable Record; the ingester generates its current Ingest
in the access-controlled repository. Initial acquisition creates a whole-Asset
Record automatically. A PDF/image Record explicitly marked temporary may later be
split or composed by the private Workbench from validated complete physical PDF
pages and whole images without reacquiring a source or synthesizing a PDF. Whole
audio, video, web and ebook Records are outside this first structural surface.

For page-mapped PDF/image Records, before extraction the digester derives a
materialised **pre-digest** and source map back through Record pages to Asset pages.
It extracts claims and exact multipart anchors and writes digest 2 to the public
repository. Other media retain digest 1 and cannot use anchor-based evidence or
generated public claim sections in this contract. Public exposure is resolved
per Asset; one member's rights or possession never unlocks another. (Planned
direction: several model digests feed one selected digest; only that digest is
assimilated.)

Human review happens through the Workbench. It corrects Ingests, records review
authority and writes replayable selector or graph-curation input; it does not
normally edit model digests directly.

The assimilator reads the digests and builds and maintains the unified knowledge graph database (SQLite, a lightweight file-based database) from them. Each graph record has a derived import receipt binding it to the canonical digest path and exact digest bytes, so presence alone is not mistaken for freshness. The database is derived data, not the source of truth - if it is deleted, the assimilator rebuilds it and the receipts from the digests.

The synthesiser reads the graph, decides which pages should exist, and emits one language-neutral brief per page (the graph slice that feeds that page). The assembler writes each page's prose from its brief alone - it must not read the graph during assembly (decision 0036). `brief_hash` identifies the ordered semantic selection and covered page members; `payload_hash` separately identifies every writer-visible value, and the article's `built_from` binding copies both. Pushed brief-mode assembly still refreshes related links and aliases from the live graph after hashing, so strict brief-only determinism remains an implementation gap.

A principle runs through all of this: **data flows one direction, and human edits are persisted at the consuming stage's input boundary, then replayed forward - never written back into an earlier stage's derived output.** Workbench record-edits become commits in `ingests` (replayed by the digester); site edits become directives in `content` (replayed by assembly); workbench graph-curation becomes the curation ledger (replayed by the assimilator, [decision 0038](../decisions/0038-graph-curation-replayable-ledger.md)).

Digests are publicly readable on the git hosting platform but are not rendered as pages on the site. The site presents assembled articles only. Each article's references link back to both the original source material and the digest, giving readers a path to verify claims or report errors via the repository's issue tracker. Corrections to digests trigger a database rebuild and article reassembly.

Original source files are archived locally as
`records/{asset_hash}.{ext}` and backed up off-machine. Public-domain and
open-licence Assets may be copied to a public serving zone. Gated Assets remain
private and are available only through the Workbench after per-Asset authority;
private or signed URLs never enter static public content.
