# 0040. Pipeline versioning and record supersession

Date: 2026-06-27
Status: accepted

> **Amended 2026-09-22 by [0051](0051-asset-record-selection-and-evidence-identity.md).**
> Extraction generation belongs to the generated Ingest. Several live Records
> may share a source URL or Assets. Scalar `superseded_by` is retained only for
> one-to-one replacement; Workbench split/composition uses separate one-to-many
> structural lineage and an atomic parent-retirement commit. The source-plus-scope
> hash recipe is replaced by the canonical ordered multi-Asset Selection codec.
> Its older legacy re-identification procedure is also replaced: `/1` and `/2`
> migrate through `anomalica/record-identity-map/1`, not `superseded_by`; existing
> hash-only references resolve through that map, and old review, digest, graph and
> sidecar state does not authorise the new `/3` identity without exact revalidation.

> Converged between the ingester and workbench workspaces on 2026-06-27. The
> written form below is pending the workbench's review of the wording; the
> decision itself is settled.

## Context

The ingester re-ingests sources as the pipeline improves - better transcription,
new annotation types, parser fixes. Two distinct problems arise that the record
format did not previously address.

**1. No staleness signal.** A record carries no monotonic indicator of which
pipeline generation produced it. `processing.version` is the ingester's git
short-hash: not ordered, not per-media-type, and absent on older records. A
consumer cannot answer "is this record behind the current extractor?" from it.
The `schema` field (`anomalica/record/1` vs `/2`) is the on-disk FORMAT, not a
generation counter - a record/1 is not stale merely because record/2 exists as a
format.

**2. No supersession guarantee.** When a source is re-ingested, nothing retires
the prior record. For the source-anchored types (audio/video/pdf) whose
`content_hash` is the source-asset hash, a re-DOWNLOAD that returns different
bytes (e.g. a platform re-encoding the media) yields a different `content_hash`,
hence a different store path - so two records for one logical source coexist.
The workbench's browse list (a non-recursive `store/*.md` glob) then shows both.
Observed: the "Skinwalker Ranch Biologist" video (`youtube:0e3-ssiKUMM`) has two
archived downloads (both 137,108,662-byte `.opus`, different hashes), producing
two visible records.

What is NOT the problem: `content_hash` for audio/video is not body-derived. It
is `hash_file(asset_path)` - the source-asset SHA-256, archived at
`records/{content_hash}.{ext}` - and is stable across re-EXTRACTION of identical
bytes. It rotates only across re-DOWNLOAD. A `source_hash` field for these types
would be byte-identical to `content_hash` and would not give a more stable
identity. The only identity stable across re-downloads is the LOGICAL source
identity (`provenance.identifiers`/`provenance.source_url`).

## Decision

### Three orthogonal axes

| Field | Meaning | Bumped when |
|-------|---------|-------------|
| `schema` (`anomalica/record/N`) | On-disk format. | A breaking format change. |
| `processing.pipeline_version` (integer, per media type) | Extraction GENERATION. Drives staleness and backfill. | Extraction output meaningfully changes. |
| `processing.version` (git short-hash) | Fine-grained provenance. | Every commit (unchanged role). |

### pipeline_version

Every record carries `processing.pipeline_version: <int>`. The current version
per media type is a hand-maintained registry in the ingester
(`shared/pipeline_version.py`, `CURRENT_VERSIONS`). A maintainer bumps it when
the extraction OUTPUT changes in a way that warrants re-ingesting existing
records - a new annotation type, a better model, a different segmentation - NOT
on every commit, so it cannot be derived from git. A record whose
`pipeline_version` is PRESENT and less than the current value for its media type
is STALE: a consumer shows it with an "outdated (vN of M)" badge and it is a
backfill target. Staleness does not hide a record - it is the best available
until re-ingested. An ABSENT or malformed `pipeline_version`, an absent manifest
entry, or a record version greater than the manifest is UNKNOWN, never version
zero and never current. It remains visible and is a scheduling signal, reported
separately from known-stale records.

