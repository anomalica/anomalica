# Audit format

The adjudication sidecar is the human judgement input to the
model-comparison eval - one per record, recording what a reviewer thought
of each model's claims. Schema `anomalica/audit/2`. The workbench writes
it; the digester's eval consumes it. See
[decision 0045](../decisions/0045-adjudication-measures-quality-and-worth.md)
for the why, including why the schema is `/2` and not a redefined `/1`.

Like the other interchanges (record [0019](../decisions/0019-record-interchange-format.md),
digest [0027](../decisions/0027-digest-interchange-format.md), ledger
[0037](../decisions/0037-ai-operation-ledger.md)), it is versioned: a
breaking change bumps the integer.

## Shape

```yaml
schema: anomalica/audit/2
record: <content_hash>          # the record whose digests were compared
models: [<model_id>, ...]       # every model in the comparison - required
adjudicated_at: <iso8601>
adjudicator: <id>               # optional
clusters:
  - id: <cluster_id>
    best_of: <model_id>         # optional; or `tie`; absent = not adjudicated
    members:
      - model: <model_id>
        claim_id: <uuid>
        quality: good           # bad | okay | good; optional when irrelevant
        irrelevant: true        # optional, defaults false
```

## Fields

| Field | Description |
|-------|-------------|
| `schema` | `anomalica/audit/2`. |
| `record` | Content hash of the adjudicated record. The join key to the digests and to the ledger's `target`. |
| `models` | Every model in the comparison, whether or not it contributed a claim. **Required** - missed-fact rate is uncomputable without it (see below). |
| `adjudicated_at` | When the adjudication was recorded. |
| `adjudicator` | Who adjudicated. Optional; supports inter-rater agreement later. |
| `clusters[].id` | The cluster of equivalent claims across models. |
| `clusters[].best_of` | The model that expressed this cluster's claim best, or `tie`. **Absent means not adjudicated**, which is not the same as `tie`. |
| `members[].model` | Which model emitted this claim. |
| `members[].claim_id` | The claim's identifier in that model's digest. |
| `members[].quality` | `bad`, `okay`, or `good`. May be omitted when `irrelevant` is set. |
| `members[].irrelevant` | Worth, not correctness. Orthogonal to `quality`. |

## The four invariants

**Quality and relevance are orthogonal, and never collapse into one
scale.** `irrelevant` is not a fourth quality value. A claim can be
accurate, faithful, well-formed - `good` - and still not worth
extracting; a claim can be squarely on-topic and `bad`. Recording them on
one axis would make "how good is this model's extraction" and "how much
noise does it emit" inseparable, and they are separately actionable: the
first is a prompt-quality problem, the second a relevance-tuning problem.

**A skipped best-of leaves the denominator entirely.** `best_of` absent
means the reviewer did not adjudicate that cluster; it records no win, no
loss, and no tie. Head-to-head win rate is computed over *competed*
clusters only - those where `best_of` is present. `tie` is a distinct,
deliberate value meaning "adjudicated, no winner": it counts in the
competed denominator and awards no win. The distinction matters because
clusters group *equivalent* claims by construction, so genuine ties are
common rather than rare; without an explicit `tie` a reviewer facing two
equally good claims must either skip (losing the information that they
were equal) or pick arbitrarily (injecting noise into the win rate).

**A member appears only if it was adjudicated.** Absence of a member
means the reviewer did not reach that claim - never "looked at it and
found it fine". This is the same shape as an absent `best_of`, and it is
what makes the irrelevant rate computable: because `irrelevant` defaults
to false, an unmarked claim would otherwise be indistinguishable from an
ungraded one, and every ungraded claim would silently count as relevant.
The denominator for anything per-claim is therefore the members present,
not the claims in the digest.

**`quality` is optional only under `irrelevant`.** Grading the
craftsmanship of a claim that should not exist is wasted review. The
consequence has to be stated rather than assumed: the quality
distribution is computed over quality-marked claims, so it measures *the
quality of claims judged worth having*, not the quality of everything a
model emitted. Read together with the irrelevant rate it gives the full
picture; read alone it flatters a noisy model.

