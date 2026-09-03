# Architecture Overview

How the pipeline fits together, end to end. A living document.

**The architecture diagram is not drawn here.** Its single source lives in this meta-repo - `reference/pipeline.mmd` (the topology) and `reference/architecture.yaml` (per-node detail), which the site mounts and renders as the interactive `/architecture/` page. Earlier versions of this document kept an ASCII copy of that diagram; it only drifted, so it is gone. Change the pipeline shape in those two files, not here.

**The repository map and the per-component documentation index live in the [README](../README.md)**, not here. Per-component detail is in the docs the README links (ingester, digester, assimilator, assembler, data model, node types).

What remains below is the one thing neither the diagram nor the per-component docs carry: the connected story of how data moves between the stages.

**Every step in order, with what makes it due and what it costs, is in [pipeline-stages.md](pipeline-stages.md)** - the answer to "when does the quote check happen" or "what runs after an import".

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

The ingester writes ingests to the access-controlled ingests repository. The digester reads from that repository and, before extracting, derives a materialised **pre-digest** from each record - the deterministic model-prep (irrelevant regions removed, footnotes inlined, word-timestamps stripped) applied so that the exact model input is itself an inspectable, stored artefact ([decision 0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)). It extracts claims and nodes from the pre-digest and writes digests to the public digests repository. Both the ingester and digester need access to the ingests repository; public exposure of any individual ingest is then gated by that record's copyright status. (Planned direction: the digester may run several models per record and a selector stage picks one selected digest from them; only the selected digest is assimilated - [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md).)

Human review happens through the workbench, which can correct both ingests and digests. Corrections are committed to the appropriate repository with the reviewer's identity as the git author.

The assimilator reads the digests and builds and maintains the unified knowledge graph database (SQLite, a lightweight file-based database) from them. The database is derived data, not the source of truth - if it is deleted, the assimilator rebuilds it from the digests.

The synthesiser reads the graph, decides which pages should exist, and emits one language-neutral brief per page (the graph slice that feeds that page). The assembler writes each page's prose from its brief alone - it does not read the graph (decision 0036). The brief's input hash is the per-page staleness unit and the audit hash 0010 mandates.

A principle runs through all of this: **data flows one direction, and human edits are persisted at the consuming stage's input boundary, then replayed forward - never written back into an earlier stage's derived output.** Workbench record-edits become commits in `ingests` (replayed by the digester); site edits become directives in `content` (replayed by assembly); workbench graph-curation becomes the curation ledger (replayed by the assimilator, [decision 0038](../decisions/0038-graph-curation-replayable-ledger.md)).

Digests are publicly readable on the git hosting platform but are not rendered as pages on the site. The site presents assembled articles only. Each article's references link back to both the original source material and the digest, giving readers a path to verify claims or report errors via the repository's issue tracker. Corrections to digests trigger a database rebuild and article reassembly.

The original source files are archived locally (`records/`, one file per original named `{content_hash}.{ext}`) and pushed off-machine to object storage - a cloud storage bucket - so a non-embeddable original can be served to readers and the archive survives loss of the local machine or link-rot at the origin. Access is routed by the source's copyright status, enforced by the storage zone itself: public-domain and openly-licensed originals sit in an open zone served by a direct URL, while copyrighted originals sit in a token-authenticated zone and are only ever handed out as short-lived signed URLs after the workbench's proof-of-possession gate passes. There is no public URL for gated content, so the split cannot leak copyrighted material.
