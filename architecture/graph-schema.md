# Knowledge graph schema

The knowledge graph is built and maintained by the assimilator from the digests (see [assimilator.md](assimilator.md)). It is derived data - rebuildable from the digests, which remain the source of truth. The database is at `~/.local/share/assimilator/knowledge.db` (overridable via `ASSIMILATOR_DB`), the location settled by the digester/assimilator split ([decision 0034](../decisions/0034-split-digester-extraction-from-assimilation.md)).

**Two databases, split by file not by flag.** Claims carry a category - `domain` (publishable site content) or `infrastructure` (source-graph cross-references: citations, recommendations, "X cites Y") - recorded per claim in the digest as `anomalica_common.digest.models.ClaimCategory` (enum `domain | infrastructure`, default `domain`). At import the assimilator routes each category to its **own** SQLite file with the **identical** schema below: domain claims to `knowledge.db`, infrastructure claims to `infrastructure.db` (derived as `<db>.parent / "infrastructure.db"`). Both sit side by side in `~/.local/share/assimilator/`. This is why there is no domain/infra column in the tables below - the distinction is the file, not a row attribute. The assembler reads `knowledge.db` only; "the knowledge graph" as a public artefact means the domain database.

The current six-table implementation is the migration baseline. Decision 0051
requires the additional derived structures below before Asset-overlap can affect
scoring; until then independence calculations that lack them fail closed rather
than treating each Record as a distinct source.

| Table | Columns | Role |
|-------|---------|------|
| `nodes` | `id` PK, `node_type` NOT NULL, `name` NOT NULL, `metadata` (JSON text), `created_at` NOT NULL, `retired_at` | One row per graph node. `retired_at` soft-retires a node on an entity merge. |
| `records` | `id` PK, `title` NOT NULL, `reference`, `date`, `producer_id`, `content_hash`, `friendly_name`, `metadata` (JSON text), `created_at` NOT NULL, `work_id` | One row per stable Record Selection. `work_id` is an evidenced work root; null means unknown and never falls back to a distinct counting root. |
| `claims` | `id` PK, `content` NOT NULL, `original_excerpt`, `claim_type` NOT NULL, `attestation`, `record_id` NOT NULL (-> `records.id`), `speaker_id`, `location_in_record` (legacy display only), `date`, `date_end`, `confidence` REAL default 1.0, `metadata` (JSON text), `created_at` NOT NULL, `claim_role`, `claim_hash`, `origin_kind`, `origin`, `relay` (JSON text), `entailment_label`, `entailment_score`, `entailment_model`, `entailment_premise`, `origin_ref`, `attribution_in_text` | One row per claim. Exact location is normalised into `claim_anchors`; the scalar is non-authoritative legacy display data. |
| `claim_node_refs` | `claim_id` (-> `claims.id`), `node_id` (-> `nodes.id`), `salience`, PK(`claim_id`, `node_id`) | The claim-to-entity edges - the connective tissue (every node-to-node relationship passes through a claim) - with the role each node plays in the claim. |
| `aliases` | `alias`, `node_id` (-> `nodes.id`), PK(`alias`, `node_id`) | Surface forms for entity resolution. |
| `corroborations` | `claim_a` (-> `claims.id`), `claim_b` (-> `claims.id`), `similarity` REAL NOT NULL, PK(`claim_a`, `claim_b`) | Semantic same/supporting-fact agreement edges. An edge is not an independence finding. |
| `assets` | `asset_hash` PK, `metadata` (JSON text) | Immutable Asset identities and derivative lineage imported from the digest Record's public structural Asset projection; acquisition and private rights evidence are not copied. |
| `record_selections` | `record_id`, `ordinal`, `asset_hash`, `selector_type`, `asset_file_page`, PK(`record_id`, `ordinal`) | Canonical expanded ordered Record Selection. |
| `claim_anchors` | `claim_id`, `ordinal`, `asset_hash`, `record_page`, `asset_file_page`, `asset_text_sha256`, `asset_start`, `asset_end`, `body_start`, `body_end`, `quote`, PK(`claim_id`, `ordinal`) | Exact typed half-open source-anchor elements. |
| `evidence_units` | `id` PK, `asset_hash`, `asset_file_page`, `asset_text_sha256`, `span_start`, `span_end` | Derived transitive connected components of overlapping intervals in one exact Asset-page text frame. `id` is the full `anomalica/evidence-unit-identity/1` SHA-256. |
| `claim_evidence_units` | `claim_id`, `evidence_unit_id`, PK(`claim_id`, `evidence_unit_id`) | Claim membership in evidence units. |
| `provenance_roots` | `id` PK, `status`, `kind`, `metadata`, `evidence` | Evaluable work/assertion roots. Status is `established` or `unknown`; unknown roots never add an independent count. |
| `claim_provenance_roots` | `claim_id`, `provenance_root_id`, `basis`, PK(`claim_id`, `provenance_root_id`) | Explicit claim-to-root derivation. `basis` records the evidence/derivation kind; no consumer falls back to Record identity. |
| `provenance_lineage` | `root_a`, `root_b`, `relation`, `evidence` | Established shared, derived or distinct lineage used separately from evidence overlap. |

