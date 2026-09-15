# Curation replay dispositions

This is the durable interchange contract for exceptional merge, rejection and
rename replay outcomes. Ordinary successful replay belongs in the isolated
candidate validation report, not this ledger.

## Location and ownership

The curation repository owns `replay-dispositions.yaml` at
`$ANOMALICA_CURATION_DIR/replay-dispositions.yaml`. Its schema is
`anomalica/curation-replay-dispositions/1`. One shared append-only ledger covers
the `merge`, `rejection` and `rename` source phases because a later operation may
supersede one from another phase.

The assimilator owns schema validation, deterministic classification proposals
and read-only consumption. An operator-authorised curation commit accepts an
entry. Candidate generation alone never writes this file. It is non-materialising
and excluded from the graph's `curation_sha256`; candidate validation binds its
separate exact-byte `disposition_ledger_sha256`.

## Document shape

The top-level object has exactly `schema` and `entries`. Each entry has:

```yaml
id: sha256:<64 lowercase hex>
source_phase: merge # merge | rejection | rename
operation_id: <canonical source operation id>
source_graph_input_fingerprint: sha256:<64 lowercase hex>
candidate_graph_input_fingerprint: sha256:<64 lowercase hex>
outcome: applied
evidence: {}
classified_at: 2000-01-01T00:00:00Z
classifier:
  implementation: assimilator
  commit: <40 lowercase Git hex>
supersedes_disposition_id: null
```

All fields are required, including a null `supersedes_disposition_id`. Objects
reject unknown keys. Names, node types, reasons, operation ids and classifier
implementations are non-empty strings. Timestamps are valid ISO 8601 offset
timestamps normalised to UTC `Z`. Fingerprints match
`^sha256:[0-9a-f]{64}$`; claim fingerprints and Git commits match
`^[0-9a-f]{64}$` and `^[0-9a-f]{40}$` respectively.

The allowed outcomes are `applied`, `absorbed`, `superseded`, `compensated`,
`contraction_drop`, `unresolved_drift`, `unconfirmed` and `invalid`.

## Disposition identity and chains

The entry id is SHA-256 of this exact UTF-8 compact JSON projection, with keys in
the shown order, non-ASCII unescaped and no trailing newline:

```json
{"schema":"anomalica/curation-replay-disposition-id/1","source_phase":"merge","operation_id":"operation-id","source_graph_input_fingerprint":"sha256:source","candidate_graph_input_fingerprint":"sha256:candidate","outcome":"applied","evidence":{},"supersedes_disposition_id":null}
```

Values replace the examples without changing key order. Nested evidence objects
use the key order specified below. String arrays are unique and sorted
lexicographically. Object arrays are unique and sorted by their own compact
canonical JSON bytes. `classified_at` and `classifier` are audit data and do not
participate in the id.

The basis key is `(source_phase, operation_id,
source_graph_input_fingerprint, candidate_graph_input_fingerprint)`. A basis has
exactly one root. Reclassification appends an entry whose
`supersedes_disposition_id` names the current unique tip of the same basis. The
referenced entry must already exist and precede the replacement by
`(classified_at, id)`. Each entry has at most one successor. Cross-basis links,
branches, cycles, duplicate ids and multiple active tips fail validation. The
active classification is the unique chain tip, not the greatest timestamp. A
different fingerprint pair starts a new basis; old bases remain history and
cannot authorise the current candidate.

## Evidence shapes

The shared closed shapes are:

- `NaturalIdentity`: `{name, node_type, prior_names}`, with unique sorted
  `prior_names`.
- `ResolvedIdentity`: `{identity, resolved}`, where `identity` is a
  `NaturalIdentity` and `resolved` is exactly `{name, node_type}`.
- `SupportLocator`: `{record_content_hash, claim_fingerprint}`.
- `OperationRef`: `{source_phase, operation_id}`.

Each outcome admits exactly these evidence keys and types:

