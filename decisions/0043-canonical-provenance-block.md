# 0043. A canonical provenance block on records, carried to claims

Date: 2026-07-11
Status: accepted

## Context

Records carry source-origin metadata scattered across many top-level frontmatter fields - `publisher`, `creators`, `source_url`, `source_id`, `fetched_url`, `source_file`, `date_published`, `date_accessed`, plus `copyright`, `classification`, `processing` - with no consistent provenance grouping, and [record-format.md](../architecture/record-format.md) defines no canonical block. A knowledge graph about contested documents needs every claim traceable to its origin - "Department of Energy, Los Alamos, 1949, VIRIN X" - which means provenance must be first-class and flow source -> record -> claim.

The scheduler invented a `provenance` block for the war.gov importer and Mark wants it canonical across every source type. Its draft (`scheduler/.ai/decisions/2026-07-11-provenance-block-proposal.md`) proposed `collection`, `publisher`, `original_date`, `acquired_date`, `location`, `source_url`, `identifiers`, `description`, `license`.

## Decision

### One provenance block, consolidating the scattered fields - not duplicating them

Every record's source-origin metadata lives in ONE `provenance` block in the frontmatter, and that block SUBSUMES the existing scattered top-level fields: they migrate in and the top-level duplicates are dropped. A parallel block that mirrored them would be two sources of truth that drift - the opposite of standardising.

```yaml
provenance:
  collection: "war.gov UFO reading room"      # curated grouping this record belongs to
  publisher: "Department of Energy"           # issuing body / channel / author-org (not the hosting platform)
  creators: ["Edward Teller"]                 # human author(s) / host(s), natural order
  published_date: "1949-03"                   # the SOURCE's own publication / upload date (ISO 8601, may be partial)
  acquired_date: "2026-07-11T09:00:00Z"       # when Anomalica brought the source in
  source_url: "https://www.war.gov/..."       # canonical URL of the original
  fetched_url: "https://web.archive.org/..."  # the URL actually retrieved, when different from source_url
  source_file: "los-alamos-1949.pdf"          # original filename, for a source ingested from a local file with no URL
  identifiers:                                # native source identifiers, keyed by scheme
    virin: "..."
    youtube: "aB8zcAttP1E"
    isbn: "978-..."
    doi: "10..."
  description: "..."                           # the source's OWN blurb, verbatim - never AI-generated
```

Migrated in (dropped from top-level): `publisher`, `creators`, `source_url`, `fetched_url`, `source_file`, `source_id` (-> `identifiers`), `date_published` (-> `published_date`), `date_accessed` (-> `acquired_date`), and the old scalar `provenance` marker. Each source type fills what it has; unknown fields are OMITTED, not null. Origin-unknown is simply the absence of `source_url`/`fetched_url`/`source_file`/`identifiers` - no separate marker is needed (this replaces the old `provenance: unknown` scalar).

### Provenance is facts about the SOURCE, not about the subject

Provenance carries source-origin facts only: who issued or created the source, when it was published or uploaded, when we acquired it, where to find it, its native identifiers, and its own blurb. SUBJECT facts - where an incident happened, when an incident occurred - are NOT provenance; they are claims about place and event nodes in the graph. So the draft's `location` is dropped, and `published_date` is strictly the source's publication date: an incident's place and date are extracted as claims, never stamped into provenance. Mixing subject metadata into provenance would put un-scored, un-corroborated "facts" outside the claim/evidence model.

### Copyright stays authoritative; provenance does not mirror it

`copyright` (carrying `copyright.status`: `public_domain` | `open_licence` | `publicly_accessible` | `licensed` | `restricted`) stays the single authoritative copyright field, top-level. Provenance carries NO `license` mirror - a second copy would drift with no clear winner. `classification` (security markings) likewise stays its own top-level field. Provenance references neither; a consumer needing copyright or classification reads those fields directly.

### `description` is verbatim and non-AI, with a copyright caveat

`description` is the source's OWN blurb or summary, reproduced verbatim, never AI-generated (matching the editorial rule that facts are never invented). Caveat worth stating: reproducing a COPYRIGHTED source's blurb verbatim is itself reproduction - acceptable for public-domain material or short fair-use excerpts, but for a `licensed` or `restricted` source the description is omitted or truncated in line with `copyright.status`, exactly as the source text itself is gated.

### Carried to claims: an authoritative record reference plus a render cache

A claim's authoritative provenance is a reference to its source RECORD - the `record_id` it already carries ([data-model.md](../architecture/data-model.md)); the record holds the provenance block, so there is one source of truth and no per-claim duplication (and the provenance-overlap corroboration logic keeps working unchanged). On top of that, the digest MAY denormalise `publisher` + `published_date` + `collection` onto each claim as a RENDER CACHE, so an article can render "from a 1949 Department of Energy document" without a join back to the record. The cache is DERIVED - recomputed on every re-digest - never authoritative; on any disagreement the record's provenance block wins.

## Why

- **Standardise means one home.** Scattered fields cannot be reasoned about uniformly; a duplicated parallel block is worse (drift). Subsuming is the actual standardisation.
- **Source-versus-subject keeps the graph honest.** Incident place and date must be claims - scored, corroborated, retractable - not provenance metadata that bypasses the evidence model.
- **One authoritative copyright field.** Mirroring `copyright.status` into `provenance.license` invites the two to disagree with no rule for which wins.
- **A reference is the source of truth; the cache is for rendering.** Claims stay thin and correct; display stays join-free.

## Consequences

- [`format-specs.yaml`](../reference/format-specs.yaml) `types.ingest` restructures: a `provenance` object replaces the subsumed top-level fields; `title`, `schema`, `source_type`, `copyright`, `classification`, the hash and `processing` fields stay.
- [record-format.md](../architecture/record-format.md) gains a Provenance section; [data-model.md](../architecture/data-model.md) "Record provenance" updates to the block and the claim carry-through.
- This is a BREAKING frontmatter change (pre-launch, preferred over a compatibility shim): consumers reading top-level `source_url`/`publisher`/`date_published`/etc. switch to `provenance.*`.
- Rollout, routed separately and paced: the ingester writes `provenance` on source records; the digester carries it to claims (authoritative reference + render cache); a backfill migration retro-stamps existing records and moves the old top-level fields into the block. The scheduler's war.gov and channel stubs align to the ratified names.

## Scope

A canonical `provenance` block on records that consolidates scattered source-origin frontmatter into one home, kept strictly to source facts (not subject facts), with `copyright` and `classification` staying authoritative and separate; carried to claims as an authoritative record reference plus a derived render cache. Generalises the scheduler's war.gov draft and drops its `location`, `license`, and incident sense of `original_date` per the source-versus-subject and single-source-of-truth rules. Builds on the provenance-overlap corroboration model ([0039](0039-multi-model-digestion-canonical-reconciliation.md), [data-model.md](../architecture/data-model.md)).
