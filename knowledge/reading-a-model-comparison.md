# Reading a model comparison

Notes on getting a model-choice decision out of an eval table without
over-reading it. Written 2026-07-25 off the first graded trio
(opus/sonnet/haiku against a 197-unit human gold), and aimed at the runs
that follow.

## Compare marginal yield, not totals

A model that emits more claims and scores higher recall has not
necessarily earned the difference. Divide the extra output by the extra
coverage it bought.

In the first trio, opus produced 201 more claims than sonnet and gained
3.1 recall points. Sonnet averaged about 9 claims per recall point;
opus's *marginal* claims cost roughly 65 each. Most of what the larger
model added covered nothing the gold was looking for - and every one of
those claims is a human review click. The average hides this completely;
only the margin shows it.

## Measure the instrument against a known intervention

The most useful number this eval produced was not about a model. Changing
the **prompt alone**, same model and same record, moved recall 12 points
(52.0 to 64.0). Model differences on the same instrument sit around 3.

That reframes the decision: model choice is a second-order effect next to a
factor the project controls directly. Effort spent picking between the top
models is dominated by effort spent on prompt work, and a comparison run
before the prompt is settled is measuring the wrong variable.

**But prompt sensitivity is not a variance bound.** A prompt change is a
deliberate intervention; run-to-run noise is a different quantity and stays
unmeasured until an arm is repeated. "Smaller than a demonstrated
intervention effect" and "inside the noise floor" are distinct claims, and
only the first is established. The honest statement is that a 3-point gap
is small relative to a known controllable factor - which is enough to stop
it deciding anything, without asserting a noise floor nobody has measured.

## Two variables at once: use the signature, not the aggregate

Changing two things in one run usually forfeits attribution. It need not,
if one variable produces a **mechanistic signature** the other cannot.

A run that enabled streaming *and* moved schema enforcement to prompt could
not attribute a drop in the attempt count to either. But a client-side
socket timeout at a fixed wall is a distinct failure class, separable in
the log from provider rejection, invalid output, and rate limiting. Asking
"did any call die on a timeout" rather than "did the count fall" recovers a
clean answer from a confounded run - and costs nothing, since the failure
is already in the log if it is recorded by cause rather than counted.

**Check the indirect path before claiming a signature is exclusive.**
Enforcement cannot produce a socket timeout directly - but it can shorten
generation, and a call that finishes sooner never reaches the wall. So
"zero timeouts" alone stays ambiguous: the wall removed, or the wall never
reached. Pairing the signature with duration settles it - zero timeouts
*at durations that previously timed out* is a fact only the first
explanation fits.

The general form: a signature is exclusive only after you have asked what
else could suppress it, not merely what else could cause it. Record
failures by cause; count them second.

## One record cannot settle a corpus-wide choice

A single graded record is evidence about that record. Source type
plausibly interacts with model - a rambling talk-show transcript, a dense
statute, and a scanned FOIA release pose different extraction problems,
and nothing says one model leads on all three. Grade at least one of each
before a default is ratified rather than adopted provisionally.

## A difference smaller than run variance is not a difference

Models are stochastic. A 3-point gap on one record, measured once, is
roughly six gold units - comfortably inside what a re-run could move.
Repeat the arm before reporting a small delta as a ranking; until then
the honest statement is that the two are not separated, which is a
different claim from a tie and a very different claim from a lead.

Where two models genuinely cannot be separated on the headline metric,
the decision falls to the tiebreakers - fidelity, review burden, cost -
and that is a legitimate way to decide. It is only illegitimate to
present it as the headline metric having chosen.

**Measure variance where the metric is not saturated.** A small, easy
record is the tempting place to bound run-to-run noise cheaply, but a
record already scoring 95-100% has almost no room to move, so the
estimate comes back compressed and is then applied to hard records where
the real spread lives. The cheap measurement is not a cheaper version of
the right one; it is a different measurement that understates. Bound
variance on a hard record or not at all.

And sequence it. A variance bound is rarely on the critical path: if the
open question is whether one model leads across *source types*, running
the arms on a transcript, a statute and a scanned release answers the
ordering question directly, and consistency across three types is
stronger evidence than a variance figure from one. Reach for the variance
run only if the ordering flips between types - that is when you need to
know whether a flip is noise.

## Characterise a failure at the strength the evidence supports

"20% of its quotes are hallucinated" and "20% of its quotes are
imprecisely transcribed" are different accusations, and for an
evidence-based project the difference is the whole point. Establish which
before either goes in the record.

But the evidentiary bar has to match the claim. A short verbatim run
inside a quote is weak evidence of faithful reconstruction: common
four-word sequences occur by chance, and a fabricated sentence can
contain one while asserting something the source never said. Anchor
length, token-level overlap, and whether the *assertion* survives are
three different tests. Where only the weak one has been run, say the
strong conclusion is unestablished rather than reaching for it - the
under-statement and the over-statement are both errors.

## A metric identical across all arms is discriminating nothing

Report that as a defect in the metric, not as agreement between models.
If a coreference score reads 8/8 for every arm because the applicability
rule selected 8 of 104 available units, the finding is "we barely tested
this", not "they all handle it". The distinction matters because the
first invites a fix and the second invites a citation.

Over-narrow applicability rules are the usual cause. A rule requiring a
span to contain a pronoun *and no proper noun of its own* discards the
richest cases - a span naming one person while a pronoun refers to
another is exactly where attribution goes wrong.

Related: [validating-embedding-spaces](validating-embedding-spaces.md) -
the same failure of a benchmark that cannot see the thing it is meant to
measure.
