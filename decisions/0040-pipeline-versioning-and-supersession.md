# 0040. Pipeline versioning and record supersession

Date: 2026-06-27
Status: accepted

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
`sources/{content_hash}.{ext}` - and is stable across re-EXTRACTION of identical
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
until re-ingested. An ABSENT `pipeline_version` means "generation not declared":
a consumer makes no staleness judgement and shows no badge (NOT treated as 0).
This keeps the field's introduction clean - existing records read as
unversioned, not as a corpus-wide flood of false "outdated (v0 of M)" - and the
metadata backfill (stamping existing records to their generation) assigns the
versions that later bumps measure against. Absent never coincides with a real
bump because the backfill precedes any bump, so present-and-less-than-M is the
only staleness signal in steady state.

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
  `records/` symlink is removed.

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

### Consumer rules (orthogonality)

- `superseded_by` present -> HIDE the record (a newer extraction exists). One
  visible record per source.
- `pipeline_version` PRESENT and `< manifest[media_type]` -> the visible record
  gets an "outdated" badge and is a backfill target, but is still shown.
- `pipeline_version` ABSENT -> no badge (generation not declared), still shown.

### What is explicitly NOT changed

`source_hash` remains web/ebook-only. For audio/video/pdf, `content_hash`
already IS the source-asset SHA-256 (the archived asset lives at
`sources/{content_hash}.{ext}`), so it already serves the workbench's
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
  `architecture/record-format.md` and `reference/format-specs.yaml` carry the
  field specs. The field semantics here are the binding interface.
