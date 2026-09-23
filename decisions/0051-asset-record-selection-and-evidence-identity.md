# 0051. Asset, Record selection and evidence identity

Date: 2026-09-22
Status: accepted

## Context

The existing interchange uses `content_hash` for several different things: the
bytes acquired from a source, the selected logical work, the generated Markdown
path, a public identifier and the key carried into claims. This works while one
source file produces one Record, but it cannot represent several Records from one
container, one Record assembled from several files, or two Records whose selected
pages overlap. `source_hash` partly separates the archived bytes for web and ebook
sources, but only by source type and without a general selection model.

The ambiguity also reaches evidence scoring. A scalar claim location cannot prove
which Asset and pages supplied a claim. Different Record identifiers can therefore
make one overlapping passage look like independent corroboration, while disjoint
passages can be treated as independent without evidence that their works or origins
are distinct.

The first implementable selection surface is narrower than the eventual media
model. The current ingester preserves complete standalone images and complete,
1-based physical PDF pages. It has no trustworthy crop, figure or arbitrary
region coordinates. The architecture must represent what can be validated now
and fail closed on everything else.

## Decision

### Implementation status

This decision is the accepted migration target, not a description of deployed
behaviour. At acceptance, Ingester emits legacy `record/1` or `/2`, Digester emits
`digest/1` with scalar locations, Assimilator has no Asset/Selection/anchor/evidence-unit
tables, Workbench has no structural API or per-Asset challenge, and Assembler has
no stable shell/enrichment split. Until each component implements this contract,
those legacy paths remain current implementation and none may claim `/3`, `/2`
anchors or Asset-derived independence by inference.

### Four distinct layers

- An **Asset** is one immutable acquired byte sequence. Its identity is the full
  `sha256:<64 lowercase hex>` digest of those exact bytes. It owns its archive
  binding, file format, acquisition locator and time, and rights/access metadata.
  Originals are stored and resolved by Asset hash.
- A **Selection** is an ordered list of selectors over one or more Assets. Order
  is semantically significant.
- A **Record** is the stable named logical work defined by one canonical Selection.
  Several Records may select from one Asset or source URL, and one Record may
  compose several Assets. Record metadata does not alter identity.
- An **Ingest** is a generated readable representation of a Record. Re-extraction
  or review edits create a different Ingest revision for the same Record; they do
  not change the Record identity.

The current Git-held Markdown file remains the atomic persisted envelope during
implementation: its frontmatter is the authoritative Record definition and its
body is the current Ingest. The conceptual separation is nevertheless binding.
Exact-body hashes, pre-digest hashes and Git blobs identify generated revisions;
`content_hash` identifies only the Record.

### Canonical Selection

New schema `anomalica/record/3` persists a non-empty `assets` list and a non-empty
ordered `selection` list. An Asset appears once in `assets`; that list is ordered
by first use in `selection`. Every selection element names an Asset hash and one
selector.

The canonical selector vocabulary for the migration target is:

- `{type: whole}` for the complete Asset. Successful ordinary acquisition creates
  exactly one default whole-Asset Record for any source type unless that identical
  canonical Selection already exists. The first Workbench composition surface accepts a whole
  selector only for a standalone image Asset; other whole-Asset Records are not
  structurally edited by this contract.
- `{type: pdf_page, page: N}` for one complete physical PDF page, where `N` is a
  positive 1-based ordinal in that Asset. It is not a printed page label.

An authoring interface may additionally accept
`{type: pdf_page_range, start: N, end: M}`, where both bounds are positive physical
page ordinals and `N <= M`; both bounds are included. Before preview, hashing or
persistence, the server expands it to `pdf_page` values `N..M` in increasing order
and preserves the surrounding selection-list order. Canonical persisted output
contains only `whole` and atomic `pdf_page`
selectors. It never sorts the list. A repeated Asset page, two overlapping input
ranges, a repeated whole Asset, or `whole` combined with another selector for the
same Asset is invalid rather than silently deduplicated. An unsupported selector,
missing Asset, wrong media type, page outside the Asset page count, missing page
text or missing source map also fails closed.

Workbench structuring in this version accepts only whole standalone images and
complete physical PDF pages. It does not synthesize a PDF or other container. A composite has
no fake original at its Record hash. Each member remains archived and addressed by
its own Asset hash.

### Record identity

`content_hash` is the full `sha256:<64 lowercase hex>` Record identity. Compute it
from the canonical expanded Selection only:

1. Form compact UTF-8 JSON with no whitespace or trailing newline and keys in the
   exact order shown: `{"schema":"anomalica/record-identity/1","selection":[...]}`.
2. Each selection element has keys in order `asset_hash`, `selector`. A selector
   has `type` first and, for `pdf_page`, `page` second. Hash strings include the
   `sha256:` prefix and are lowercase. JSON strings use the ordinary JSON escapes
   for control characters; this version admits no other string-valued identity
   input.