## Derived metrics

Nothing below is stored - each falls out of the sidecar.

| Metric | Derivation |
|--------|-----------|
| Per-model quality distribution | Counts of `bad` / `okay` / `good` per model, over quality-marked claims. |
| Irrelevant (noise) rate | `irrelevant` marks over that model's members. |
| Head-to-head best-of win rate | Wins over competed clusters (`best_of` present, `tie` included in the denominator). Skipped clusters excluded. |
| Missed-fact rate | Clusters in which a model has no member, over all clusters. Free from cluster membership - which is why `models` is required. |
| Cost per good claim | `good` counts joined to per-model token usage on record and model. Only valid at full adjudication coverage - see below. |

**No cost, price, or token fields appear in this sidecar.** Usage is
recorded where the work happened, not copied into the judgement of it.

The join source is the **digest's own `ai_usage` block**, which every
variant carries (model plus token counts). The AI-operation ledger
([0037](../decisions/0037-ai-operation-ledger.md)) is where this moves
once it exists - the database is unbuilt and the emit sites unwired as of
2026-07-23, so an eval that joins against the ledger today joins against
nothing.

Join on **tokens, not on a stored cost**. Per the canonical rule in
[format-specs.yaml](../reference/format-specs.yaml), AI usage is
provenance only - model, version, token counts - and any notional cost is
derived by the consumer from published list prices, never stored in an
artefact. A stored dollar figure bakes in a price that changes and turns
an interchange record into a billing one.

## Adjudication coverage

Adjudication is partial until it is finished, and a metric that mixes a
*complete* numerator with a *partial* denominator (or the reverse) degrades
smoothly and invisibly as coverage falls - it never announces itself, it
just reads wrong. Coverage per model is the members present in this
sidecar over the claims in that model's digest.

Two metrics have that asymmetry and must never print without their
coverage beside them:

- **Cost per good claim.** The run cost is complete the moment the model
  finishes; the good-claim count grows with every click of review. At 20
  claims graded out of 100 the metric overstates cost roughly fivefold,
  and it improves steadily as review proceeds, which reads exactly like a
  model getting cheaper. Restrict the headline figure to fully-adjudicated
  records, or scale explicitly and say so.
- **Irrelevant (noise) rate.** Same trap in the flattering direction: if
  the denominator is all claims rather than adjudicated members, every
  ungraded claim counts as relevant and the model looks quieter than it
  is. The member-presence invariant above is what fixes this - divide by
  members present.

Two are immune, and it is worth knowing why so the fence is not applied
where it is not needed. **Head-to-head win rate** is immune by
construction: skipped clusters leave the denominator, so it is always
computed over exactly what was adjudicated. **Missed-fact rate** is immune
entirely - it falls out of cluster membership and the recorded model set,
and needs no adjudication at all.

This is the same discipline as the quality-distribution caveat above, and
the same failure that the sparse-gold reading produced (an off-target rate
of 70% on sparse gold against 39% on dense). A number that flatters
silently must never print naked.

## The quality scale

The `okay`|`bad` boundary is the load-bearing one and needs holding, or
the scale drifts into a satisfaction rating and the metric stops meaning
anything.

- **`good`** - faithful and well-formed. Attribution, hedging, and quote
  support are all intact.
- **`okay`** - usable but flawed. Clumsy or loose wording, a weak quote
  selection, an over-tight paraphrase - while remaining supported by the
  source and not misrepresenting it.
- **`bad`** - unsupported by the source, or misrepresenting it. This is a
  faithfulness failure: a flattened attribution that changes provenance, a
  dropped hedge that changes certainty, a meaning-inverting elision
  ([digest-format.md](digest-format.md), elision rule 5). Reserve `bad`
  for these. Using it for "I did not like the wording" is what `okay` is
  for, and conflating the two destroys the signal.

`bad` is deliberately the human-owned half of fidelity. The mechanical
checks catch a quote that does not locate or runs out of order; a
reviewer catches the one that passes every mechanical check and still
misrepresents what the source said.