The registry and manifest explicitly list every supported `source_type`.
Silently returning generation 1 for an unregistered type converts a missing
contract into a current record, so an unregistered type is an error. Introducing
a handler requires adding its generation before it can emit a current record.

### Current-version manifest

The ingester writes `store/_pipeline_versions.yaml` into the ingests store on
every run: an upserted map of `{media_type: current_version}`. Consumers read it
to learn M (the current version) for the badge. It sits inside the store
directory, alongside the `store/*.md` records; a consumer globbing records
ignores it. No service endpoint - the data lives where consumers already look.

### Supersession

Supersession is a guarantee, not a convention, keyed on LOGICAL source identity
(`provenance.identifiers`, then `provenance.source_url` - the only identity stable across re-downloads;
the per-download `content_hash` is not). On (re-)ingest of a source that already
has a live root record:

- the new record's frontmatter carries `supersedes: <old_content_hash>`;
- the prior record's frontmatter is stamped `superseded_by: <new_content_hash>`,
  the prior file is moved from `store/{hash}.md` to `store/v1/{hash}.md`, and its
  `by-name/` symlink is removed.

The frontmatter flag is the SOURCE OF TRUTH; the `store/v1/` location is a
derived convenience so a non-recursive `store/*.md` glob naturally excludes
retired records. A consumer hides any record carrying `superseded_by`; among any
records sharing a source identity that slip through (e.g. a failed move), newest
`date_extracted` wins as belt-and-braces.

Supersession is stamped ACROSS schema boundaries: the newest extraction of a
source wins regardless of format (a record/2 supersedes a record/1 of the same
source). It revokes the superseded record's claim to the canonical
`store/{hash}.md` path - the "`store/{sha256}.md` is canonical" invariant holds
for LIVE records. A superseded record remains readable at `store/v1/{hash}.md`
for lineage and audit; consumers should resolve only live records.

**Supersession vs in-place re-extraction.** Supersession applies only when
re-acquisition produces a DIFFERENT `content_hash` - a fresh download for
audio/video (the platform re-encodes, so the asset bytes differ) or a body
change for web/ebook. Re-extraction from the SAME asset keeps the same
`content_hash` and is an IN-PLACE update at `store/{hash}.md` (schema and
`pipeline_version` may bump; identity is stable, so reviews bound to the hash
survive). It is never two records. Consequently the browse list is ALWAYS
one-per-source: there is no on-disk state where record/1 and record/2 of one
source are both live at the store root.

The word-timestamp rollout's `.v2`-suffixed files (`store/{hash}.v2.md` written
during the per-word migration) are vestigial scaffolding from before this
decision: in the corpus each word-level record came from a fresh download (new
hash) with its record/1 predecessor already retired to `store/v1/`, so
one-per-source already holds. The suffix is collapsed to the canonical
`store/{hash}.md` (in-place upgrade) as a follow-up once word-level is the
canonical audio/video output; until then a consumer's dedup (hide
`superseded_by`, newest `date_extracted` tiebreak) covers any stray.

### Historical consumer rules (superseded where amended above)

- `superseded_by` present -> HIDE the record (a newer extraction exists). One
  visible record per source.
- `pipeline_version` PRESENT and `< manifest[media_type]` -> the visible record
  gets an "outdated" badge and is a backfill target, but is still shown.
- `pipeline_version` ABSENT, malformed or not comparable -> unknown-generation
  badge, still shown and eligible for separately authorised backfill.

### What the 2026-06-27 decision did not change (historical)

`source_hash` remains web/ebook-only. For audio/video/pdf, `content_hash`
already IS the source-asset SHA-256 (the archived asset lives at
`records/{content_hash}.{ext}`), so it already serves the workbench's
source-asset review-identity tier (review-workbench.md, "Possession key"). A
separate `source_hash` for these types would be byte-identical and is not
emitted.