3. Prefix those JSON bytes with the 28 ASCII bytes
   `anomalica-record-identity-v1` followed by one zero byte.
4. SHA-256 the complete preimage and prefix the lowercase result with `sha256:`.

Titles, URLs, rights, provenance, Asset acquisition metadata including
`acquired_at`, page labels, extraction output and mutable metadata are excluded.
Asset and selector order are included.

The fixture below hashes to
`sha256:cf74ff9325207f22d92ff805386830db6066ef1ec8a70fa00ce2adc850ff89f3`:

```json
{"schema":"anomalica/record-identity/1","selection":[{"asset_hash":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","selector":{"type":"pdf_page","page":4}},{"asset_hash":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","selector":{"type":"pdf_page","page":5}},{"asset_hash":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","selector":{"type":"whole"}}]}
```

### Page map and source mapping

Every paged `record/3` carries a server-derived `page_map`. Record-local
`file_page` is always the sequential ordinal `1..N` in Selection order. Each map
entry is exactly `{record_page, asset_hash, asset_file_page}`. A whole image maps
to Asset page 1. A whole PDF maps Record pages `1..N` to physical Asset pages
`1..N` in ascending order without rewriting the identity-bearing whole selector.
Atomic PDF pages 4, 5 and 9 selected in that order map Record pages 1, 2 and 3 to
Asset pages 4, 5 and 9. Printed page labels remain verbatim display metadata and
never substitute for either ordinal.

The ingester also retains the deterministic source map from each current Ingest
page through every pre-digest transform. It maps half-open Unicode code-point
intervals in the materialised pre-digest back to half-open intervals in the
canonical extracted text of exactly one Asset page, bound by that page text's
exact `asset_text_sha256`. A transform may collapse or
remove text, but it must carry this map forward. Missing or ambiguous mapping
blocks the structural operation and claim anchoring. Re-extraction, if separately
authorised and completed, is an upstream prerequisite rather than part of preview
or commit; the structural path invokes no provider. A rough model location is
never retained as an exact anchor.

### Claim anchors

For page-mapped PDF/image Records, `anomalica/digest/2` replaces the scalar machine
location with a required, non-empty ordered `source_anchors` list. Each element
contains:

- `asset_hash`, `record_page`, `asset_file_page` and `asset_text_sha256`;
- `asset_span: {start, end}` in Unicode code points in that Asset page's canonical
  extracted text;
- `body_span: {start, end}` in Unicode code points in the exact materialised
  pre-digest named by the digest;
- `quote`, the exact non-empty body substring for that element.

Every interval is half-open `[start, end)`, has integer bounds and `start < end`.
One element cannot cross an Asset or page boundary. One claim may carry several
  elements across pages or Assets. Canonical order is ascending `record_page`, then
  asset-local start and end. Elements are kept separate across elisions; an
enclosing span that includes unquoted prose is invalid. Every anchor must be
contained by the Record Selection and agree with its `page_map`, source map and
quoted substring.

Digest 2 is not a general location schema for audio, video, web or ebook Records;
those formats remain on digest 1 until a later decision defines their typed Asset
coordinates. They cannot contribute anchor-based evidence independence or gain a
public generated claim section under this contract, and therefore remain at the
safe metadata shell. This is deliberate fail-closed scope, not permission to map
their rough scalar locations into page coordinates.

Every new canonical digest also binds the complete mutable graph-relevant Record
projection with `record_snapshot_sha256` under
`anomalica/digest-record-snapshot/1`. Stable `content_hash` continues to identify
the Selection; the separate snapshot makes a title, rights, page-map or
`work_provenance` edit stale rather than allowing old graph metadata to remain
apparently current.

The required source map changes the page-mapped pre-digest contract and therefore requires a
new registered preparation version. A digest with the old preparation version or
only legacy scalar `location` has no canonical anchors. Legacy location remains
readable as display text but cannot drive deduplication, evidence counting or
public claim links; re-digestion performs deterministic realignment. Chunking and
chunk overlap must be sufficient to expose claims spanning adjacent selected
pages or Assets.

When claims with the same proposition and provenance are reconciled, their unique
anchors are unioned in canonical order. They are not emitted as duplicate claims
merely because the evidence is multipart.

### Evidence identity and independence

Anchors identify evidence sites, not provenance roots.

