# Brief format

The brief is the interchange between the synthesiser (producer) and the assembler/writer (consumer), schema `anomalica/brief/1`. It holds exactly the graph slice that feeds ONE page - language-neutral, before any prose - and is the writer's sole input (see [decision 0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)). Like the digest format (0027), it is a versioned interchange spec: breaking changes bump the integer.

The canonical machine-readable field list is [`reference/format-specs.yaml`](../reference/format-specs.yaml) (`types.brief`); this document is its narrative companion.

The v1 field set below is live, grounded against the synthesiser's first-cut brief. Two parts of the intended shape are deferred and marked as such ([Intended but deferred](#intended-but-deferred)) - documented now, built when their gate lands.

## Shape

A YAML document (`.yaml`) - the same serialisation as the digest interchange (0027), not markdown with frontmatter. Top-level keys carry the page identity, the brief hash, the generated stamp, and the related-node candidates; a `claims` list carries the ordered, selected claims with their provenance. Language-neutral throughout - facts, not prose; one brief feeds all N language articles for its page. The fields below are the locked `anomalica/brief/1` contract; YAML is the serialisation.

## Top-level fields

The top-level fields - `schema`, `brief_hash`, `page`, `generated`, `related_nodes` - are listed with their descriptions in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.brief`. This document does not repeat them; the narrative below covers what a field list cannot (slug resolution, the `brief_hash` audit role).

`page.slug` and `related_nodes[].slug` are resolved by the synthesiser at emission via the canonical slugifier (`metadata.explicit_slug` if present, else the shared anomalica-common slugifier - first-last for persons, with deterministic disambiguation; see [node slugs](node-types.md#node-slugs)). They are pre-resolved into the brief because the assembler is writer-only and does not read node metadata; an unresolved slug would silently break pattern-slug URLs and their cross-links.

## `claims` (the selection)

An ordered list of claims - the selection, and the only facts the writer may use. Nothing outside it can enter the prose; this is what makes 0008 enforceable by construction. Order is the synthesiser's. Each claim's fields - `claim_id`, `claim_hash`, `content`, `original_excerpt`, `claim_type`, `attestation`, `speaker`, `node_refs`, `date`/`date_end`, `location_in_record`, `evidence`, `provenance` - are listed in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.brief` (`body.claims`). Note `provenance.content_hash` and `friendly_name`: they link each claim back to its source ingest.

## Identity and audit

`brief_hash` = SHA-256 over the ordered `[(claim_id, claim_hash)]` plus the page identity. One fingerprint, three uses:

- the scheduler's staleness diff unit (the "Something changed?" step - reassemble a page only when its `brief_hash` changes);
- the assembler's freeze (`built_from`) - exactly what an article was built from;
- 0010's "knowledge-graph data" prompt-component audit hash - precise and reconstructable.

This is distinct from `generated.graph_version`, the coarse "knowledge-graph version used" stamp 0010 also records. Both are present in v1 and play distinct roles: `brief_hash` is the precise, per-page, reconstructable hash; `graph_version` is the coarse graph-version stamp. Together they satisfy 0010's audit requirement.

## Intended but deferred

Documented now so the full intended shape is on record; built when its gate lands.

- **Page-level evidence block** - `page.evidence { score, tier, independent_sources }`. The per-claim `evidence{}` is neutral in v1. When the [algorithmic-evidence-scoring draft](../decisions/drafts/algorithmic-evidence-scoring.md) is pinned, a page-level evidence block is added: the synthesiser's page-existence threshold reads it, and it is where the public score surfaces - until then, the provisional "scoring methodology in development" of [0035](../decisions/0035-first-public-artefact-proof-of-method.md) Phase 1. Shape documented here; built when scoring pins.
