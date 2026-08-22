# Absence is not a verdict

**A thing that was never observed must never be counted as a thing that
was observed and found acceptable.** Whenever a schema or a metric cannot
distinguish "not looked at" from "looked at and fine", it will silently
report the second, and it will do so in the flattering direction.

This is the most reliably recurring failure in the project. It was worth
writing down after five instances in one week, across five components,
each found separately; the sections below have since roughly doubled that
and none of them was found by looking for it. Recognise it by shape rather
than rediscovering it per instance - and expect the next one to arrive
looking like a fact about the world rather than a fact about a query.

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

## It also applies to instrumentation, not just schemas

The same conflation appears one level up, where the apparatus reports a
measurement it never actually took.

Re-running a model arm to estimate run-to-run variance returns
**byte-identical** output, because the checkpoint cache serves the prior
result from disk. The measurement reads 0.0 variance *by construction* -
absence of a fresh call conflated with an observation of stability. It
needs the call cache disabled, which makes it a full-cost run rather than
a cheap one.

The consequence is worse than a single wrong number: a variance estimate
of zero makes **every** subsequent delta look significant. A silent
non-measurement here does not mislead about itself, it miscalibrates
everything compared against it afterwards.

The general form: before trusting a number, check that the apparatus
performed the observation rather than returning something that merely
looks like one. Caches, defaults, and short-circuits all produce
confident-looking output without doing the work.

## The sharpest case: a measurement nobody took

Every instance above is a query, schema, or instrument that *ran* and
could not see something. There is a worse form: **an instrument that was
specified, believed to exist, and never built.**

The AI-operation ledger ([0037](../decisions/0037-ai-operation-ledger.md))
has no table in either database. It is the artefact specified to answer
"what ran, on what transport, spending what" - and when two unexplained
runs surfaced (19 August, 9 Opus digests, 8.6M tokens; 21 August, 31
pages, 6.3M), the instrument that would have attributed them was absent.
**An absent ledger reads as an absence of spend.**

This is harder to catch than a blind query, because a query at least
returns something a sceptic can interrogate. Here there is nothing to
interrogate and no error - only a quiet, confident nil, backed by a
decision record that says the mechanism exists. Ask not only "would this
query have seen it?" but "was this ever measured at all?", and treat a
specified-but-unbuilt instrument as a standing source of false negatives
until it is written.

## Two more query-shaped instances

- **A prefix match cannot see a corruption in the middle.** A `LIKE`
  pattern anchored at the start of a name reported nil
  description-shaped person nodes, missing "Unidentified Aerial
  Phenomena (UAP) Gerb" - page-worthy, 36 claims. The absence was a fact
  about the pattern, reported as a fact about the corpus.
- **A count over a table that failed to load returns 0, not an error.**
  A coverage count read a virtual table it could not open and reported
  zero coverage rather than an unavailable source.

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
