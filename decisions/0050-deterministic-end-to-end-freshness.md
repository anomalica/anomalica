# 0050. Deterministic end-to-end freshness

Date: 2026-09-14
Status: accepted

## Context

Freshness was implemented as several unrelated checks: record pipeline versions,
pre-digest hashes, digest presence, graph membership, graph timestamps, brief
hashes, article citations and deployment file hashes. Each check is useful at its
own boundary, but a timestamp or one corpus-wide percentage cannot say which
producer is due, whether an output is locally current but inherits an upstream
problem, or what consequence should receive scarce model tokens first.

There are also three contract conflicts. Records without
`processing.pipeline_version` have been described both as neutral and as version
zero; the ingester silently assigns generation 1 to an unregistered source type;
and the brief and content specifications describe `brief_hash` and `built_from`
more abstractly than their deterministic wire forms.

## Decision

[`architecture/freshness.md`](../architecture/freshness.md) is the canonical
current-state model. Every boundary compares the artefact it consumes with the
producer's current declaration or a deterministic reconstruction. It reports its
own stage-native counts and distances, then carries upstream reasons without
turning them into a summed score or percentage.

A freshness finding is grouped by `(boundary, artefact)`. The group contains the
local reason codes for that artefact and inherited groups retain their original
boundary and artefact. Unioning groups and reason codes removes duplicates when
several claims or pages lead back to the same stale digest. A downstream artefact
can therefore be locally current while inheriting an upstream stale or unknown
reason; the report must preserve both facts.

The artefact locators are exact wire identities: a record is its full
`sha256:<content-hash>`; a digest is its canonical repository-relative YAML path;
a graph import is the full `sha256:<record-content-hash>` it binds; a brief is
`<section>/<slug>`; an article is `<section>/<slug>.<language>` without the file
extension; and a deployment artefact is its exact built or public path. These
forms, rather than a title, bare slug, graph timestamp or filesystem modification
time, are the deduplication keys.

The consequence class used for scheduling is independent of the metric:
`repair`, `finish`, `verify`, or `new`, in that order. Within `finish`, production
that has never completed precedes regeneration; known stale published output
precedes known stale unpublished output, then unknown currentness. Free work
precedes token-spending work within the same consequence. Native value and age
remain tie-breakers. Estimated tokens constrain dispatch against an authorised
allowance; they are not divided into severity to create a synthetic score.

Priority is not authorisation. Every dispatch through a remote model stage,
including first generation, requires a quoted approval bound to the exact
candidate set, model, route, reason groups and token/cost or plan-impact estimate.
The scheduler reserves that approval before invoking the transport; a started or
uncertain attempt consumes it. Deterministic stages require no model approval and
may converge independently around blocked model work.

In particular, unknown digest extraction generation is a scheduling signal and
is not permission to invoke a model. A full-corpus generation-1 re-digestion is
not authorised by this decision, by the generation-1 manifest, or by a scheduler
finding. It requires a separately costed and explicitly authorised batch. The
same separation applies to every metered or plan-limited regeneration.

Record pipeline generations and digest extraction generations use the same
three-state comparison: equal is `current`, lower is `stale`, and absent,
malformed, unexpectedly greater, or lacking a current manifest entry is
`unknown`. Unknown is never coerced to zero. The ingester registry and published
manifest must explicitly contain every supported `source_type`; an unregistered
type is an error, not implicit generation 1.

The exact brief selection and payload hashes and the entity-article `built_from`
shape are fixed in [brief-format.md](../architecture/brief-format.md) and
[content-format.md](../architecture/content-format.md). Existing `brief_hash`
bytes are retained. A legacy brief or article missing `payload_hash` has an
unknown old payload binding and is not current; regeneration closes that gap
without pretending the old selection hash covered values it omitted.
`payload_hash_mismatch` is valid only at the `brief-selection` and `article-input`
boundaries: the first compares a rebuilt writer payload with a stored brief and
the second compares the brief payload identity copied into an article.

The assimilator emits a flattened, deduplicated `anomalica-freshness/v1` manifest
from the exact schedule bytes. It binds those bytes by `source_queue_sha256`.
Deployment consumes the manifest only when the caller supplies its expected
SHA-256 and the exact bytes, schema, fields, boundaries and boundary-specific
reason codes validate; otherwise it fails closed. This guarded manifest carries
upstream findings into deployment without making a mutable queue or an
unverified report authoritative.

## Consequences

- A health view reports local metrics with their denominators and reason groups;
  it never offers one end-to-end freshness percentage.
- Import receipts bind graph records to exact digest bytes, allowing a changed
  digest to be distinguished from a merely present digest.
- A graph timestamp may trigger a cheap reconciliation but cannot prove a brief
  fresh; deterministic selection does.
- Free import and synthesis work can settle their local boundaries even while an
  inherited model-derived input remains stale, unknown or approval-blocked.
- Scheduler jobs carry consequence, local reason groups and inherited reason
  groups. Repeated downstream references do not multiply one upstream defect.
- Deployment inherits only a hash-guarded canonical manifest and records the site
  and content commits used for the build.
- Unknown legacy provenance remains visible and actionable without silently
  authorising corpus-wide model work.

## Related

- [Current freshness architecture](../architecture/freshness.md)
- [0040: Pipeline versioning and record supersession](0040-pipeline-versioning-and-supersession.md)
- [0049: Digest extraction generation and freshness](0049-digest-extraction-generation-and-freshness.md)
- [Brief format](../architecture/brief-format.md)
- [Content format](../architecture/content-format.md)