Claims whose anchor intervals overlap in the same Asset, physical page and exact
`asset_text_sha256` frame are always the same
evidence. They cannot corroborate one another and contribute at most one unit to
any support or independence count, regardless of Record, model, wording,
contained-document attribution or claimed provenance root. Touching half-open
intervals do not overlap. Anchors for the same Asset page under different text
frames are overlap-unknown until deterministically remapped. Unmappable coordinates are overlap-unknown and fail
closed rather than being treated as disjoint. Evidence identity is the transitive
connected component of overlap, so bridge overlaps cannot manufacture two units.
Each component's rebuild-stable ID is the full SHA-256 defined by
`anomalica/evidence-unit-identity/1` over its Asset hash, physical page, exact
page-text hash and union half-open span. Sequence numbers, database row ids and
import order are forbidden identities. Briefs carry these IDs and bind them in
their exact `payload_hash`.

Disjoint evidence is not automatically independent. Independence requires
evidenced distinct work or assertion-origin provenance with no established shared
lineage. Different Records, Assets, publishers, speakers, titles or disjoint spans
alone do not establish it. An absent or unresolved root is unknown and adds no
independent count.

Separate documents within one bundle may establish separate roots only when
Record metadata carries distinct `work_provenance.root_id` values and non-empty
supporting evidence. A boundary number, title or author string is insufficient. Without that
evidence all selections fail closed to the shared Asset/container root.
Semantic agreement, evidence identity and provenance independence are stored and
computed separately. A same-fact edge is not itself an independence finding.

### Workbench structuring and lifecycle

The private Workbench may split one temporary parent into several child Records
or compose one Record from several Assets. The client submits only ordered
selections and editable Record metadata. Preview and commit are derived by the
server from one compare-and-swap-bound Git ref and the exact Asset/page source
maps. A parent is temporary only when its live `record/3` frontmatter explicitly
carries `structure_status: temporary`; outputs are final and omit that field.
Commit atomically creates every child or composite and retires every parent;
partial creation is forbidden.

Structural lineage is one-to-many and is stored separately from scalar
replacement supersession. A parent can retire into several children; one child
may cite several structural parents. `superseded_by` remains only for one-to-one
replacement of one Record by another and must not encode a split or composition.
Parent review, housekeeping, gold, verification, digest and graph sidecars do not
inherit mechanically. A child starts without those authorities and each derived
artefact must bind the child Record and current Ingest independently.
Structurally retired parents remain at their canonical store path with
`retired_into`; live discovery excludes either `retired_into` or `superseded_by`,
and reference resolution may still read the retained parent for audit. They are
not placed in `store/v1/`, whose legacy contents have different migration rules.

`by-name/` symlinks are legacy, derived and non-authoritative. Canonical discovery
enumerates the store and validates Selection identity. Writers need not include a
mixed symlink transaction in an otherwise atomic Record operation.

### Access and public pages

Rights and access are resolved for every Asset member. In `record/3`, each
`assets[].copyright` block is authoritative; legacy top-level `copyright` is read
only for `/1` and `/2` Records and cannot widen a member decision. Permission or possession
of one Asset never unlocks another. A composite body or original is available
only to a caller authorised for every contributing member needed by that output;
public reproduction applies the public allow-list independently to each Asset.

In `anomalica/public-record/2`, `source` is exactly `{assets: [...]}` in
first-selection-use order. Each Asset member is exactly `{ordinal, source_type,
file_format, acquired_at?, pages?, selected_record_pages, capabilities}`. The
optional `acquired_at` is copied from that member's
`record/3 assets[].acquisition.acquired_at` only when it is an offset-bearing
RFC 3339 instant (with `Z` or a numeric offset), validates as a real instant and
is safe for public disclosure. A missing, malformed or otherwise unsafe value is
omitted, never set to null, repaired, inferred from another field or substituted
from another Asset. It remains acquisition metadata and does not enter Record
identity.

Public Asset and Record hashes are identifiers, never access credentials. For a
gated local copy the Workbench issues an authenticated, single-use, short-lived
`anomalica/asset-possession-challenge/1` containing a 256-bit nonce and random byte
ranges. The browser submits `anomalica/asset-possession-proof/1`, hashing the nonce,
encoded ranges and exact local bytes; it uploads no source bytes. The server binds
the challenge to session, Asset, use and expiry and compares against its archived
copy. A submitted public hash or a legacy cloze answer cannot grant access.

Every live Record has one stable hash route under `/records/`, using the first 56
hexadecimal characters of its Record `content_hash`. The hash route is canonical
and does not change when the title changes. A title slug may be an alias or
redirect only. Until complete current review and current exact-anchor eligibility,
the route exposes a safe metadata shell, no source body, no gated Asset locator or
generated claims, and carries `noindex`. For a page-mapped PDF/image Record, after
review and current digest-2 eligibility it becomes the indexed
generated explanation and claim page at the same route. Claim links use the
stable Record route plus `#source-{source_anchor_id}`. `source_anchor_id` is the
first 32 hex characters of SHA-256 over the 26 ASCII bytes
`anomalica-source-anchor-v1`, one zero byte, then compact JSON with top-level keys
`schema`, `anchors` in that order. `schema` is
`anomalica/source-anchor-identity/1`; `anchors` is a copy of the anchor list sorted
lexicographically by `asset_hash`, then numerically by `asset_file_page`, then
lexicographically by `asset_text_sha256`, then numerically by span start and end.
Each element contains
each anchor's `asset_hash`, `asset_file_page`, `asset_text_sha256` and `asset_span`
(keys in that order; span keys `start`, `end`; no whitespace or newline). It excludes Record page, body span, quote and claim
wording, so re-digestion and Record reordering do not break the evidence-site link.
A page build fails on a truncated-id collision. Several claims may intentionally
link to the same evidence site.

