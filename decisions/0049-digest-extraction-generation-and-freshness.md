# 0049. Digest extraction generation and freshness

Date: 2026-09-13
Status: accepted

## Context

`anomalica/digest/1` identifies the digest wire format, not the fidelity of the
extraction that populated it. Prompt hashes, model provenance and the pre-digest
hash identify several important inputs but do not fingerprint every effective
setting, and none supplies an ordered statement that an older extraction should
be replaced. As a result, schema compatibility, reproducibility provenance and
corpus freshness can be mistaken for one another.

The digest fidelity programme also proposes narrative accounts and
claim-to-account links. Those fields would change canonical output before the
account extractor has been measured against its available ground truth.

## Decision

### Three independent identities

Every new digest keeps three independent identities:

| Identity | Meaning | Changes when |
|---|---|---|
| `schema` | Digest wire format understood by readers. | A breaking contract change. |
| `extraction_config` | SHA-256 fingerprint of the complete exact effective extraction configuration. | Any output-affecting configuration or implementation identity changes. |
| `extraction_generation` | Positive, manually maintained fidelity cohort. | Maintainers judge that extraction output has materially changed and the corpus warrants re-digestion. |

The configuration fingerprint is computed from a deterministic canonical JSON
representation and covers the resolved model and model version, ordered passes
and prompt hashes, preparation version, chunking, decoding, validation and
deterministic post-processing. Existing readable provenance remains in the
digest. A changed fingerprint does not by itself make a digest stale, and a
generation is never derived from the fingerprint, schema, Git or time.

### Manifest and freshness

The digests repository root contains `digest-generation.json`, schema
`anomalica/digest-generation/1`, with one positive integer
`current_generation`. The digester owns the manifest and updates it with its
manually maintained generation. Consumers read it from the same committed tree
as the corpus. JSON avoids collision with the recursive YAML digest discovery
rule.

A generation equal to the manifest is current; a lower generation is stale; an
absent, malformed or unexpectedly greater generation is unknown. Unknown remains
a separately reported health category, but neither stale nor unknown qualifies
for a current-only operation. A missing or invalid manifest likewise fails
closed.

Source-input freshness is a separate test against `pre_digest.sha256`. A digest
is fresh only when its schema is supported, its generation equals the manifest,
its exact configuration fingerprint is valid, and its bound pre-digest is the
current materialised input. Health output reports current, stale and unknown
with denominators and reasons for both generation and input freshness.

No generation or configuration fingerprint is back-stamped onto an old digest.
Neither can be reliably inferred from timestamps, model names, prompts,
pre-digest metadata or historical Git state. Re-digestion produces the first
trustworthy current stamp.

### Accounts remain gated

Accounts and claim-to-account links remain report-only evaluation output, not
canonical digest fields. They are scored against the existing Doty account
ground truth using precision, recall, boundary overlap and claim-binding
coverage. They enter the canonical contract only after those results are
reviewed and judged adequate. Activation requires an extraction-generation bump;
it requires a schema bump only if the final wire change is breaking.

## Consequences

- Legacy digests remain readable under their declared schema but are unknown and
  operationally not current when the new provenance fields are absent.
- Configuration experiments remain distinguishable without forcing a corpus
  re-digestion for every non-material adjustment.
- A deliberate generation bump creates an explicit backfill set without
  pretending that old artefacts carried provenance they did not record.
- A backfill set is a scheduling signal, not model-execution authorisation. This
  decision and a generation-1 manifest do not authorise full-corpus generation-1
  re-digestion; any batch requires separate explicit approval after its aggregate
  cost or plan impact is shown.
- Canonical downstream consumers remain account-blind until evaluation supports
  activating the fields.

## Related

- [Digest interchange format](../architecture/digest-format.md)
- [0027: Digest interchange format](0027-digest-interchange-format.md)
- [0039: Multi-model digestion and canonical reconciliation](0039-multi-model-digestion-canonical-reconciliation.md)
- [0040: Pipeline versioning and record supersession](0040-pipeline-versioning-and-supersession.md)
- [0042: The pre-digest stage, and highlights as evaluation-only](0042-pre-digest-stage-and-eval-only-highlights.md)
