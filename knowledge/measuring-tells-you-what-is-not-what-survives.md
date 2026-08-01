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

## The mirror: a decision record cannot report its own non-implementation

The note above says artefacts cannot tell you what is being retired. The
inverse is just as costly: **an accepted decision record reads exactly
like a built system.** Nothing in its text distinguishes "this is how it
works" from "this is how it was agreed it would work, and nobody has
written it yet".

Three in one week, all reading as settled:

| Record | Status when measured |
|---|---|
| [0010](../decisions/0010-auditable-assembly.md) audit trail | Nothing computed - `hashlib` not imported in the assembler |
| [0043](../decisions/0043-canonical-provenance-block.md) provenance block | 0 of 154 records carry it; the key is occupied by unrelated metadata |
| [0040](../decisions/0040-pipeline-versioning-and-supersession.md) supersession | Partial - see below |

Specifying against one of these produces work that cannot be built. It
happened here: email header routing was specified into 0043's provenance
block, by the same person who wrote 0043, without checking whether
anything emitted it. A decision record you authored yourself is the one
you are least likely to re-verify, which is exactly backwards.

**Partial implementation is more dangerous than none.** 0040 measured as
2 records carrying `supersedes`/`superseded_by`, a `store/v1/` directory
present, and `pipeline_version` on 0 of 154. A spot-check finds the
directory and the stamped records and concludes the scheme is live; the
automatic path that would make it a *guarantee* does not exist, and the
two stamped records are hand-made. Absence is at least honest. A working
fragment implies a working whole.

The check is the same one line: **name the field and count it.** `grep -c`
over the artefacts settles in seconds what a record's prose cannot settle
at all.

## Two corollaries about who is holding the artefact

**When two components disagree about a file, trust the one NOT in the
processing path.** A component that parses a file before measuring it is
measuring its own output, not the artefact. A digester reported a book's
body at 88KB while the file held 622KB, and drafted a handover to the
ingester on that reading - the record was never damaged; the parser was.
The component with no stake and no transform in between is reading the
bytes.

**A flat threshold across media types is wrong by default.** The same
number means different things to a transcript and a book. A pre-digest
survival check flagged 129 records because every transcript sits near 30%
retention - word timestamps are about 65% of a `record/2` body and are
stripped correctly - and against a timestamp-stripped baseline the same
check flagged exactly one. Three separate instances of this appeared in a
single day, which makes it a pattern rather than a coincidence: before
setting a threshold, ask what the denominator is made of for each type it
will run against.

## A confidently recorded wrong cause is worse than no cause

Writing down an unmeasured cause does more damage than leaving the
question open, because the note inherits the authority of the document it
sits in and redirects the next investigator away from the answer.

A blocked-items file carried "do not re-add until the schema-in-argv fix
lands" for two days. The schema was the largest plausible culprit and was
never measured; the actual cause was the node directory in a different
argv element ([cli-transport-argv-ceiling](cli-transport-argv-ceiling.md)).
Anyone acting on that note would have shrunk the schema, watched the
failure repeat identically, and had no idea why - having already spent the
one obvious hypothesis.

Record the symptom and the measurement. Where a cause is a guess, write it
as a guess, or write nothing: "unknown, X and Y not yet ruled out" costs a
reader nothing and misleads no one.

**The failures that survive are the ones whose output looks right.** Every
error worth the name this week produced well-formed, internally consistent,
plausible output - a book parsed to 14% of itself, a phantom drift across
1,589 claims, a health check reporting "No findings" over zero records, a
date invented to fill a field. None would have been caught by reading the
code, because the code did what it said. They are found by comparing the
output against the thing it describes.

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
