# You checked one side and named the other

Internal method knowledge (a reference note). Eleven wrong findings were produced
across two sessions in a single day (2026-08-01), by two careful people, on a
codebase they each knew well. Every one has the same shape, and it is not
carelessness:

> **A side was measured, and a DIFFERENT side's behaviour was described.**

The measurement was correct each time. The sentence attached to it was about
something that had not been looked at.

## The eleven

| Measured | Named | Actually true |
|---|---|---|
| digest claims, both sections | one database's claim count | 9.7% "loss" was 0% - the other section is in the other database |
| `claim_node_refs` only | "32.5% of nodes are orphans" | 16.7% - speaker links and the infrastructure DB attach the rest |
| graph node ids vs digest node ids | "682 referenced-then-orphaned" | 18 - different id spaces after dedup and fresh-uuid minting |
| the write path stores nothing on absence | "the read rule is pinned by a test" | only the write side was; SQL and Python then disagreed about absence |
| the emitter writes `provenance_chain` | "the graph predates ADR 0044" | the parser never read it back; a full re-digest changed nothing |
| node names appearing 27 times | "entity dedup has failed corpus-wide" | one live node, 26 orphaned declarations - dedup worked |
| a key that did not exist returned empty | "a book digested to zero claims" | wrong key name (`claims` vs `domain_claims`) |
| ditto | "1,853 claims are uncitable" | wrong key name (`location_in_record` vs `location`) |
| a tool's output count | "it silently drops 2,064 claims" | it drops two; the rest was a `--sample` default the reader had set |
| 306 pages pass the floor | "306 pass two conditions" | 90 of them were never tested on the second |
| the thin fraction is flat over 40x corpus growth | "therefore structural" | true, but the mechanism was unknown until orphans were separated out |

## Why it is not carelessness

Each conclusion was the *obvious* reading of a correct measurement. Nothing
errored. Most produced a plausible number in a plausible direction, and several
came with a ready explanation that fitted perfectly - "the corpus predates the
field", "the two-pass design leaves orphans" - which is what stopped anyone
looking further. A wrong number that looks wrong gets checked; these did not look
wrong.

The three that were caught before publication were caught the same way: **by
querying one more column, on the side that had not been examined.** Not by
thinking harder, not by re-reading the code. The CIA case is the clearest - 27
nodes of one name is a dedup catastrophe or a node directory working correctly,
and the two are indistinguishable until you ask how many claims point at each.

## The rule

1. **Name only the side you measured.** If the sentence is about imports, measure
   imports. A statement about the graph, derived from the digests, is a
   hypothesis.
2. **Compare POPULATIONS, not implementations.** "Does the producer emit it" and
   "does the schema have a column" were both yes while the field was being
   dropped between them. Count it on both sides; the only reliable question is
   whether the two numbers match.
3. **State the denominator or it is not a number.** Thin nodes are 37.4% of all
   nodes and 55.5% of *referenced* nodes - an 18-point swing from a choice nobody
   would think to mention, because the orphans in the denominator are mostly
   duplicate directory entries of entities that are richly represented.
4. **A correct number can carry a false implication, and measurement will not
   catch that.** "306 pages pass two conditions" was arithmetically right and
   untrue of 90 of them. Only a reader who has not made your assumption catches
   this class - which is the argument for the work passing through someone else
   before it reaches a decision.
5. **Distrust the explanation that arrives with the number.** Every long-lived
   error here came with one. If it is testable, test it before repeating it; if
   it predicts nothing, it is not an explanation.

Related: [absence is not a verdict](absence-is-not-a-verdict.md),
[an allow-list drops the next field](an-allow-list-drops-the-next-field.md),
[measuring tells you what is, not what survives](measuring-tells-you-what-is-not-what-survives.md).
