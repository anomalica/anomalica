# Human-gold evaluation format

Human-gold evaluation uses the ingest's existing inline highlights as source
units. It does not copy highlighted spans into another artefact and it does not
ask a reviewer to adjudicate a model's complete claim set. The only sidecar is a
compact record of accepted facts, decisions, progress and attestation.

The canonical machine-readable field list is
[`reference/format-specs.yaml`](../reference/format-specs.yaml)
(`types.highlight_gold`).

## Evaluation registry

[`reference/evaluations.yaml`](../reference/evaluations.yaml) is the central
public index of reference datasets and experiments. Its schema is
`anomalica/evaluation-registry/2`. The registry is deliberately small and static:
it declares identity, ownership, discovery and safety constraints once. It does
not copy lifecycle, gold readiness, counts, blockers or decisions from the
evidence that establishes them. One descriptor has these fields:

- `id`: stable lowercase hyphenated identity, never reused;
- `title` and `purpose`: concise human-readable descriptions;
- `owner_repo`: the `organisation/repository` responsible for the evaluation;
- `evidence`: a stable `provider_id` and `detail_capability`;
- `limits`: public-safe `rights` and `routes` constraints;
- `artifacts`: stable references to implementations, manifests, fixtures,
  reports, results, review interfaces or gold;

The provider id names exactly one artifact in the same descriptor with
`role: state`. A public state provider has a repository-relative JSON path. A
private state provider has no locator and can be resolved only by an explicitly
registered server-side administrator adapter. `detail_capability` is a stable
backend capability id, not frontend data: the aggregation response says whether
that capability is available, and the frontend renders only that response.

The provider or adapter returns `anomalica/evaluation-state/1`:

```json
{
  "schema": "anomalica/evaluation-state/1",
  "evaluation_id": "search-reranker-minilm-vs-granite",
  "evidence": [
    {"artifact_id": "search-reranker-minilm-vs-granite-result", "sha256": "sha256:0123..."}
  ],
  "evidence_sha256": "sha256:4567...",
  "status": "adopted",
  "gold": {"status": "reviewed-derived", "reviewed": 16, "total": 16, "unit": "queries"},
  "decision": {"code": "retain-minilm", "summary": "Retain MiniLM."}
}
```

`status` is exactly one of `proposed`, `ready-for-human-review`, `reviewed`,
`adopted`, `rejected` or `blocked`. Gold status is exactly one of `unavailable`,
`source-reviewed`, `provisional`, `ready-for-human-review`, `human-reviewed` or
`reviewed-derived`. Gold counts are non-negative integers, `reviewed` cannot
exceed `total`, and `unit` names their denominator. `blocked_reason` is required
exactly when lifecycle status is `blocked`. `decision`, when present, has an
owner-defined stable lowercase-hyphenated `code` and concise `summary`.

`evidence` is a non-empty ordered list of stable artifact ids and hashes of their
exact bytes. A public provider may reference only public artifacts declared in
its registry descriptor. A private provider may additionally use stable
item-scoped ids resolved from validated owner data by its allowlisted adapter;
those ids never expose a locator and cannot be supplied by the client.
`evidence_sha256` is SHA-256 of UTF-8 compact JSON for the list, with object keys
sorted, no insignificant whitespace, non-ASCII unescaped and no trailing newline.
The aggregator resolves and hashes every item before returning state. This makes
stale state detectable without putting a mutable expected hash in the static
registry.

A collection evaluation may add `items`, each carrying stable `id`, lifecycle,
gold, optional blocker and decision, and administrator-only `record_id` or
`review_id`. The top-level lifecycle, gold, blocker and decision are derived from
those validated items rather than replacing them with a hand-written aggregate.
Source text, quotes and reviewer identity remain forbidden.

State that depends on private evidence uses a private provider even if an
aggregate would itself be safe to publish. A public summary cannot establish
reviewed, adopted or rejected lifecycle merely by reporting that hidden evidence
exists. The private adapter may return safe record and review ids to an authorised
administrator detail response, but they do not belong in a public state artifact.

An artifact is `{id, role, visibility, repository?, path?}`. `id` is globally
unique within the registry. A `public` artifact requires both `repository` and a
repository-relative `path`; an absolute path is invalid. A `private` artifact
forbids both locator fields and is represented only by its stable id, role and
visibility. An authorised local consumer may map a recognised private id to its
own storage, but it must never derive a filesystem path from registry text or
return that private locator through a public response.

The aggregator fails visibly when a provider, detail capability or evidence
artifact is missing or inaccessible; when schema, evaluation id, vocabulary,
counts or hashes are malformed; or when evidence bytes no longer match the
provider state. It returns a synchronisation error instead of the derived
lifecycle. In particular, inaccessible private evidence cannot produce
`reviewed`, `adopted` or `rejected` state unless an allowlisted administrator
adapter has validated it. Cached last-known state may be diagnostic, but it is
never presented as current.

The registry contains no source quotes, copyrighted bodies, reviewer identities,
private provider or account details, approval evidence, host state or absolute
filesystem paths. `limits` is descriptive reviewer-facing metadata, not dispatch
permission: model and source use must still pass the owning component's enforced
rights and route gates. Workbench serves the index only to administrators and
keeps private artifact resolution behind the same authorised server boundary.

## Source units

One highlight id names one source unit. Once accepted as gold, that unit yields
one or more expected facts; it does not imply exactly one claim. A reviewer may
split a compound passage into several atomic expected facts without drawing
several overlapping highlights over the same words.

