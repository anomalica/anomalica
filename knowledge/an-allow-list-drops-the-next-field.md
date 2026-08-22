# An allow-list drops the next field silently

Internal method knowledge (a reference note). A function that copies data across
a boundary by NAMING the fields it knows about will drop every field added after
it was written, and will do so without an error, a warning, or a wrong number
anywhere. The data is emitted correctly upstream and absent downstream, and the
absence is then explained by a plausible story that nobody re-checks.

Twice in six hours, at one boundary, on 2026-07-31.

## The boundary

`parse_digest_yaml` turns a digest on disk into the dict the importer folds into
the graph. It built its output by listing keys:

```python
frontmatter = {
    "record_id": record.get("id"),
    "record_title": record.get("title"),
    "record_producer": record.get("producer"),
    "record_date": record.get("date"),
    "record_reference": record.get("reference"),
    ...
}
```

Correct on the day it was written. Every field added to the digest afterwards
stopped at that line.

## What was lost, and the story that hid it

**The provenance chain (ADR 0044).** The digester emitted `provenance_chain` on
87% of claims; the graph held `origin_kind` NULL on all 19,006. The claims table
had the columns, the model had the field, the emitter wrote it - and the parser
did not read it back.

The absence had an explanation: "the graph was built from pre-0044 digests, so a
re-digest will populate it." Plausible, widely repeated (I repeated it myself),
and wrong. The corpus was re-digested in full and the count stayed at zero,
because no amount of re-emitting a field helps when nothing reads it. ADR 0039
keys claim INDEPENDENCE on that field, so for months two podcasts relaying one
anonymous email were indistinguishable from two witnesses.

**`record.review.state`.** Stamped human / machine / none on every digest, read
by nothing, so 53 records reached the graph unmarked. This one had a deadline
attached: 110 unreviewed records were approved for digestion precisely because
they would arrive MARKED and a consumer could filter. The justification was sound
and the mechanism worked in the digest and nowhere else.

Auditing the same boundary properly then found **five** dropped record fields
(review, publisher, medium, processing_version, duration) plus `content_hash` -
which was present in every digest and being re-derived by a filesystem scan of
the ingests directory on every single import. Not just wasteful: a scan can
resolve to a different record than the hash names, which is the supersession case
that cost a separate investigation the day before.

## Why it evades every normal check

- **No error.** A missing key is a `None`, and `None` is a legal value.
- **No wrong number.** Nothing is miscounted; a column is simply empty, and an
  empty column looks like a producer that has not started emitting yet.
- **A ready explanation.** "That data predates the feature" fits perfectly and is
  cheap to believe. It survived a full re-digest that disproved it.
- **Tests pass.** Both sides are individually correct. The emitter emits, the
  schema has the column. Only an end-to-end comparison of the two populations
  finds it, and nobody runs that until something forces it.

## The rule

1. **Pass the structure through; let the consumer choose.** The fix was to stop
   enumerating and hand the whole record block over. A field added upstream now
   reaches consumers with no change at the boundary.
2. **Parsing is not the place for policy.** Offering everything is not the same
   as storing everything - `ai_usage` is offered by the parser and deliberately
   never stored, because the graph feeds the public site and per-record billing
   data must not be one join from a renderer. That judgement belongs to the
   consumer, which knows where its data goes; the parser does not.
3. **Compare populations, not implementations.** "Does the producer emit it" and
   "does the schema have a column" are both yes here. The only question that
   found it was: count it on both sides. Do that for every field the pipeline is
   supposed to carry, once, rather than trusting that a path exists.
4. **Distrust an explanation that predicts nothing.** "The corpus predates the
   field" was testable - re-digest and re-count - and nobody tested it until the
   re-digest happened for other reasons and the number did not move.

## The note did not prevent the recurrence (2026-08-21)

Three weeks later the same shape arrived seven more times in one afternoon, twice
at *this* boundary - the parser's field list dropping a newly specified
`curation` block, and the emitter's field list destroying `pre_digest`,
`run_kind` and `record.speakers` on any round trip. This note existed, named the
function, and was not enough.

The reason it was not enough is that "allow-list" made it read as a
data-copying bug, so nobody recognised the same fault wearing other clothes:

- a corpus sweep keyed on a lower-case `unnamed` prefix, blind to every
  capitalised description
- its replacement keyed on name *shape*, which flagged a real surname and still
  missed the case it was written for
- an extraction prompt teaching a category with one worked example, so the model
  matched the example instead of applying the category
- a guard placed on node *minting* while references and speakers resolved through
  an unguarded matcher
- a database column that was only ever SET and never cleared, leaving a record
  pointing at a node that had just been retired

**The unifying cause is not enumeration. It is that adding is easy to write and
removing has to be thought about**, so the removing half gets skipped and nothing
fails loudly when it does. Every one of these handled the case it was written for
and stayed silent on the case that arrived later. An allow-list is just the most
recognisable costume.

So the question to ask of any write path, guard or sweep is not "does it list
everything?" but **"what happens to the case this was not written for?"** - and
specifically, what removes, clears, or rejects, given that only the adding half
tends to get built.

Related: [absence is not a verdict](absence-is-not-a-verdict.md) - the empty
column read as a state; [the diligent version is the wrong
one](the-diligent-version-is-the-wrong-one.md) - the same preference for an
authoritative structure over an enumerated one; [a condition that cannot
fire](a-condition-that-cannot-fire.md) - the check that would have caught it
being the one that structurally could not.
