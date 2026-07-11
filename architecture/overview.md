# Architecture Overview

How the pipeline fits together, end to end. A living document.

**The architecture diagram is not drawn here.** Its single source lives in this meta-repo - `reference/pipeline.mmd` (the topology) and `reference/architecture.yaml` (per-node detail), which the site mounts and renders as the interactive `/architecture/` page. Earlier versions of this document kept an ASCII copy of that diagram; it only drifted, so it is gone. Change the pipeline shape in those two files, not here.

**The repository map and the per-component documentation index live in the [README](../README.md)**, not here. Per-component detail is in the docs the README links (ingester, digester, assimilator, assembler, data model, node types).

What remains below is the one thing neither the diagram nor the per-component docs carry: the connected story of how data moves between the stages.

## Data flow

The ingester writes ingests to the access-controlled ingests repository. The digester reads from that repository and, before extracting, derives a materialised **pre-digest** from each record - the deterministic model-prep (irrelevant regions removed, footnotes inlined, word-timestamps stripped) applied so that the exact model input is itself an inspectable, stored artefact ([decision 0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)). It extracts claims and nodes from the pre-digest and writes digests to the public digests repository. Both the ingester and digester need access to the ingests repository; public exposure of any individual ingest is then gated by that record's copyright status. (Planned direction: the digester may run several models per record and a selector stage picks one selected digest from them; only the selected digest is assimilated - [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md).)

Human review happens through the workbench, which can correct both ingests and digests. Corrections are committed to the appropriate repository with the reviewer's identity as the git author.

The assimilator reads the digests and builds and maintains the unified knowledge graph database (SQLite, a lightweight file-based database) from them. The database is derived data, not the source of truth - if it is deleted, the assimilator rebuilds it from the digests.

The synthesiser reads the graph, decides which pages should exist, and emits one language-neutral brief per page (the graph slice that feeds that page). The assembler writes each page's prose from its brief alone - it does not read the graph (decision 0036). The brief's input hash is the per-page staleness unit and the audit hash 0010 mandates.

A principle runs through all of this: **data flows one direction, and human edits are persisted at the consuming stage's input boundary, then replayed forward - never written back into an earlier stage's derived output.** Workbench record-edits become commits in `ingests` (replayed by the digester); site edits become directives in `content` (replayed by assembly); workbench graph-curation becomes the curation ledger (replayed by the assimilator, [decision 0038](../decisions/0038-graph-curation-replayable-ledger.md)).

Digests are publicly readable on the git hosting platform but are not rendered as pages on the site. The site presents assembled articles only. Each article's references link back to both the original source material and the digest, giving readers a path to verify claims or report errors via the repository's issue tracker. Corrections to digests trigger a database rebuild and article reassembly.

The original source files are archived locally (`sources/`) and pushed off-machine to object storage - a cloud storage bucket - so a non-embeddable original can be served to readers and the archive survives loss of the local machine or link-rot at the origin. Access is routed by the source's copyright status, enforced by the storage zone itself: public-domain and openly-licensed originals sit in an open zone served by a direct URL, while copyrighted originals sit in a token-authenticated zone and are only ever handed out as short-lived signed URLs after the workbench's proof-of-possession gate passes. There is no public URL for gated content, so the split cannot leak copyrighted material.