| Outcome | Evidence |
|---|---|
| `applied` | `{resolved_identities: [ResolvedIdentity, ...], postcondition}`; the list is non-empty and postcondition is `merged`, `distinct` or `renamed`, matching the source phase. |
| `absorbed` | `{resolved_identities: [...], absent_identities: [NaturalIdentity, ...], postcondition}`; both lists are non-empty. |
| `superseded` | `{superseded_by: OperationRef, resolved_identities: [...], postcondition}`; the resolved list is non-empty and the referenced later active operation proves the earlier postcondition. |
| `compensated` | Normally `{compensated_by: OperationRef}` naming an explicit later reversal. For a historical rename proposal fulfilled and then semantically reversed, it is exactly `{applied_by: OperationRef, compensated_by: OperationRef}`; the second rename must restore the original exact typed name. |
| `contraction_drop` | `{absent_identities: [NaturalIdentity, ...], absent_support_locators: [SupportLocator, ...]}`; both lists are non-empty and every locator is proved absent from the candidate. |
| `unresolved_drift` | `{unresolved_identities: [NaturalIdentity, ...], surviving_support_locators: [SupportLocator, ...], reason}`; the reason is non-empty and at least one list is non-empty. |
| `unconfirmed` | `{reason}` with a non-empty string. |
| `invalid` | `{field_paths: [JSON Pointer, ...], reason}`; both are non-empty and paths are unique and sorted. |

`applied`, `absorbed`, `superseded`, `compensated` and `contraction_drop` are
replacement-safe only when their evidence validates against the bound candidate.
The other outcomes block replacement.

Natural identity resolution first collects exact `name + node_type` matches
against canonical node names and aliases for the declared name and all
`prior_names`. It must find one unique node. Only when that set is empty may the
declared deterministic non-fuzzy matching tiers run, again collecting all results
and requiring one unique node. Fuzzy, cross-type and first-match resolution are
invalid. Two rejection identities resolving to one node require explicit
superseding-merge or contraction evidence; they are not automatically absorbed.

## Required operations

The disposition ledger is exceptional-only. The validator derives its required
set independently:

1. Parse every base merge, rejection and rename operation, every rename proposal,
   and every explicit reversal from the material curation inputs.
2. Apply valid reversals. An explicitly reversed base operation is reported as
   normally compensated and requires no disposition.
3. Require strict normal replay to return exactly one result for every valid,
   confirmed, uncompensated operation. Exact postcondition materialisation is
   reported as normally applied and requires no disposition.
4. Require a disposition basis for every stable-id unconfirmed or invalid entry
   and every uncompensated operation not normally applied. A malformed entry with
   no stable id blocks outside the ledger.

The validator rejects missing or duplicate replay results, unknown operation ids,
and any mismatch between the derived required bases and current ledger tips. A
fresh `applied` or `compensated` root is redundant and invalid. Those outcomes may
appear only as successors closing an existing same-basis exceptional chain after
independent replay or source inventory proves the normal outcome. Existing
current-basis chains therefore remain in the expected-tip set until closed.
Different-fingerprint history is structurally validated but does not count towards
current coverage.

Source operations replay by `(timestamp, stable operation id)` within fixed
dependency phases: import, merges, rejection materialisation, renames, then
dependent curation. Disposition entries replay by `(classified_at, id)`.

## Rename proposals

Every well-formed `rename-proposals/*.json` file is a base request in the rename
phase. Its canonical operation id is `rename-proposal:<id>` and its timestamp is
`proposed_at`. The filename, synthetic `node_id`, and SQLite status are not source
identity. Proposal files are never reversals.

A uniquely actionable pending proposal and a rejection proved by two distinct
exact live names are normal non-blocking outcomes. A future applied rename proves
fulfilment through the rename-ledger version 2 `proposal_id` field. Historical
applied, merge-resolved, compensated, lost or ambiguous proposals require
disposition evidence. The two Greys proposal ids are
`rename-proposal:df3df0ad-d58b-478a-9660-cb7d7b87501d` and
`rename-proposal:c5927528-3d73-4ead-91d2-8ed0095bcac9`. The compensated UAP
proposal is `rename-proposal:78ef39a1-f81b-4d25-81aa-e0074c52243a`; its evidence
binds applying rename
`rename-ledger:sha256:a290bdafbf704874131df66e0a242808fb0cb1f77087d13f0ad3855baca85262`
and inverse rename
`rename-ledger:sha256:efb904c4cf523c27610051fe7f94bb399b2a3090e39c04683c31ba3d69b3898b`.

## Empty ledger

When no dispositions are required, an absent file means this exact canonical
empty document:

```yaml
schema: anomalica/curation-replay-dispositions/1
entries: []
```

The exact bytes use LF and one final newline. Their SHA-256 is
`sha256:bbef14384bcdc68220da8d53888bb79e29a9c54b5a05d3c12ab490470b3efb50`.
Reports use that value, never null, a named sentinel or the hash of zero bytes. If
any disposition is required, absence fails validation. A present empty ledger is
valid only with those exact bytes. Zero-byte, null, partial, CRLF, commented or
otherwise non-canonical documents are invalid. Every present ledger must validate
and equal its canonical serialisation before its exact bytes are hashed.