## Consequences

- Backfill: records below the current `pipeline_version` for their media type
  are re-ingested; the 10 record/1 videos (incl. Skinwalker) first. Backfill
  runs on the Claude subscription - no metered spend.
- The digester sees supersession via frontmatter and can avoid re-consuming
  retired records.
- Cross-component contract: the workbench reads the manifest and the flags;
  `architecture/ingest-format.md` and `reference/format-specs.yaml` carry the
  field specs. The field semantics here are the binding interface.

## Amendment 2026-07-25: identity is source + selection, and the resolution path is normative

This record's "Supersession vs in-place re-extraction" rule contained a
contradiction that bit only body-anchored types. It said supersession
fires on "a body change for web/ebook", and also that "re-extraction from
the SAME asset keeps the same `content_hash` ... identity is stable, so
reviews bound to the hash survive". For web, ebook, and scoped-excerpt
records both could not hold: `content_hash` *was* the body hash, so
re-extraction from an unchanged asset changed identity, and the promise
that bound reviews survive was false precisely where it was most needed.

Resolved by removing the cause rather than adding machinery:
**`content_hash` hashes the source asset plus the selection, never the
extracted body** ([ingest-format.md](../architecture/ingest-format.md#store)).
Re-extraction - a better extractor, a page-chrome strip, chapter-number
repair, email thread segmentation - no longer changes identity for any
type. The in-place update this record already blesses becomes the uniform
behaviour, and the sentence above becomes true as written.

Supersession is unchanged and still fires on re-**acquisition**: a fresh
download whose bytes differ is a different source asset, hence a
different identity, stamped exactly as this record specifies.

**Resolution is normative, because two components implemented it
differently.** Retirement moves the prior file to `store/v1/{hash}.md`;
`store/{hash}.md` is then absent. A consumer holding an old hash must
therefore resolve in this order, and a consumer that stops at the first
step reports a silent drop - a missing body, a skipped record, and a
sweep that still exits successfully:

1. `store/{hash}.md` - live record, use it.
2. `store/v1/{hash}.md` - retired; read `superseded_by` and repeat from
   step 1 with that hash.
3. Neither - a genuine dangling reference. Report it; never treat it as
   an empty record.

The guarantee this places on the producer: **retirement must never leave
nothing resolvable at the old identity.** The retired file at
`store/v1/{hash}.md` carrying `superseded_by` is what satisfies it. A
retirement that deletes rather than moves breaks every stored pointer,
and the failure is silent at every consumer.

**The migration computes the new hash from the ARCHIVED ASSET ON DISK,
never by re-fetching.** A re-fetch can return different bytes - a page
changes, a server re-encodes - and would silently convert a
re-identification into a re-acquisition, giving the record an identity
that reflects today's fetch rather than the artefact actually held. The
asset is already archived under `records/`; hash that.

This amendment originally proposed stamping the one-off migration through
`superseded_by` and resolving digest, pre-digest and review pointers forward. That
procedure never became the 0051 migration contract and is superseded. Legacy `/1`
and `/2` identities now resolve only through
`anomalica/record-identity-map/1`; old artefacts remain history and confer no
authority on `/3` without exact revalidation.

> **Note 2026-09-11:** Housekeeping's `input_sha256` is deliberately a
> different identity from `content_hash`. Decision
> [0048](0048-post-ingest-housekeeping-is-content-versioned.md) hashes the
> complete exact ingest Markdown bytes to decide whether that derived pass is
> current; this does not alter the source-plus-selection record identity or
> supersession rules above.

> **Note 2026-09-22:** The 2026-07-25 “asset plus normalised scope string”
> identity and one-visible-Record-per-source statements are superseded by 0051.
> Legacy `/1` and `/2` Records retain an explicit implicit-whole read rule; new
> `/3` Records persist Assets and atomic ordered selectors.
