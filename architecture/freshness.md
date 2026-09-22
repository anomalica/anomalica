# End-to-end freshness

This is the canonical freshness boundary model from a live ingest record to
deployment. It includes deployed checks and explicitly labelled accepted migration
extensions. Boundary results are scheduler inputs. The only freshness
interchange is the guarded `anomalica-freshness/v1` manifest that carries those
results from scheduling into deployment; its field list is in
[`reference/format-specs.yaml`](../reference/format-specs.yaml).

The `record/3` Record-snapshot and source-map checks below are accepted migration
extensions, not deployed scheduler behaviour. Legacy Records and digests lacking
those bindings are unknown at those checks and cannot gain target-only eligibility.

## Result model

Freshness is a set of boundary results. One result group has:

```yaml
boundary: digest-input
artifact: sha256:<record-content-hash>
local_status: stale # current | stale | unknown | missing | invalid
local_reasons: [pre_digest_hash_mismatch]
inherited: []
consequence: finish
```

`artifact` is the stable locator at that boundary. Its exact forms are:

| Artefact | `artifact` identity |
|---|---|
| Record | Full `sha256:<record-content-hash>` at `record-generation` and `digest-input`. |
| Digest | Canonical repository-relative digest YAML path at `digest-generation`. |
| Graph import | Full `sha256:<record-content-hash>` of the record bound by the import receipt. |
| Brief | `<section>/<slug>` brief reference, with no extension. |
| Article | `<section>/<slug>.<language>`, with no `.md` extension. |
| Deployment | Exact built or public path affected by the finding; `production-build` is the synthetic identity for a failed build before a path exists. |

Consumers group by `(boundary, artifact)`, union reason codes within a group, and
union inherited groups by their own `(boundary, artifact)`.
They do not copy an inherited reason onto the downstream boundary. This is the
deduplication rule: one stale digest remains one finding even when it contributes
many claims to many pages.

`local_status` describes only the local comparison. A brief may match the current
graph selection and still inherit `generation_unknown` from a
`digest-generation` boundary.
Health output shows that as locally current with an inherited reason, not as an
unexplained stale brief. Status counts always name their denominator. There is no
sum, average or universal freshness percentage across boundaries.

## Boundary checks

| Boundary | Locally current when | Stage-native drift metrics |
|---|---|---|
| Live source -> record | The Record carries neither `superseded_by` nor `retired_into` and its schema is supported. Legacy `/1` and `/2` use the deployed scalar generation. **0051 target:** for `record/3`, `processing.asset_pipeline_versions` completely covers the selected Assets and every positive version equals its Asset `source_type` entry in `store/_pipeline_versions.yaml`. | Counts by source type and `current`/`stale`/`unknown`/`invalid`; for stale Asset members, the integer generation distance `current - recorded`; replacement-retired, structurally retired and dangling-lineage counts separately. |
| Record -> digest | One canonical digest exists; its schema is supported for the Record media; its `record.content_hash` resolves to the live record; `pre_digest.sha256` equals the SHA-256 of the current materialised pre-digest; `extraction_generation` equals `digest-generation.json`; and `extraction_config` is a valid resolvable fingerprint. **0051 target:** `record_snapshot_sha256` also matches the current anomalica/digest-record-snapshot/1 projection, and schema 2 has prep version 9 plus an exact current source-map hash. | Missing digest count; generation status and distance; stable Record, mutable Record-snapshot, input and source-map binding match/mismatch/unknown; schema/config invalid counts; claim and node counts remain descriptive, not freshness percentages. |
| Digest -> graph import | The graph has one import receipt for the live record whose `digest_sha256` equals SHA-256 of the exact canonical digest YAML bytes and whose `import_generation` equals the assimilator's current deterministic import generation. | Canonical digests missing from graph, receipt hash mismatches, import-generation distance, graph records with no live canonical digest, and duplicate live record bindings. |
| Graph -> brief | A deterministic re-selection for the brief reference produces the recorded `brief_hash` and `payload_hash`, page identity and publication decision. `generated.graph_version` may trigger this cheap comparison but does not prove it. | Missing briefs; removed, added, content-changed and order-changed selected claims, each as a count against the recorded and current selection sizes; exact payload, page-member, identity, publication and listing-tuple mismatches separately. |
| Brief -> article | The article exists at the brief reference and language; its path resolves to that `<section>/<slug>` brief; and machine-owned `built_from.brief_hash` and `built_from.payload_hash` equal the current brief's hashes. Every cited claim hash is still present in the bound brief. Missing `built_from.payload_hash` against a current brief is an unknown old binding, not current. | Missing articles by language; selection- and payload-hash mismatches; missing/changed citation counts over article citation count; generator-identity drift; body-hash mismatch reported separately as a protected human edit, not stale input. |
| Build -> deployment | A production build from the recorded site commit and committed content commit passes validation, and the remote storage map has exactly the same `(path, SHA-256 of exact bytes)` set. After a changed deployment, sampled live responses match the built bytes after cache purge. | Local paths new/changed, remote-only paths, dead and stripped link counts, dropped redirect counts, live sample mismatches, and the two input commits. |

