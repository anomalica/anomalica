# The instrument measured itself

**A query can report a property of the query rather than of the data, and the
answer comes back looking perfectly ordinary.** No error, no empty result, no
warning - a plausible number, in the shape you expected, that describes your
own tooling.

This appeared four times on 2026-08-15 alone, in three different sessions, none
of them recognised at the time by the session that made it. Worth knowing by
shape, because every instance was found by someone else re-measuring rather
than by the author noticing.

| The measurement | Reported | Actually |
|---|---|---|
| Sizing a storage move by `content_hash` | 1 object, 5MB | 19 objects, 104MB - ebooks hash their body, so the original is found through `source_hash` |
| Counting claims carrying a `relay` | 0 of 27,966 | 2,507 - the field is nested under `provenance_chain`, and the flat lookup returned nothing for every claim |
| Coverage of `source_hash` by type | 13 ebooks, 27 web | 17 of 17 and 34 of 34 - the command ended `head -40`, and 13 + 27 = 40 |
| Recent output check | 0 files in the last hour | 3 - `find -newermt '-1 hour'` matched nothing where `-mmin -60` matched three |

## Detectors that work without knowing the right answer

- **Parts that sum to a round number you chose.** If a breakdown adds up to your
  own `head -N`, `LIMIT`, page size or `[:N]` slice, you are looking at the cap,
  not at the data. 13 + 27 = 40 was sitting in the output.
- **State the denominator.** "17 of 17" is checkable by the reader; "17" is not.
  A bare count carries no evidence that the query reached everything.
- **A clean zero deserves more suspicion than a messy number.** Zero is what a
  broken query returns, what a wrong nesting level returns, and what a typo in a
  field name returns. It is rarely what a live corpus contains.
- **Confirm the shape before concluding a field is unused.** Print one whole
  record and look at it. Two of the four above were a lookup at the wrong level
  of a nested structure, which cannot fail loudly - the key is simply absent.
- **If a count seems low, re-measure a different way before reporting it.** Not
  the same way more carefully; a different way. Agreement between two unrelated
  methods is the cheapest real evidence available.
- **A check with two possible outputs that prints neither has not run.** Piping a
  test through another command and reading the wrong exit status gives exactly
  that: `grep -q ... | sed ...` reports `sed`, which succeeds whatever `grep`
  found, so an if/else prints nothing and the answer looks like "no". Silence from
  something built to answer either way is the tell.

## Why it is worth a note

Each of these looked like a finding. Three of the four were about to be acted on:
a storage plan sized two orders of magnitude wrong, a conclusion that a required
provenance field had never been populated, and a partial-coverage case that did
not exist being coded around. The failure is not carelessness - the queries were
reasonable and the numbers were plausible. It is that nothing in the result
distinguishes a measurement of the corpus from a measurement of the harness.

Same family as [absence is not a verdict](absence-is-not-a-verdict.md), which is
this failure at the schema level rather than the query level, and
[a partial copy answers 200](a-partial-copy-answers-200.md), which is it at the
transport level.
