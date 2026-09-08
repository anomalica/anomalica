# The fingerprint that differed from itself

An identity value - a fingerprint, a config hash, a cache key, anything whose
job is to say "these two things are the same" - has to be checked against
ITSELF before it is trusted to compare anything else. Compute it twice, in two
processes, and see whether it agrees. Nothing else in a system will tell you
when it does not: an unstable identity value looks exactly like a real
difference.

## What it hid

A `config` fingerprint was added on 2026-09-08 so two digests could be proved
to come from one configuration - prompts, schema and code hashed together. It
returned a different value in every process. The instrument built to establish
comparability was incomparable with itself, and it had been that way since the
hour it was written.

The cause was one level down and much worse than the fingerprint. Two of the
three enums in the claims schema were built as set comprehensions:

```python
VALID_CLAIM_TYPES = {t.value for t in ClaimType}      # a set has no order
VALID_ATTESTATION = {t.value for t in AttestationLevel}
VALID_ORIGIN_KINDS = sorted(k.value for k in OriginKind)   # someone saw it once
```

Python randomises string hashing per process, so the order of a set of strings
changes every time the program starts. That order went into the JSON schema the
model is constrained by. **Every extraction this project has ever made presented
the model with its claim-type and attestation options shuffled differently**, and
option order biases which option a model picks.

So an uncontrolled variable sat inside every run-to-run comparison on the
corpus, including the measured 3.9-point noise floor that decides which model
differences count as real. The fingerprint was a symptom; the schema was the
disease.

## How it surfaced, and it is the cheapest check there is

Two computations of one fingerprint, minutes apart, from identical code,
disagreed: `b3db3b1f` against `eb101f8b`. **Two numbers about one thing that
cannot both be true.** No test failed, no output looked wrong, and the digest,
the variant filename and the grade table all agreed with each other - because
they were all reading the same wrong value.

The same check caught a second fault the same evening: a 99.97% quote-failure
rate sitting beside a 0.98 quote-fidelity score on the same record.

## What to do about it

- **A set is not an order.** The moment an unordered collection reaches a model,
  a schema, a prompt, a hash or a file name, its arbitrary order becomes an
  interface. Use a tuple in the declaration order, or sort it.
- **Test identity values across a process boundary.** In-process checks cannot
  see hash randomisation - the seed is fixed at start-up. Run the computation
  under two `PYTHONHASHSEED` values and compare.
- **Look for two numbers about one thing.** Not as an occasional audit, but
  whenever a system reports a quantity twice by different routes. It is the only
  detector that works when every instrument agrees.

## Related

- [a-guard-beside-an-unguarded-twin](a-guard-beside-an-unguarded-twin.md) -
  `VALID_ORIGIN_KINDS` was already sorted. The same fault was found once and
  fixed in one of the three places it occurred, and the fix looked complete
  because the site someone looked at was correct.
- [reading-a-model-comparison](reading-a-model-comparison.md) - the noise floor
  this defect was inside.
- [both-halves-passed-their-own-tests](both-halves-passed-their-own-tests.md)
