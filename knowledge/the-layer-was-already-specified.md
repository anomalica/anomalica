# The layer was already specified

Internal method knowledge (a reference note). Before designing a new layer of
the data model, check whether it is already written down and simply unbuilt.
On this project the answer has repeatedly been yes, and the cost of not
checking is a second design that competes with the first.

**A specified-but-unbuilt concept is invisible in exactly the way that
matters.** It leaves no data, so every query returns nothing and the concept
reads as absent. It leaves no failures, so nothing draws attention to it. The
only trace is a paragraph in an architecture document and, sometimes, an empty
column in the database. Both are easy to miss while looking at the data, which
is where a designer naturally looks.

## The instances

**`claim_role`.** A column on `claims` with a `CHECK` constraint on four values
(`official_explanation`, `witness_testimony`, `investigation_finding`,
`cover_up_evidence`), documented in `architecture/node-types.md` as "the
narrative function the claim plays in the story an article tells", with its
intended consumer named: the assembler would structure articles by role. It has
never been populated. As of 2026-09-08, 0 of 38,863 claims carry one. The
document says plainly that it is designed and not implemented; nothing in the
running system says so.

**`Pattern`.** A fully specified node type - a recurring phenomenon across
cases, with a stated bar of three independent cases, and an explicit rule that
it is *curator-created, not extractor-emitted*. It is the cross-corpus theme
layer. It has never been built. Anyone asked to design "a level above claims
that captures themes" will design this again unless they read node-types.md
first.

**`matter`.** The counter-example, and the reason this note is not simply
"build the specified thing". `matter` WAS built, as a node type, and was
removed because it folded four ways - event, organisation, project, topic - and
neither models nor reviewers could place things in it. 134 legacy nodes survive
in the graph. So the record contains both unbuilt good ideas and built bad
ones, and the document distinguishes them if you read it.

## The rule this produces

When a new layer is proposed, do three greps before any design work:

1. The architecture documents, for the concept under any name.
2. The database schema, for a column or table that would hold it. An empty
   column with a constraint on it is a design someone finished and abandoned.
3. The decision records, for the same concept having been *removed*, and why.

Then state which of the three you found, because the answer changes the work
entirely: specified-and-unbuilt is implementation, specified-and-removed is a
decision to reverse with reasons, and genuinely absent is design.

## The related trap

A layer that is *partly* emergent reads as absent too. Extraction was believed
to have no representation of a narrative episode. It has one: on a 40,000-word
interview containing roughly 26 distinct narrated accounts, extraction found 17
of them and filed them as `event` nodes. What was missing was not the
recognition - it was a name for the relationship, and the unnamed accounts.
"The system does not do this" was false; "the system does this for the easy
half and cannot say so" was true, and the second sentence produces a much
smaller piece of work than the first.

See [absence-is-not-a-verdict](absence-is-not-a-verdict.md), of which this is a
special case: the absence of *data* was being read as the absence of a
*decision*.
