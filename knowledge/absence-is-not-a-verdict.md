# Absence is not a verdict

**A thing that was never observed must never be counted as a thing that
was observed and found acceptable.** Whenever a schema or a metric cannot
distinguish "not looked at" from "looked at and fine", it will silently
report the second, and it will do so in the flattering direction.

This has appeared five times in one week, in five different components,
each time discovered separately. It is worth recognising by shape rather
than rediscovering per instance.

| Where | Absence meant | Would have been read as |
|---|---|---|
| Audit sidecar, `irrelevant` | Claim never adjudicated | Claim judged relevant - so a noisy model reads as quiet |
| Audit sidecar, `best_of` | Reviewer skipped the cluster | A tie, or a loss for every model |
| Audit sidecar, member entries | Reviewer never reached the claim | Claim judged fine, inflating the quality distribution |
| Coreference metric | Ancestors name no referent, so the unit is untestable | Model resolved it correctly |
| Email `dkim_verified` | No signature present in this copy | Signature verification failed |

## Why it is always the flattering direction

Because the absent value is the *default*, and defaults are written by
someone thinking about the normal case. `false` for a problem flag reads
as "no problem". A missing row reads as "nothing to report". Nobody
chooses a default meaning "unknown", because at schema-design time the
unknown case feels like an edge case rather than the majority of the data
during a partial run.

The failure therefore compounds with incompleteness: the less work has
been done, the better the numbers look. That is the exact opposite of
what a progress metric should do, and it degrades smoothly, so there is
no threshold at which anyone notices.

## The fix, in the same shape every time

Make "not observed" representable, and exclude it rather than defaulting
it:

- **Presence semantics.** A record appears only if it was adjudicated;
  absence means not-reached. Denominators count what is present, never
  what could have been.
- **An explicit third value** where absence is already load-bearing.
  `tie` must exist separately from a skipped cluster, because otherwise a
  reviewer facing an honest tie can only skip - and skipping is data loss
  dressed as a judgement.
- **An untestable count**, reported alongside rather than folded in. A
  unit that cannot be tested is not a unit that passed; publish it as its
  own number so the coverage is visible.

## The related trap: a heuristic that overrides ground truth

The coreference case had a second failure underneath the first. The
applicability rule tried to *infer from prose* which spans were
context-dependent - when the human gold already said so directly, because
drawing a context edge **is** the reviewer declaring that span dependent.

A heuristic re-deriving something a human has already asserted is
strictly worse than the assertion, and it will disagree with it. If gold
data states a fact, read the fact; do not reconstruct it from the text
the gold was built against.

Related: [reading-a-model-comparison](reading-a-model-comparison.md) - a
metric identical across every arm is discriminating nothing, which is the
same class of silence.
