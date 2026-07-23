# Measuring tells you what IS, not what survives

Measure the artefacts before specifying against them - that rule is
elsewhere and it holds. This note is the half that rule does not cover.

**The data tells you what exists. The decision records tell you what is
being retired. A measurement cannot distinguish a gap worth filling from
a gap that closes itself when a superseded path is switched off.**

## The instance

93 of 146 articles carried no audit binding. Measured correctly: node
mode, the majority of the corpus, had nothing tying an article to what it
was built from. The obvious remedy was measured just as correctly - the
`claim_hash` column already existed in `knowledge.db`, the assembler's
query simply did not select it. One column, and the largest hole in the
corpus closes.

That remedy was forbidden by a decision already accepted. [0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)
retires the direct-graph-read path entirely: the assembler is to be
"given the brief and nothing else - it does not read the graph", and the
brief's input hash *is* 0010's knowledge-graph-data audit hash, "not a
parallel scheme". A database-direct binding for node mode would have been
precisely that parallel scheme, built on a path scheduled for deletion.
The 93 close on their own, by re-assembly from briefs or by the
synthesiser judging those pages should not exist.

Nothing in the corpus said so. Every article, every column, every count
was real. The artefacts cannot report their own obsolescence.

## Why it is hard to catch

The failure looks exactly like diligence. Someone measured rather than
assumed, found a real gap, proposed a proportionate fix, and was wrong -
and each step of that is the behaviour you want. There is no sloppiness
to notice. The tell is not in the work's quality but in its target: a
remedy aimed at a path that a decision record has already superseded.

It also survives review by people who are being careful, because the
measurement is checkable and the ADR is not in front of them. Confirming
the number confirms nothing about whether the number matters.

## The check

Before specifying a fix for a measured gap, ask what decision governs the
path the gap is on, and whether that path is the one the project is
keeping. Two questions, both cheap:

- Is there an ADR that supersedes this path, or names it interim?
- Does the gap close by itself when the superseding path lands?

If the answer to either is yes, the work is throwaway no matter how real
the gap is. Record the gap and its expiry rather than filling it.

Related: [which-layer-is-authoritative](which-layer-is-authoritative.md) -
emitted output is truth about what a system *does*; it is silent about
what the system is *becoming*.