This one-anchor fixture yields full SHA-256
`84a75f3e0a9e6de863f2f8953f27a527d5a68585288ef34a0f590880d1dd73ba`
and public `source_anchor_id` `84a75f3e0a9e6de863f2f8953f27a527`:

```json
{"schema":"anomalica/source-anchor-identity/1","anchors":[{"asset_hash":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","asset_file_page":4,"asset_text_sha256":"sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","asset_span":{"start":340,"end":517}}]}
```

### Legacy interpretation

An existing `anomalica/record/1` or `/2` file has an implicit one-element
Selection `{type: whole}`. Its Asset hash is `source_hash` when present, otherwise
the legacy `content_hash`. This is a read/migration rule for existing corpus data,
not a producer option and not proof that an old `content_hash` was computed by the
new codec.

Migration is deterministic and fail-closed:

1. Resolve the held archive from the legacy hash and `archived_ext`; never
   reacquire. Recompute SHA-256 over the exact bytes and require it to equal the
   implied Asset hash. Missing bytes, mismatch, missing acquisition metadata or
   missing rights authority blocks that Record.
2. Construct one explicit Asset descriptor from the legacy format, acquisition
   and rights fields and one whole selector. Compute the new Record identity by
   the codec above. Preserve the exact old `{schema, content_hash}` in the new
   Record's `legacy_identities` list.
3. In one compare-and-swap-bound commit, write the new `/3` envelope at
   `store/{bare_new_content_hash}.md`, move the old live envelope and its sidecars
   to `store/legacy-identities/record-{1|2}/{old_content_hash}.*`, preserving the
   old hash's exact lexical form in the filename, and add exactly one old-to-new entry to
   `store/_record_identity_map.yaml` (`anomalica/record-identity-map/1`). Existing
   hash-only references resolve by exact old content hash; `old_schema` is audit
   context, not part of the lookup key. A duplicate old hash, one old hash mapping
   to several new ids, or several old live
   Records collapsing to one new Selection requires human resolution and writes
   nothing.
4. Consumers resolve an old Record reference only through that map. Review,
   housekeeping, gold, verification, digest and graph state remains audit history
   and does not authorise the new `/3` Record; each authority must be regenerated
    or explicitly revalidated against its exact current input. `by-name/` is
    rebuilt as a derived convenience after the canonical commit.

Legacy migration may establish the `/3` Record envelope without fabricating a
source map. If exact current page text or a deterministic source map is absent, the
migration still succeeds after the checks above, but structural preview,
`digest/2`, exact anchors and public generated claims remain blocked until that
upstream material is produced under its own authorised process.

## Consequences

- One Asset can safely yield several live Records and one Record can compose
  several Assets without a synthetic original.
- Record identity is stable across Ingest regeneration but changes when the
  ordered source selection changes.
- Existing single-source ingestion remains automatic: acquisition creates one
  Asset and a default Record that selects it whole. A PDF/image Record is marked
  temporary only when explicitly queued for structural review.
- PDF/image split and composition can ship without pretending crop coordinates
  exist. Finer selectors require a later schema change and source-map support.
- For page-mapped PDF/image Records, digest schema 2 and the new pre-digest
  preparation version are mandatory for machine evidence identity; other media
  remain digest 1, visible but ineligible for anchor-based operations.
- Graph corroboration counts become conservative: overlap always collapses, while
  disjoint or merely cross-Record evidence adds no independence without positive
  provenance evidence.
- Decisions 0039 and 0040 are amended where they equated a Record with one source
  or replacement lineage with every retirement. Decision 0043 remains the work
  provenance direction, split from Asset acquisition facts by this decision.

## Related

- [Record and Ingest format](../architecture/ingest-format.md)
- [Data model](../architecture/data-model.md)
- [Digest format](../architecture/digest-format.md)
- [Knowledge graph schema](../architecture/graph-schema.md)
- [Review Workbench](../architecture/review-workbench.md)
- [0039: Multi-model digestion and canonical reconciliation](0039-multi-model-digestion-canonical-reconciliation.md)
- [0040: Pipeline versioning and record supersession](0040-pipeline-versioning-and-supersession.md)
- [0043: Canonical provenance block](0043-canonical-provenance-block.md)
