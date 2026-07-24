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