Machine boundary names are `record-generation`, `digest-input`,
`digest-generation`, `graph-import`, `brief-selection`, `article-input` and
`deployment`. Reason codes are lower-case snake case and stable scheduler input:

- `record-generation`: `record_superseded`, `record_structurally_retired`, `schema_unsupported`,
  `generation_behind`, `generation_unknown`, `lineage_dangling`;
- `digest-input`: `digest_missing`, `schema_unsupported`,
  `record_binding_mismatch`, `pre_digest_hash_mismatch`,
  `record_snapshot_mismatch`, `record_snapshot_binding_unknown`,
  `pre_digest_binding_unknown`, `prep_version_unsupported`,
  `source_map_hash_mismatch`, `source_map_binding_unknown`,
  `extraction_config_invalid`;
- `digest-generation`: `generation_behind`, `generation_unknown`;
- `graph-import`: `import_missing`, `digest_hash_mismatch`,
  `import_generation_behind`, `import_generation_unknown`, `orphan_record`,
  `duplicate_binding`;
- `brief-selection`: `brief_missing`, `selection_hash_mismatch`, `payload_hash_mismatch`,
  `page_identity_mismatch`, `publication_mismatch`, `listing_mismatch`;
- `article-input`: `article_missing`, `brief_hash_mismatch`, `payload_hash_mismatch`,
  `citation_missing`, `citation_hash_mismatch`, `generator_changed`,
  `body_modified`;
- `deployment`: `build_failed`, `path_changed`, `remote_only`, `dead_link`,
  `stripped_link`, `redirect_dropped`, `live_hash_mismatch`.

Several codes may coexist in one group. `body_modified` is protected state and
does not itself request overwrite; `generator_changed` normally has `verify`
consequence until policy explicitly requests regeneration.

`payload_hash_mismatch` is deliberately boundary-specific. At
`brief-selection` it means deterministic re-selection produced a different exact
writer payload from the stored brief. At `article-input` it means the article's
copied `built_from.payload_hash` differs from, or is absent against, the current
brief. It is invalid at record, digest, graph-import and deployment boundaries.

The graph import receipt is derived graph state, not a new source of truth. Its
minimal shape is `(record_content_hash, digest_path, digest_sha256,
import_generation)`. A rebuild recreates it while importing canonical digests.
Changing deterministic import or canonical-input eligibility increments
`import_generation`; old receipts then remain inspectable but are not current. A
contraction of the canonical digest set additionally produces `orphan_record`:
incremental per-record imports cannot remove that graph state and must not claim
convergence. The schedule emits one explicit deterministic rebuild job for the
complete canonical set rather than one deletion-shaped import per orphan.

The rebuild is prepared in an isolated candidate database, replays the complete
curation ledger, and verifies its canonical-input fingerprint, receipts and
integrity before any replacement. Replacing the live graph is one atomic,
explicitly authorised operation; schedule generation and candidate validation do
not mutate it. Accepted replacement changes graph state once, after which normal
brief, article and deployment freshness carries the resulting downstream drift.

The graph's exact input fingerprint is SHA-256 of UTF-8 compact JSON, keys in the
shown order, non-ASCII unescaped and no trailing newline:

```json
{"import_generation":1,"digests":[["record-hash","digests/a.yaml","digest-hash"]],"curation_sha256":"curation-hash"}
```

`digests` contains every receipt as
`[record_content_hash, digest_path, digest_sha256]`, sorted lexicographically by
that triple. A missing curation ledger uses the SHA-256 of empty bytes, not null.
A single database modification time is invalid in write-ahead logging mode and
`MAX(claims.created_at)` omits changes that do not mint a claim; neither is a
freshness identity.

Brief selection compares ordered `(claim_id, claim_hash)` pairs because order is
writer input. Diagnostic set drift must also compare claim hashes, not only claim
identifiers: identifiers locate claims, while hashes detect changed content. The
separate `payload_hash` compares the complete writer-visible page, claim and
related-node values, including context intentionally excluded from `claim_hash`.

Deployment compares a map rather than one aggregate hash so it can distinguish
uploads from removals and name the affected public paths. A successful local build
is not a deployment, and a successful upload is not current until remote bytes and
post-purge live samples agree.

## Guarded deployment manifest

The assimilator writes an adjacent `anomalica-freshness/v1` manifest from the
exact schedule document it has just written. Its fields are `schema`,
`generated_at`, `source_queue_sha256` and `groups`. `source_queue_sha256` is 64
lowercase hexadecimal digits over the exact schedule bytes. `groups` is the
flattened, deduplicated union of local and inherited reason groups, sorted by
`(boundary, artifact)`; each emitted group has `inherited: []` because ancestry
has already been flattened.

The writer refuses to emit the manifest if the schedule bytes differ from the
in-memory schedule used to construct it. Deployment must accept a manifest only
when the path and expected manifest SHA-256 are supplied together. It must hash
the exact manifest bytes before parsing, require `anomalica-freshness/v1`,
validate all required fields and validate every reason against its
boundary-specific vocabulary above.
A missing pair, byte mismatch, malformed manifest, unknown boundary or misplaced
reason fails closed. The deployment result records the accepted manifest path and
hash as `inherited_source`.

