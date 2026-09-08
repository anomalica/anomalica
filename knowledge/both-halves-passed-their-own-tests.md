# Both halves passed their own tests

Internal method knowledge (a reference note). When one thing is decided, written
or displayed in two places, the bug lives in the disagreement between them - and
a test of either half cannot see it, because each half is correct about its own
shape and wrong about the other's.

**The missing property is AGREEMENT, not correctness.** Every instance below had
full test coverage on both sides throughout. Nothing was untested. What was
untested was that the two sides matched, and that is a different assertion from
either of the ones already written.

## Three instances in one evening, 2026-09-08

**The guard that reached the display but not the dispatch.** A model size ceiling
was consulted where the job list is BUILT and not where a job is DISPATCHED. The
schedule builder passed the job's size to the chooser and correctly held the
oversized work; the runner called the same chooser without the size and got a
model the ceiling forbids. So since the ceiling shipped, the card read "held" and
the dispatcher sent the job anyway - two thirty-minute timeouts on records
sixteen times over the limit, and an operator surface describing a system other
than the one running. Worse than no guard, because no guard is at least honest.
The fix was not to add the check a second time but to derive the size inside the
resolver, so no caller can omit it: *every caller is a place a parameter can be
forgotten, and it was forgotten in exactly the one that dispatches.*

**The writer and the parser that disagreed about a reference.** A claim's node
reference gained a role. The emitters were updated; the parse boundary still
flattened each reference to a bare name on the way to the importer. The
extractor would have emitted roles correctly, the database column would have
stayed null on all 83,798 edges, the scorer would have reported everything
unassessed, and the obvious reading would have been that the extractor was not
emitting. Five call sites needed the change and were found one at a time across
three separate bugs, the last of which crashed after 47 minutes of paid model
calls, at the write step, after everything had been spent.

**The regex that could not see the case it was written for.** Four link patterns
excluded `]` from the display text rather than matching escapes, so a link whose
label contained an escaped bracket was invisible to display rewriting, to link
resolution AND to the retarget pass. Not fixed, not validated, not reported by
anything - and the count of remaining instances was wrong for the same reason
the instances were missed.

## Why this class is hard to see

The two halves are usually written at different times, often by different
people, and each is *locally* correct. Reviewing either one finds nothing. The
tests are green because they assert what each half believes about itself. The
symptom appears somewhere else entirely - as a producer that seems not to
produce, a job that seems to be held, a fix that seems not to have worked - so
the investigation starts in the wrong component.

That misdirection is the real cost. Twice this evening the first diagnosis
blamed an upstream stage that was working correctly.

## What to do

- **When a shape changes, grep every read and write of it before fixing the
  first one.** Five sites, one search. This was written down after the third bug
  in the sequence above and then not done, and two more sites were found by
  someone else running the search.
- **Test the boundary end to end**: emit, parse, assert the value arrives. Not
  the writer against a fixture and the parser against a fixture.
- **Where two paths compute one decision, assert they agree** across a range of
  inputs, rather than asserting each is right.
- **Prefer a shape that cannot disagree.** Pass the whole block through and
  rename known keys on top, rather than enumerating fields - an enumerating
  parser drops the next field added upstream, silently. One boundary lost the
  provenance chain and the review state this way before nearly losing a third,
  with a comment predicting it thirty lines above the line that would have done
  it.

Related: [absence-is-not-a-verdict](absence-is-not-a-verdict.md) - a value
dropped at a boundary reads downstream as a value never produced, and the two are
indistinguishable without the end-to-end test.
