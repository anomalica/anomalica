# An index entry in a sentence

A node name has two jobs and they pull opposite ways. It must sort,
disambiguate and stay stable — so places are named `Country, Region, Specific`
and people `Last, First`. It also reaches the reader **inside a sentence**,
where those same names read as index entries:

> the facility at USA, Nevada, Area 51

> an unusual structure on USA, [N/A], Phobos

Found 2026-09-08 by screenshotting a live page and reading it. Both sentences
are built from correct claims and correct links; the canonical names, slugs and
graph are all exactly right. **The defect exists only in what the sentence
shows.**

## The shape

Whenever one string serves both identity and display, display loses silently:
identity is checked by machines constantly (slugs must match, links must
resolve) and display is checked by nobody until a person reads the page.

The fix is never to change the name. It is a rendering rule at the point of
use, so a future badly-named node cannot reach prose either. That is the
difference between fixing an instance and fixing the class.

## The convention is not reliably followed

Of 1,088 comma-separated place names, 12 are written the other way round
(`Area 51, Nevada, USA`). Taking the most specific segment there yields "USA" —
worse than the index form it replaces.

So a display rule must establish orientation before trimming anything, and
**leave the name untouched when it cannot**. Unchanged is the safe answer
because it is what already ships. Applied to the corpus: 45 of 47 corrected, 2
left for the graph to fix.

## The escaped bracket, which is the wider lesson

A node named `USA, [N/A], Mars` reaches prose as:

    [USA, \[N/A\], Mars](/places/na-mars-usa)

Every link regex in the assembler excluded `]` from the display text rather
than matching escapes, so **no pattern could span one**. That link was
invisible to display rewriting, to link resolution and to the retarget pass
alike — not fixed, not validated, and not reported by anything that counts
links.

Two consequences worth carrying:

1. A worst-case name is exactly the name most likely to break the tooling that
   would have caught it. The badly-formed cases hide from the instruments
   pointed at them.
2. A count of "how many are left" made with the same broken pattern reports
   zero remaining and is believed. This was caught only because the page still
   read wrong after it had been declared fixed.

Four regexes shared the blind spot because each was written separately. One
shared pattern now.

## Still open

The page TITLE is untouched: `/places/ohio-wright-patterson-air-force-base-usa`
still has "USA, Ohio, Wright-Patterson Air Force Base" as its heading. Titles
are also the site's card and list surface, where disambiguation earns its keep,
so trimming them is a joint decision rather than a rendering fix.

Related: `the-first-spelling-wins.md`,
`the-instrument-answers-in-the-expected-shape.md`.
