# Knowledge graph schema

The knowledge graph is built and maintained by the assimilator from the digests (see [assimilator.md](assimilator.md)). It is derived data - rebuildable from the digests, which remain the source of truth. The database is at `~/.local/share/assimilator/knowledge.db` (overridable via `ASSIMILATOR_DB`), the location settled by the digester/assimilator split ([decision 0034](../decisions/0034-split-digester-extraction-from-assimilation.md)).

**Two databases, split by file not by flag.** Claims carry a category - `domain` (publishable site content) or `infrastructure` (source-graph cross-references: citations, recommendations, "X cites Y") - recorded per claim in the digest as `anomalica_common.digest.models.ClaimCategory` (enum `domain | infrastructure`, default `domain`). At import the assimilator routes each category to its **own** SQLite file with the **identical** schema below: domain claims to `knowledge.db`, infrastructure claims to `infrastructure.db` (derived as `<db>.parent / "infrastructure.db"`). Both sit side by side in `~/.local/share/assimilator/`. This is why there is no domain/infra column in the tables below - the distinction is the file, not a row attribute. The assembler reads `knowledge.db` only; "the knowledge graph" as a public artefact means the domain database.

Grounded against the assimilator's `database.py` schema (foreign keys on). Six relational tables:

| Table | Columns | Role |
|-------|---------|------|
| `nodes` | `id` PK, `node_type` NOT NULL, `name` NOT NULL, `metadata` (JSON text), `created_at` NOT NULL, `retired_at` | One row per graph node. `retired_at` soft-retires a node on an entity merge. |
| `records` | `id` PK, `title` NOT NULL, `reference`, `date`, `producer_id`, `content_hash`, `friendly_name`, `metadata` (JSON text), `created_at` NOT NULL | One row per source record. |
| `claims` | `id` PK, `content` NOT NULL, `original_excerpt`, `claim_type` NOT NULL, `attestation`, `record_id` NOT NULL (-> `records.id`), `speaker_id`, `location_in_record`, `date`, `date_end`, `confidence` REAL default 1.0, `metadata` (JSON text), `created_at` NOT NULL, `claim_role`, `claim_hash`, `origin_kind`, `origin`, `relay` (JSON text), `entailment_label`, `entailment_score`, `entailment_model`, `entailment_premise`, `origin_ref`, `attribution_in_text` | One row per claim, including its source-local assertion provenance and rendering declaration. |
| `claim_node_refs` | `claim_id` (-> `claims.id`), `node_id` (-> `nodes.id`), `salience`, PK(`claim_id`, `node_id`) | The claim-to-entity edges - the connective tissue (every node-to-node relationship passes through a claim) - with the role each node plays in the claim. |
| `aliases` | `alias`, `node_id` (-> `nodes.id`), PK(`alias`, `node_id`) | Surface forms for entity resolution. |
| `corroborations` | `claim_a` (-> `claims.id`), `claim_b` (-> `claims.id`), `similarity` REAL NOT NULL, PK(`claim_a`, `claim_b`) | Independent-source agreement edges (the `corroborate` pass output). |

Notes:

- **`claim_role`** is a nullable CHECK enum: `official_explanation`, `witness_testimony`, `investigation_finding`, `cover_up_evidence` (see [node-types.md](node-types.md)). Stored but not yet consumed by the assembler.
- **`origin_kind`, `origin`, `origin_ref`, and `relay`** persist the claim's provenance chain from [decision 0044](../decisions/0044-claim-provenance-chain-is-required.md). `relay` is an ordered JSON list from origin to speaker. `origin_ref` is a stable handle for a recurring anonymous source within one record: distinct values may split anonymous roots within that record, but the same value across records never establishes shared identity. Null means the field was not captured, not that no origin or relay exists.
- **`attribution_in_text`** is the extraction writer's nullable declaration, stored as CHECK-constrained `0` or `1`. Consumers use the shared `attribution_mode` rule; they must not infer a missing declaration from claim type, attestation, or provenance. Null remains unknown and fails safe for rendering.
- **`claim_node_refs.salience`** is a nullable CHECK enum: `subject`, `participant`, `setting`, `mentioned`. Null means not assessed, never "not salient". Import preserves the extracted role. A node merge preserves roles when it moves edges; if survivor and victim already reference the same claim, the survivor edge keeps the stronger role in that order (`subject` > `participant` > `setting` > `mentioned` > null), and reversal restores both prior values.
- **`confidence`** (REAL, default 1.0) is the evidence-score column. It carries a real, data-derived score once the scoring methodology is defined (the algorithmic-evidence-scoring draft); until then it is the default.
- **`metadata`** columns are JSON-encoded text - free-form per-row extension.
- **Narrative accounts and account-scoped temporal claim relations are not live graph tables.** They remain evaluation-only and forbidden in canonical digests under [digest-format.md](digest-format.md#planned-accounts-and-claim-linkage); this schema must not infer them from claim locations or dates.
- **Graph maintenance (planned).** The assimilator maintains the graph beyond import. Claim dedup keys on PROVENANCE OVERLAP (`record_id` + `location_in_record`): same source + overlapping location is a duplicate (superseded to one canonical), different sources is corroboration (kept, linked via `corroborations`). The cross-source half exists today (`corroborations` + `scoring.get_independent_source_count`, which counts independent records); the same-source half is net-new - a claim supersede mechanism (a column mirroring `nodes.retired_at`, retiring a deduplicated claim while keeping it linked and inert for audit). Cases provenance cannot settle (same-source different-line; cross-source linking) go through the [0038](../decisions/0038-graph-curation-replayable-ledger.md) curation machinery pointed at claims (propose / confirm / supersede), reversible and replayed on rebuild. Independence is counted by provenance root ([0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md)).
- **Indices:** `nodes(node_type)`, `nodes(name)`, `claims(record_id)`, `claims(speaker_id)`, `claims(claim_role)`, `claim_node_refs(node_id)`, `aliases(node_id)`, `corroborations(claim_a)`, `corroborations(claim_b)`, `records(content_hash)`.

### Rename proposal materialisation

`rename_proposals` is a derived read model reconstructed from proposal files,
the curation ledgers and any exceptional replay dispositions. It has `id` (the
raw proposal id), `proposal_operation_id` (unique canonical
`rename-proposal:<id>`), `node_id` (proposal-time audit id),
`node_name_at_proposal`, `proposed_name`, `reason`, `proposed_by`, `proposed_at`,
`status`, `resolved_at`, `resolution_note`, `resolution_phase`,
`resolution_operation_id`, `compensation_operation_id` and
`replay_disposition_id`.

`status` is `pending`, `applied`, `merged`, `rejected`, `compensated`,
`contraction_drop`, `unresolved_drift` or `invalid`. For `pending`, all operation
and disposition links and `resolved_at` are null. `applied` links one rename
operation; `merged` links one explicitly confirmed merge; and `rejected` links
one rename-phase `reject_proposal` event through `resolution_phase` and
`resolution_operation_id`. `compensated` also carries
`compensation_operation_id`. The three disposition-derived outcomes carry
`replay_disposition_id`; they have no inferred operation link unless that
disposition's closed evidence explicitly supplies one. All operation ids are
canonical namespaced ids, never synthetic graph ids or unqualified legacy ids.
The complete source and reconstruction contract is in
[curation replay dispositions](curation-replay-dispositions.md#rename-proposals).

## Embeddings (derived index, not part of the relational contract)

Embeddings and hybrid search are a separate derived layer (the assimilator's embeddings module, sqlite-vec vector tables), rebuildable from the relational data. They are an index over the graph, not part of the schema contract above.

The assembler's read view of this schema (which tables and columns it actually queries to assemble an entity article) is in [assembler.md](assembler.md).