## Inheritance

Each producer forwards the union of upstream reason groups attached to the inputs
that actually contributed to its output. It adds one local group only when its own
comparison is not current. It does not fan a record reason out once per claim or a
digest reason out once per page.

An upstream reason does not automatically make every downstream artefact locally
stale. It does affect scheduling consequence where readers are exposed. For
example, a deployed article whose bytes equal the current build can be locally
deployment-current while inheriting an unknown digest generation. This distinction
allows deterministic free stages to converge without pretending the model-derived
input is trustworthy or current.

## Consequence and scheduling

The scheduler orders consequence before resource cost:

| Consequence | Meaning | Examples |
|---|---|---|
| `repair` | A reader-facing artefact is broken, unsafe or no longer eligible. | Dead citation, forbidden record page, missing deployed page, live bytes differing from the deployed build. |
| `finish` | Existing pipeline work cannot reach its intended output, or a known stale/unknown input has a downstream consequence. | Missing first digest/import/brief/article; stale published article; stale digest; unknown extraction generation. |
| `verify` | The current usable artefact remains, and the job measures or improves confidence rather than completing the delivery chain. | Quote check, merge shortlist, health check, generator-identity audit. |
| `new` | Work begins on material not yet in the pipeline. | New intake. |

Within `finish`, order `never_done`, then known stale published, known stale
unpublished, then unknown currentness. Within an equal consequence and completion
state, free work runs before model work, then the producer's native value and
oldest-first starvation guard apply. Token estimates are dispatch constraints and
may pack jobs within an authorised allowance; no `priority / tokens` score may let
cheap low-consequence work outrank repair or completion.

Classification and execution permission are separate fields. A job may be fully
ranked while blocked for authorisation, model availability, review or budget.
Every remote-model `digest`, `assemble`, `translate` and `corroborate` dispatch,
including `never_done`, requires a quoted, expiring approval for the exact
candidate set, model, route, reason groups, token estimates and aggregate cost or
plan impact. The runner atomically reserves one approved candidate before calling
the transport. A started or uncertain attempt consumes that candidate; only a
proved refusal before the call permits reuse under the same approval.

Deterministic `import` and `synthesise` stages do not consume a model approval.
They may run until their local boundaries are current even when they continue to
carry inherited stale or unknown groups. The scheduler does not recreate a
deterministic job merely because its unchanged output inherits such a group, so
free stages converge rather than loop.

Unknown generation creates a candidate and reason; it grants none of those
permissions. Full-corpus generation-1 re-digestion is not authorised. Before any
such batch, the scheduler must show its concrete total token/cost or plan impact
and receive explicit batch approval.

## Exact bindings

- Record generation uses an explicit manifest entry. Missing record field,
  missing manifest entry, malformed value and a record ahead of the manifest are
  all `unknown`; none is version zero.
- Digest source input is the current materialised pre-digest SHA-256, not record
  identity, Git revision or modification time.
- Graph import binds exact canonical digest YAML bytes. Cosmetic YAML changes may
  cause a harmless free re-import; they cannot hide a semantic change.
- Brief selection uses the exact `brief_hash` and `payload_hash` algorithms in
  [brief-format.md](brief-format.md#identity-and-audit).
- Entity articles use the exact `built_from` shape in
  [content-format.md](content-format.md#auditable-assembly).
- Deployment compares exact built-file bytes by public path.

## Current implementation gaps

The following producer-side paths are implemented: normal ingester producers
reject unregistered source types; the digester stamps and validates exact
generation and configuration identities; and the assimilator consumes exact
canonical digest bytes, records import receipts, compares both brief and article
payload bindings, propagates reason groups and writes the queue-bound freshness
manifest. Orphan contraction produces one blocked graph-rebuild control job.

The remaining implementation gaps are:

- Site deployment does not yet consume or validate the guarded freshness
  manifest, record its `inherited_source`, or record immutable site and content
  input commits.
- The assembler requires and copies `payload_hash` into the article's
  `built_from` block, but brief-mode assembly still refreshes related links and
  aliases from the live graph after the brief payload was hashed. The same
  `brief_hash` and `payload_hash` therefore do not yet guarantee identical writer
  input or output.
- The scheduler implements first-completion priority but not the complete
  published-stale, unpublished-stale and unknown `finish` sub-order. It lists
  translation and corroboration as approval-bound stages but does not yet execute
  them, and it does not yet prove that inherited reasons alone cannot recreate an
  unchanged deterministic job across queue regenerations.
- The isolated graph-rebuild executor, candidate validator and atomic replacement
  operation are not yet shipped. The rebuild control job remains blocked and
  cannot mutate the live graph.

Digests created before extraction generation and exact-configuration stamping
remain `unknown` until separately approved re-digestion. Legacy briefs without
`payload_hash` regenerate deterministically. Legacy articles without
`built_from.payload_hash` remain stale until the assembler gap above closes and an
exact article candidate is approved and reassembled. None of these
classifications authorises model work.
