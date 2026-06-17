# Knowledge graph schema

The unified knowledge graph is a single SQLite database, built and maintained by the assimilator from the digests (see [assimilator.md](assimilator.md)). It is derived data - rebuildable from the digests, which remain the source of truth. The file is currently at `~/.local/share/digester/knowledge.db`; it relocates to `~/.local/share/assimilator/knowledge.db` when the digester/assimilator split ([decision 0034](../decisions/0034-split-digester-extraction-from-assimilation.md)) moves the database, and is overridable via `ASSIMILATOR_DB`. There is one database (no separate infrastructure database).

Grounded against the assimilator's `database.py` schema (foreign keys on). Six relational tables:

| Table | Columns | Role |
|-------|---------|------|
| `nodes` | `id` PK, `node_type` NOT NULL, `name` NOT NULL, `metadata` (JSON text), `created_at` NOT NULL, `retired_at` | One row per graph node. `retired_at` soft-retires a node on an entity merge. |
| `records` | `id` PK, `title` NOT NULL, `reference`, `date`, `producer_id`, `content_hash`, `friendly_name`, `metadata` (JSON text), `created_at` NOT NULL | One row per source record. |
| `claims` | `id` PK, `content` NOT NULL, `original_excerpt`, `claim_type` NOT NULL, `attestation`, `record_id` NOT NULL (-> `records.id`), `speaker_id`, `location_in_record`, `date`, `date_end`, `confidence` REAL default 1.0, `metadata` (JSON text), `created_at` NOT NULL, `claim_role` | One row per claim. |
| `claim_node_refs` | `claim_id` (-> `claims.id`), `node_id` (-> `nodes.id`), PK(`claim_id`, `node_id`) | The claim-to-entity edges - the connective tissue (every node-to-node relationship passes through a claim). |
| `aliases` | `alias`, `node_id` (-> `nodes.id`), PK(`alias`, `node_id`) | Surface forms for entity resolution. |
| `corroborations` | `claim_a` (-> `claims.id`), `claim_b` (-> `claims.id`), `similarity` REAL NOT NULL, PK(`claim_a`, `claim_b`) | Independent-source agreement edges (the `corroborate` pass output). |

Notes:

- **`claim_role`** is a nullable CHECK enum: `official_explanation`, `witness_testimony`, `investigation_finding`, `cover_up_evidence` (see [node-types.md](node-types.md)). Stored but not yet consumed by the assembler.
- **`confidence`** (REAL, default 1.0) is the evidence-score column. It carries a real, data-derived score once the scoring methodology is defined (the algorithmic-evidence-scoring draft); until then it is the default.
- **`metadata`** columns are JSON-encoded text - free-form per-row extension.
- **Indices:** `nodes(node_type)`, `nodes(name)`, `claims(record_id)`, `claims(speaker_id)`, `claims(claim_role)`, `claim_node_refs(node_id)`, `aliases(node_id)`, `corroborations(claim_a)`, `corroborations(claim_b)`, `records(content_hash)`.

## Embeddings (derived index, not part of the relational contract)

Embeddings and hybrid search are a separate derived layer (the assimilator's embeddings module, sqlite-vec vector tables), rebuildable from the relational data. They are an index over the graph, not part of the schema contract above.

The assembler's read view of this schema (which tables and columns it actually queries to assemble an entity article) is in [assembler.md](assembler.md).
