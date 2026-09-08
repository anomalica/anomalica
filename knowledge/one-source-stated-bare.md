# One source stated bare

A claim rendered without attribution asserts that Anomalica vouches for it.
**Nothing in the pipeline currently decides whether we can.** The field that
looks like it makes that decision, `attribution_mode`, is not keyed to
corroboration, so a single unreliable source reaches the reader in our own
voice while better-supported material around it is carefully attributed.

Found 2026-09-08 by reading a page as a stranger and tracing each sentence back
to its source line, which is the only method that surfaces it: every individual
step is correct, and the defect exists only at the page.

## The instance

`/events/world-war-ii` opened:

> In March 1938, Germany annexed the Sudetenland from Czechoslovakia,
> effectively beginning World War II.

Source line, *The Fatima Secret*, `ch4:1903-2005`:

> In March of 1938 Germany annexed the Sudetenland from Czechoslovakia,
> effectively beginning World War II.

The extraction is exactly faithful. The sentence is false. The Sudetenland was
occupied 1–10 October 1938 following the Munich Agreement of 29–30 September;
March 1938 was the Anschluss of Austria, which is the page's *next* sentence.
The same paragraph dated the Battle of Stalingrad to 1942-12-08 — the date of a
papal consecration, welded to the battle by the source. Stalingrad began
1942-08-23.

## Why it is not an extraction bug

On the same page, claims 6–18 **from the same book** are all attributed:
"According to *The Fatima Secret*", "Michael Hesemann has said". Only the
historical claims are bare.

The split is exactly backwards, and it is not random. A writer treats
background facts as common knowledge safe to assert, and treats religious or
contested claims as needing a source. That instinct is correct in general and
inverted here, because a devotional book is *least* reliable on the history it
uses as scaffolding and most careful about the doctrine it exists to convey.

**A source is not uniformly reliable, and the parts a writer will state bare
are the parts it was never authoritative on.**

## The measurement

Across all 805 published briefs, `attribution_mode` against
`evidence.independent_sources`:

| mode | sources | claims |
|---|---|---|
| `bare_ok` | 1 | 20,605 |
| `unknown` | 1 | 18,349 |
| `bare_ok` | 2 | 90 |
| `bare_ok` | 3+ | 23 |

Two or more independent sources is 138 claims in the entire corpus — one
quarter of one percent. So `bare_ok` cannot be, and is not, a judgement about
corroboration. 757 of 805 briefs contain at least one claim marked safe to
state on one source's authority.

## The rule this implies

A claim with `independent_sources < 2` must not be rendered bare, whatever
`attribution_mode` says. Checkable at build time from the brief alone, no model
required. It would have caught both Fatima sentences.

It is a large change to how the corpus reads, and that is the point: this is a
single-source corpus and it currently reads as though it is not.

## The rule reproduced the failure it was written to stop

The first implementation was:

    if mode == "bare_ok" and sources < 2:
        mode = "unknown"          # attribute it

which permits a claim whose count is **absent**. A brief carrying no measurement
would sail through the rule written to stop us asserting what we cannot support
— absence read as a verdict, inside its own antidote, on the same afternoon it
was written.

It reads as correct because the comparison looks total: a number is either below
two or it is not. `None` is neither, and the branch quietly falls through to the
permissive side. The corrected form makes `bare_ok` earn itself rather than
survive the lack of a measurement:

    if mode == "bare_ok" and not (isinstance(sources, int) and sources >= 2):

**The transferable part is how it was found, not the bug.** It surfaced because
the missing-count case was written as a test rather than reasoned about. Every
guard has three inputs — the bad case, the good case, and the case where the
measurement is missing — and the third is the one that gets skipped, because
nothing in the code names it.

## A stale comment actively prevents work

The field this rule depends on was described in the assembler as
"forward-provisioned, neutral until evidence-scoring pins", which reads as *this
is a placeholder, do not build on it*. It was simply out of date. The
assimilator's own module says `evidence.score` is the neutral one and
`independent_sources` is real.

Had the comment been believed, the correct answer would have been "this rule
cannot be implemented, the data is not there" — confidently wrong, with a source
citation. A comment that has fallen out of date is not neutral; it is a
recommendation not to look.

## How to find the next one

Read the page, then read each sentence's source line beside it. Structural
checks cannot see this — every claim matches its quote, every citation
resolves, and the page passes every gate. Compare what the page ASSERTS with
what the corpus can actually SUPPORT, which is a different question from
whether the extraction was faithful.

Related: `surface-agreement-is-not-independence.md` (independence is expensive
and every cheap proxy flatters), `absence-is-not-a-verdict.md`.
