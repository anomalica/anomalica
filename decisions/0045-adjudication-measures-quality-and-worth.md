# 0045. Adjudication measures claim quality and worth, not truth

Date: 2026-07-23
Status: accepted

## Context

The model-comparison eval asks which model digests a record best. Human
adjudication supplies the judgement, recorded in a per-record sidecar.
Under `anomalica/audit/1` that sidecar recorded **truth verdicts**:
`real` / `hallucinated` / `not_asserted` per cluster, and `correct` /
`flattened` / `misattributed` / `overhedged` per member.

That allocation of human attention no longer fits what the machine can
do for itself. Fabrication is now caught deterministically:

- The elision rules in [digest-format.md](../architecture/digest-format.md)
  make a quote that does not locate against the source a *broken* quote,
  and one whose fragments run out of source order a reordered quote. Both
  are mechanical fidelity failures, found without a human.
- Coreference-mechanical checks catch the attribution failures that
  `flattened` and `misattributed` were recording by hand.

So the clicks spent asking a reviewer "is this real?" largely duplicate
work the pipeline already does. Human judgement is the scarce input to
this eval, and it was being spent on the half a machine can do.

What a machine cannot do is the residual that digest-format.md rule 5
already assigns to humans explicitly: an elision that drops a negation,
condition, or attributive qualifier can invert the sense of the retained
fragments while every fragment stays verbatim, located, and ordered.
Semantic misrepresentation is not mechanically checkable. Neither is
**worth** - whether a claim was worth extracting at all is a judgement
about relevance, not correctness, and no fidelity check has an opinion
about it.

There are zero `audit.json` files on disk. Clean slate: no migration, no
back-compatibility, no data to reinterpret.

## Decision

Adjudication records three things, and the schema bumps to
`anomalica/audit/2`. The field-level contract is
[architecture/audit-format.md](../architecture/audit-format.md).

1. **Per-claim quality**, three-point: `bad` / `okay` / `good`. `bad` is
   defined to mean unsupported by the source or misrepresenting it - a
   faithfulness failure, not dissatisfaction with the wording.
2. **A per-claim `irrelevant` mark**, orthogonal to quality. It records
   *worth*, not correctness: a claim can be accurate, well-formed, and
   still not worth extracting.
3. **Per-cluster best-of selection**, optional. Skipping a cluster
   records nothing - not a tie, not a loss.

### Why bump to `/2` rather than redefine `/1`

The case for reusing `/1` is real: no files exist, so no reader can be
misled by the reassignment, and this project prefers breaking changes to
deferred ones. It still loses, for three reasons.

A schema id is a claim about which semantics a payload carries. `/1`'s
truth-verdict semantics exist - in component code, in this repository's
history, and in any branch, fixture, or local run that predates the
change - even though no committed files do. Reusing the id makes the
string ambiguous across the project's own history, and the failure mode
is silent: a `/1` payload written by a stale checkout would be *read* as
quality semantics rather than loudly rejected.

Bumping is not a back-compatibility shim, which is the thing this phase
rejects. Nothing reads `/1`, nothing writes it, there is no migration
and no dual-write period. The old semantics are simply dead. The bump
costs one integer and buys an identifier that never lies.

It also matches the convention the project already exercises: `record`
and `digest` each carry both a `/1` and a `/2`, and
[ai-ledger-format.md](../architecture/ai-ledger-format.md) states the
rule plainly - a breaking change bumps the integer.

## Consequences

The workbench writes the sidecar; the digester's eval consumes it. Two
requirements follow from what the aggregation must derive, and both are
easy to miss:

- **The set of models under comparison must be recorded.** Missed-fact
  rate falls out of cluster membership for free - a model with no member
  in a cluster missed that fact - but only if "absent from this cluster"
  can be told apart from "not run at all". Without the model set the
  metric is uncomputable.
- **Skipped best-of clusters leave the head-to-head denominator.** Win
  rate is computed over *competed* clusters only. A skip that silently
  counted as a draw would penalise every model for a reviewer's absence.

Cost-per-good-claim is derived, not recorded. The audit sidecar carries
no cost, price, or token fields: usage is recorded where the work
happened, and the metric is a join from per-model good-claim counts to
per-model token usage. The join source today is the digest's own
`ai_usage` block; the AI-operation ledger
([0037](0037-ai-operation-ledger.md)) is where it moves once built, which
it is not as of 2026-07-23. The join is on tokens, never on a stored cost
- notional cost is derived by the consumer from list prices and stored in
no artefact.

Every derived metric that mixes a complete numerator with a partial
denominator must publish its adjudication coverage. Cost-per-good-claim
and the irrelevant rate both do, and both degrade smoothly and invisibly
as coverage falls rather than failing loudly; the head-to-head win rate
and missed-fact rate do not. The field contract fences this.

Adjudication no longer produces a truth signal. That is deliberate - the
mechanical checks own fabrication, and their coverage is now load-bearing
for the eval's validity. If a fabrication class is found that neither the
elision rules nor the coreference checks catch, it must be fixed there,
not by adding a verdict back to the human's list.