A multipart highlight remains one source unit. Each start/end pair is a
separately locatable part, retained as a list in body order. Consumers must not
replace the parts with one enclosing span, because that would make intervening
prose part of the evidence. Display may join the parts with ` [...] `, but
location and overlap operate on the parts separately.

A `highlight-context` edge supplies interpretive context to its dependent
highlight. It does not merge the linked highlights into one source unit. The
dependent unit's evidence is its own parts plus the transitive, resolvable
backwards-linked context needed to resolve attribution, pronouns or references;
its expected facts stay attached to the dependent id. A context highlight may
also be adjudicated as its own unit. A link to a highlight outside a bounded
review range may support a unit inside the range without expanding that range or
asserting that the context unit was reviewed. A dangling or forward context link
must be resolved or the dependent unit deferred.

The ingest body is authoritative for highlight parts and context edges. The
sidecar never repeats their offsets or text.

## Sidecar

The Workbench writes `store/{bare_content_hash}.gold.json` beside the ingest:

```json
{
  "schema": "anomalica/highlight-gold/1",
  "record_hash": "sha256:0123...",
  "body_sha256": "sha256:4567...",
  "ranges": [
    {
      "id": "r1",
      "start": 1200,
      "end": 4800,
      "complete": false,
      "reviewer": {
        "issuer": "github",
        "subject": "1234567",
        "name": "Reviewer name"
      },
      "updated_at": "2026-09-14T12:00:00Z",
      "units": [
        {
          "highlight_id": "h3",
          "decision": "accept",
          "facts": ["The witness reported that the object was intact."]
        },
        {
          "highlight_id": "h7",
          "decision": "split",
          "facts": [
            "The sensor operator reported an object.",
            "The object moved north."
          ]
        },
        {"highlight_id": "h8", "decision": "defer"}
      ]
    }
  ]
}
```

`record_hash` is the ingest's full `content_hash`. `body_sha256` is SHA-256 of
the exact raw stored body after the closing frontmatter fence, expressed as
`sha256:<64 lowercase hex>`. It binds both the range offsets and the inline
markers they refer to. A mismatch makes the sidecar stale and non-gold until a
reviewer reopens it against the new body; consumers must not silently re-anchor
or grade it.

Each entry in `ranges` is one resumable pass over a half-open range of Unicode
code-point offsets into that same raw body. `start` and `end` record only the
boundary reviewed, not highlight spans. `0` through the body length is a
whole-body review. Ranges may follow a natural section, page or time-derived
segment, but the stored boundary is exact and body-bound. Range ids are opaque
and unique within the sidecar. Ranges must not overlap; extend an existing range
or choose another disjoint section instead of double-counting source material.

`reviewer` comes from the authenticated server session, never from client input.
`issuer` plus `subject` is the durable identity; `name` is display data. One
range is one reviewer's resumable pass. A completed range also carries
`attested_at`, set by the server from the authenticated completion save.

## Decisions and batches

The interface presents three to five unresolved highlights at a time and saves
each batch atomically. Fewer are shown only at the end of a range. Saved unit
decisions are the resume cursor: on return, the next batch is the first three to
five source-ordered highlights in range without a decision. Deferred units are
shown again after never-reviewed units. No separate mutable cursor is stored.

Each unit has exactly one decision:

- `accept`: accept one displayed proposed fact unchanged; exactly one fact is
  stored.
- `adjust`: accept reviewer-edited wording; one or more facts are stored.
- `split`: accept two or more atomic facts from the one highlight.
- `reject`: the highlight is not an expected-fact unit; no facts are stored.
- `defer`: leave the unit undecided; no facts are stored, and the range cannot be
  complete.

Facts under `accept`, `adjust` and `split` become human gold only when the
authenticated save succeeds. Draft text and artificial-intelligence-generated
candidates are not gold. Rejected and deferred units are not negative facts.

The interface may show canonical or variant digest claims whose aligned quote
overlaps any part of the current highlight. These are optional proposed facts,
not the review denominator and not a complete model claim set. They are a
derived view and are not copied into the sidecar. A reviewer may accept, adjust
or split one, or ignore all proposals and write the fact directly. A digest
claim's existence, model provenance or overlap never grants gold status.

## Completeness and scoring

`complete: true` is a human attestation that the authenticated reviewer
read the entire bounded range, created any missing highlights needed to represent
its relevant facts, and resolved every fully contained highlight to
`accept`, `adjust`, `split` or `reject`. It is valid only when no such unit is
missing or deferred, all multipart parts and required context links resolve, and
the server has checked the bounded range. The server sets `complete` and
`attested_at` together only as part of an authenticated save after checking those
conditions. `attested_at` is forbidden while incomplete. A complete range may
contain no accepted facts.

A highlight with any part crossing a range boundary is outside that range. It is
reported as a boundary case and excluded from both expected and proposed-fact
denominators; the reviewer can widen the range instead. A model claim is in the
precision denominator only when every separately aligned quote fragment lies
within the range. These rules prevent a bounded attestation from silently making
claims about adjacent, unread text.

An incomplete range supports progress reporting and recall over its adjudicated
accepted facts only. It does not support precision, false-positive rate or F1,
because the expected set is not attested complete. A complete range supports
precision and recall within that range, with the exact range and counts always
reported. No metric from a bounded range may be labelled as whole-record
performance.

Gold matching is fact-level. A model may express one expected fact in a broader
claim or several claims, but duplicate model claims cannot earn duplicate credit.
Source overlap locates candidates and evidence; it is not by itself semantic
agreement with an expected fact.
