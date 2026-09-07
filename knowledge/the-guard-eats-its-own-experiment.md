# The guard eats its own experiment

Before running a measurement, ask what the machinery you have just built does
to it. Twice in one afternoon (2026-09-07) a correct implementation was wrong
for the case in front of it, and only the second one was caught before it cost
anything.

## The two cases

**A guard built for the failure seen, not the variable identified.** The
hypothesis was that kimi-k3 fails on the size of the accumulated node
directory. Every failure to date had happened in Pass B, where the directory
appears as a schema enum, so the guard measured the largest enum in the schema.
Pass A carries the same directory as PROSE in its prompt, so a book failed at
chunk 18 of 27 with 473 nodes and never reached the guard at all. The
hypothesis said "directory size"; the code said "Pass B schema enum"; the gap
between them was invisible because every failure so far happened to be in
Pass B.

**A guard that would have eaten the experiment that sets it.** That same guard
refuses an opencode run above the threshold and reroutes it to another model.
The two experiments queued to MEASURE the threshold were both deliberately
above it - 75 nodes and 455. They would have rerouted, spent allowance on the
wrong model, produced digests that answered nothing, and returned "the tests
could not run" as though that were a result. Caught with minutes to spare and
fixed by lifting the limit for those two runs, which is what the environment
override existed for.

## What to do

- After building a guard, state the hypothesis and the implementation as two
  separate sentences and compare them. "Fails on directory size" and "refuses a
  large schema enum" are not the same sentence, and the difference is where the
  next failure lives.
- Before running any measurement, ask what you have recently changed that sits
  in its path. A guard, a cache, a default, a retry - each of them can turn an
  experiment into a measurement of itself. The call cache does this too: three
  repeat runs to measure run-to-run variance return byte-identical results and
  a variance of exactly zero, because an identical call replays a stored
  response. That one is caught by `DIGESTER_CALL_CACHE=off`.
- Make a threshold an environment override rather than a constant. The reason is
  not tuning; it is that the experiment which sets it must be able to run past
  it.

## Related

- [cli-transport-argv-ceiling](cli-transport-argv-ceiling.md) - the same
  underlying shape on a different transport: what scales is the constraint, not
  the document.
- [a-condition-that-cannot-fire](a-condition-that-cannot-fire.md)