Notes:

- **`claim_role`** is a nullable CHECK enum: `official_explanation`, `witness_testimony`, `investigation_finding`, `cover_up_evidence` (see [node-types.md](node-types.md)). Stored but not yet consumed by the assembler.
- **`origin_kind`, `origin`, `origin_ref`, and `relay`** persist the claim's provenance chain from [decision 0044](../decisions/0044-claim-provenance-chain-is-required.md). `relay` is an ordered JSON list from origin to speaker. `origin_ref` is a stable handle for a recurring anonymous source within one record: distinct values may split anonymous roots within that record, but the same value across records never establishes shared identity. Null means the field was not captured, not that no origin or relay exists.
- **`attribution_in_text`** is the extraction writer's nullable declaration, stored as CHECK-constrained `0` or `1`. Consumers use the shared `attribution_mode` rule; they must not infer a missing declaration from claim type, attestation, or provenance. Null remains unknown and fails safe for rendering.
- **`claim_node_refs.salience`** is a nullable CHECK enum: `subject`, `participant`, `setting`, `mentioned`. Null means not assessed, never "not salient". Import preserves the extracted role. A node merge preserves roles when it moves edges; if survivor and victim already reference the same claim, the survivor edge keeps the stronger role in that order (`subject` > `participant` > `setting` > `mentioned` > null), and reversal restores both prior values.
- **`confidence`** (REAL, default 1.0) is the evidence-score column. It carries a real, data-derived score once the scoring methodology is defined (the algorithmic-evidence-scoring draft); until then it is the default.
- **`metadata`** columns are JSON-encoded text - free-form per-row extension.
- **`records.work_id`** never defaults to `records.id` for counting. An unlinked
  Record has unknown work identity, not a fresh independent root. Page gating and
  source spread use only positively established roots and report unknowns separately.
  Import populates it only from validated `record/3.work_provenance.root_id` with
  non-empty evidence or from an explicit replayable graph-curation operation.
- **Narrative accounts and account-scoped temporal claim relations are not live graph tables.** They remain evaluation-only and forbidden in canonical digests under [digest-format.md](digest-format.md#planned-accounts-and-claim-linkage); this schema must not infer them from claim locations or dates.
- **Evidence identity is mandatory and deterministic.** Claims whose anchors
  overlap on the same Asset physical page under the same `asset_text_sha256` are
  one evidence unit and can contribute at most once,
  even across different Records. Half-open intervals touching only at a boundary
  do not overlap. Connected components make overlap transitive. An unmappable pair
  is unknown, never disjoint. Different text-frame hashes for one Asset page are
  also unknown until deterministically remapped.
- **Evidence-unit IDs are rebuild-stable.** For each exact Asset-page/text-frame
  tuple, import first combines domain and infrastructure anchors from the complete
  canonical digest set, before routing claims to separate databases. It sorts those
  intervals by `(start, end,
  claim_id, ordinal)`, computes transitive overlap components using strict
  `next.start < component.end`, and gives each component the union
  `[minimum start, maximum end)`. It then derives the full ID using
  `anomalica/evidence-unit-identity/1`; database row order, import time and
  allocator state are forbidden inputs. A later bridge interval may deliberately
  merge components and change their IDs. Brief claims carry the resulting sorted
  unique IDs, so `payload_hash` binds the exact evidence grouping presented to the
  writer.
  Each database stores only claim memberships for its resident claims, but uses the
  globally computed component ID and union span; category routing cannot split or
  merge evidence identity.
- **Independence is separate.** Disjoint evidence, different Records and different
  Assets are not automatically independent. Distinct support requires positively
  evidenced work or assertion-origin roots with no established shared lineage.
  Separate documents in one bundle inherit the shared Asset/container root unless
  Record metadata establishes distinct provenance roots. Agreement edges remain
  useful when independence is zero or unknown.
- **Indices:** `nodes(node_type)`, `nodes(name)`, `claims(record_id)`, `claims(speaker_id)`, `claims(claim_role)`, `claim_node_refs(node_id)`, `aliases(node_id)`, `corroborations(claim_a)`, `corroborations(claim_b)`, `records(content_hash)`, `records(work_id)`.

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
