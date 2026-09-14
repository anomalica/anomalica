# End-to-end freshness

This is the canonical current-state freshness model from a live ingest record to
deployment. It defines comparisons and scheduler inputs, not a new interchange
artefact. Format fields remain in their own specifications.

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

`artifact` is the stable locator at that boundary: record content hash, canonical
digest path, graph record content hash, brief reference, article path and language,
or deployed path. Consumers group by `(boundary, artifact)`, union reason codes
within a group, and union inherited groups by their own `(boundary, artifact)`.
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
| Live source -> record | The record is not superseded; its schema is supported; `processing.pipeline_version` is an integer equal to the explicit entry for its `source_type` in `store/_pipeline_versions.yaml`. | Counts by source type and `current`/`stale`/`unknown`/`invalid`; for stale records, the integer generation distance `current - recorded`; superseded and dangling-lineage counts separately. |
| Record -> digest | One canonical digest exists; its schema is supported; its `record.content_hash` resolves to the live record; `pre_digest.sha256` equals the SHA-256 of the current materialised pre-digest; `extraction_generation` equals `digest-generation.json`; and `extraction_config` is a valid resolvable fingerprint. | Missing digest count; generation status and distance; input binding match/mismatch/unknown; schema/config invalid counts; claim and node counts remain descriptive, not freshness percentages. |
| Digest -> graph import | The graph has one import receipt for the live record whose `digest_sha256` equals SHA-256 of the exact canonical digest YAML bytes and whose `import_generation` equals the assimilator's current deterministic import generation. | Canonical digests missing from graph, receipt hash mismatches, import-generation distance, graph records with no live canonical digest, and duplicate live record bindings. |
| Graph -> brief | A deterministic re-selection for the brief reference produces the recorded `brief_hash` and `payload_hash`, page identity and publication decision. `generated.graph_version` may trigger this cheap comparison but does not prove it. | Missing briefs; removed, added, content-changed and order-changed selected claims, each as a count against the recorded and current selection sizes; exact payload, page-member, identity, publication and listing-tuple mismatches separately. |
| Brief -> article | The article exists at the brief reference and language; its path resolves to that `<section>/<slug>` brief; and machine-owned `built_from.brief_hash` and `built_from.payload_hash` equal the current brief's hashes. Every cited claim hash is still present in the bound brief. Missing `built_from.payload_hash` against a current brief is an unknown old binding, not current. | Missing articles by language; selection- and payload-hash mismatches; missing/changed citation counts over article citation count; generator-identity drift; body-hash mismatch reported separately as a protected human edit, not stale input. |
| Build -> deployment | A production build from the recorded site commit and committed content commit passes validation, and the remote storage map has exactly the same `(path, SHA-256 of exact bytes)` set. After a changed deployment, sampled live responses match the built bytes after cache purge. | Local paths new/changed, remote-only paths, dead and stripped link counts, dropped redirect counts, live sample mismatches, and the two input commits. |

Machine boundary names are `record-generation`, `digest-input`,
`digest-generation`, `graph-import`, `brief-selection`, `article-input` and
`deployment`. Reason codes are lower-case snake case and stable scheduler input:

- `record-generation`: `record_superseded`, `schema_unsupported`,
  `generation_behind`, `generation_unknown`, `lineage_dangling`;
- `digest-input`: `digest_missing`, `schema_unsupported`,
  `record_binding_mismatch`, `pre_digest_hash_mismatch`,
  `pre_digest_binding_unknown`, `extraction_config_invalid`;
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

The contract above is accepted; the audit found these producer changes still to
land:

- The ingester currently defaults an unregistered type to generation 1. It must
  reject it and explicitly register every supported `source_type` before its
  record can be current.
- Digest generation and exact-configuration fields and their repository manifest
  are specified by [decision 0049](../decisions/0049-digest-extraction-generation-and-freshness.md);
  legacy absent values remain unknown until a separately authorised re-digestion.
- The assimilator scheduler currently treats graph record presence as proof of
  import and uses the latest claim timestamp to trigger brief regeneration. The
  import receipt and deterministic selection comparison replace those proofs;
  the timestamp may remain only as a cheap trigger.
- The scheduler currently distinguishes never-done work but not the full
  published/stale/unknown ordering within `finish`; that sub-order still needs to
  consume the consequence metadata above.
- The assembler emits the canonical flat `built_from` claim freeze. Its readers
  must consume both `built_from.brief_hash` and `built_from.payload_hash` and
  derive the brief reference from the full article path; a legacy article missing
  the latter is not current against a current brief.
- Deployment already compares exact local and remote path hashes and verifies
  sampled live bytes. Its freshness result still needs to expose the site and
  committed content revisions used for that build.
