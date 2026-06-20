# Brief format

The brief is the interchange between the synthesiser (producer) and the assembler/writer (consumer), schema `anomalica/brief/1`. It holds exactly the graph slice that feeds ONE page - language-neutral, before any prose - and is the writer's sole input (see [decision 0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)). Like the digest format (0027), it is a versioned interchange spec: breaking changes bump the integer.

The v1 field set below is live, grounded against the synthesiser's first-cut brief. Two parts of the intended shape are deferred and marked as such ([Intended but deferred](#intended-but-deferred)) - documented now, built when their gate lands.

## Shape

Markdown + YAML frontmatter, a self-contained bundle. The frontmatter carries the page identity, the brief's hash, and the related-node candidates; the body carries the ordered, selected claims with their provenance. Language-neutral throughout - facts, not prose; one brief feeds all N language articles for its page.

## Frontmatter

| Field | Description |
|-------|-------------|
| `schema` | `anomalica/brief/1`. |
| `brief_hash` | SHA-256 over the ordered `[(claim_id, claim_hash)]` plus the page identity - the brief's fingerprint. One value, three uses (see [Identity and audit](#identity-and-audit)). |
| `page` | The page this brief builds: `{ kind: entity, node_id, node_type, title, slug }`. |
| `generated` | `{ graph_version }` - the knowledge-graph version the brief was generated from (the coarse "knowledge-graph version used" stamp 0010 records). |
| `related_nodes` | Nodes co-occurring with the page entity, ranked by shared-claim count - the candidate entities the writer may link to. Each carries its resolved `slug` for cross-links. |

`page.slug` and `related_nodes[].slug` are resolved by the synthesiser at emission (`metadata.explicit_slug` if present, else `slugify(title)` - see [node slugs](node-types.md#node-slugs)). They are pre-resolved into the brief because the assembler is writer-only and does not read node metadata; an unresolved slug would silently break pattern-slug URLs and their cross-links.

## Body: the selected claims

An ordered list of claims - the selection, and the only facts the writer may use. Nothing outside it can enter the prose; this is what makes 0008 enforceable by construction. Order is the synthesiser's. Each claim carries:

| Field | Description |
|-------|-------------|
| `claim_id` | The claim's id in the graph. |
| `claim_hash` | The per-claim fingerprint, verbatim from the claims table - the unit `brief_hash` is built from. |
| `content` | The claim text. |
| `original_excerpt` | The verbatim source quote. |
| `claim_type` | observation / testimony / hearsay / opinion / measurement / administrative (see [node-types.md](node-types.md)). |
| `attestation` | first / second / third-hand, or absent (nullable). |
| `speaker` | `{ node_id, title }` - who asserted the claim. |
| `node_refs` | The domain nodes the claim references. |
| `date`, `date_end` | The claim's date or date range. |
| `location_in_record` | Where in the source record the claim appears (timestamp range, page, paragraph). |
| `evidence` | `{ score, independent_sources }` - neutral until evidence scoring is pinned (see [Intended but deferred](#intended-but-deferred)). |
| `provenance` | `{ record_id, record_title, record_date, record_reference, content_hash, friendly_name }` - the citation and deep-link source for the claim. |

## Identity and audit

`brief_hash` = SHA-256 over the ordered `[(claim_id, claim_hash)]` plus the page identity. One fingerprint, three uses:

- the scheduler's staleness diff unit (the "Something changed?" step - reassemble a page only when its `brief_hash` changes);
- the assembler's freeze (`built_from`) - exactly what an article was built from;
- 0010's "knowledge-graph data" prompt-component audit hash - precise and reconstructable.

This is distinct from `generated.graph_version`, the coarse "knowledge-graph version used" stamp 0010 also records. Both are present in v1 and play distinct roles: `brief_hash` is the precise, per-page, reconstructable hash; `graph_version` is the coarse graph-version stamp. Together they satisfy 0010's audit requirement.

## Intended but deferred

Documented now so the full intended shape is on record; built when its gate lands.

- **Page-level evidence block** - `page.evidence { score, tier, independent_sources }`. The per-claim `evidence{}` is neutral in v1. When the [algorithmic-evidence-scoring draft](../decisions/drafts/algorithmic-evidence-scoring.md) is pinned, a page-level evidence block is added: the synthesiser's page-existence threshold reads it, and it is where the public score surfaces - until then, the provisional "scoring methodology in development" of [0035](../decisions/0035-first-public-artefact-proof-of-method.md) Phase 1. Shape documented here; built when scoring pins.
