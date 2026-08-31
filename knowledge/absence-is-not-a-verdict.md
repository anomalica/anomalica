# Absence is not a verdict

**A thing that was never observed must never be counted as a thing that
was observed and found acceptable.** Whenever a schema or a metric cannot
distinguish "not looked at" from "looked at and fine", it will silently
report the second, and it will do so in the flattering direction.

This is the most reliably recurring failure in the project. It was worth
writing down after five instances in one week, across five components,
each found separately; the sections below have since roughly doubled that
and none of them was found by looking for it. Recognise it by shape rather
than rediscovering it per instance - and expect the next one to arrive
looking like a fact about the world rather than a fact about a query.

| Where | Absence meant | Would have been read as |
|---|---|---|
| Audit sidecar, `irrelevant` | Claim never adjudicated | Claim judged relevant - so a noisy model reads as quiet |
| Audit sidecar, `best_of` | Reviewer skipped the cluster | A tie, or a loss for every model |
| Audit sidecar, member entries | Reviewer never reached the claim | Claim judged fine, inflating the quality distribution |
| Coreference metric | Ancestors name no referent, so the unit is untestable | Model resolved it correctly |
| Email `dkim_verified` | No signature present in this copy | Signature verification failed |

## Why it is always the flattering direction

Because the absent value is the *default*, and defaults are written by
someone thinking about the normal case. `false` for a problem flag reads
as "no problem". A missing row reads as "nothing to report". Nobody
chooses a default meaning "unknown", because at schema-design time the
unknown case feels like an edge case rather than the majority of the data
during a partial run.

The failure therefore compounds with incompleteness: the less work has
been done, the better the numbers look. That is the exact opposite of
what a progress metric should do, and it degrades smoothly, so there is
no threshold at which anyone notices.

## The fix, in the same shape every time

Make "not observed" representable, and exclude it rather than defaulting
it:

- **Presence semantics.** A record appears only if it was adjudicated;
  absence means not-reached. Denominators count what is present, never
  what could have been.
- **An explicit third value** where absence is already load-bearing.
  `tie` must exist separately from a skipped cluster, because otherwise a
  reviewer facing an honest tie can only skip - and skipping is data loss
  dressed as a judgement.
- **An untestable count**, reported alongside rather than folded in. A
  unit that cannot be tested is not a unit that passed; publish it as its
  own number so the coverage is visible.

## It also applies to instrumentation, not just schemas

The same conflation appears one level up, where the apparatus reports a
measurement it never actually took.

Re-running a model arm to estimate run-to-run variance returns
**byte-identical** output, because the checkpoint cache serves the prior
result from disk. The measurement reads 0.0 variance *by construction* -
absence of a fresh call conflated with an observation of stability. It
needs the call cache disabled, which makes it a full-cost run rather than
a cheap one.

The consequence is worse than a single wrong number: a variance estimate
of zero makes **every** subsequent delta look significant. A silent
non-measurement here does not mislead about itself, it miscalibrates
everything compared against it afterwards.

The general form: before trusting a number, check that the apparatus
performed the observation rather than returning something that merely
looks like one. Caches, defaults, and short-circuits all produce
confident-looking output without doing the work.

## The sharpest case: a measurement nobody took

Every instance above is a query, schema, or instrument that *ran* and
could not see something. There is a worse form: **an instrument that was
specified, believed to exist, and never built.**

The AI-operation ledger ([0037](../decisions/0037-ai-operation-ledger.md))
has no table in either database. It is the artefact specified to answer
"what ran, on what transport, spending what" - and when two unexplained
runs surfaced (19 August, 9 Opus digests, 8.6M tokens; 21 August, 31
pages, 6.3M), the instrument that would have attributed them was absent.
**An absent ledger reads as an absence of spend.**

This is harder to catch than a blind query, because a query at least
returns something a sceptic can interrogate. Here there is nothing to
interrogate and no error - only a quiet, confident nil, backed by a
decision record that says the mechanism exists. Ask not only "would this
query have seen it?" but "was this ever measured at all?", and treat a
specified-but-unbuilt instrument as a standing source of false negatives
until it is written.

## Two more query-shaped instances

- **A prefix match cannot see a corruption in the middle.** A `LIKE`
  pattern anchored at the start of a name reported nil
  description-shaped person nodes, missing "Unidentified Aerial
  Phenomena (UAP) Gerb" - page-worthy, 36 claims. The absence was a fact
  about the pattern, reported as a fact about the corpus.
- **A count over a table that failed to load returns 0, not an error.**
  A coverage count read a virtual table it could not open and reported
  zero coverage rather than an unavailable source.

## A field that answers uniformly says nothing, and looks like it says everything

The most expensive form of this fault: not a query that cannot see, but a column
that is populated, typed, well named, and constant.

**The instance (2026-08-28).** Designing a ranking to decide which claims survive a
per-page cap, the obvious signal is `claims.confidence`. It exists, it is a REAL
column, it is exactly what you would rank by. It is 1.0 on all 31,066 claims.
`claim_role` is the second thing you would reach for - official_explanation,
witness_testimony, investigation_finding, cover_up_evidence, a CHECK constraint
enumerating them - and it is null on all 31,066.

Ranking by either would have produced a ranking that ran, sorted, returned results,
and ordered by nothing at all. Every page would have been built from an arbitrary
subset while the code read as though it were selecting the strongest evidence.

**A schema tells you what CAN be recorded, never what IS.** A column's existence is
a claim about intent by whoever wrote the migration. Populated-ness is a separate
fact and it is not visible from the schema, the model class, the type annotation, or
the field name - all of which looked right here.

The check is one query per field and it takes seconds:

    SELECT COUNT(*), COUNT(field), COUNT(DISTINCT field) FROM table

Three numbers. Rows, non-null, distinct. **A distinct count of 1 means the field
cannot discriminate anything**, however meaningful its name. Run it on every field a
ranking, filter or gate depends on, before designing against it - not after, when
the design is what has to change.

What made it survive scrutiny here: the fields that ARE usable sit beside them in
the same table. `attestation` is 76% populated with four real values;
`origin_kind` is 98% populated. So a spot check of the table looks healthy, and the
two dead fields are invisible unless you ask about them specifically.

This is the same family as the rest of this note - a check that reads as done and is
not - but the false reassurance comes from the schema rather than from a query, a
comment or an instrument. It is the hardest to see because nothing is missing.

## The state you assert may be one you changed yourself

The sharpest instance of this whole family, because no instrument failed.

I measured the embedding backlog, found it empty, and told another component the
embeddings were finished. Both true at the time of measuring. In the hour between
measuring and asserting, I ran an identity pass that renamed 176 nodes - and a rule
I had written that same morning makes a rename DROP the node's vector, deliberately,
because a stale vector answers similarity queries under a name the node no longer
has. So 143 embeddings were outstanding again, invalidated by me, and I reported the
graph as settled while holding the cause of its unsettling.

That component's queue correctly showed the downstream job blocked. I told them it
was stale. They pushed back with the file's own timestamp, and they were right.

**A measurement is a statement about a moment, and the moment it describes is the
one you took it in - not the one you are speaking in.** The gap is invisible from
inside because your own writes do not feel like events that could invalidate your own
reading.

Practical form:

- **Re-measure before asserting, not before deciding.** The expensive check is the
  one you skip because you "just looked".
- **Suspect yourself first when a downstream component disagrees about state.** They
  are reading now; you are quoting then. Their disagreement is evidence about the
  interval, and the interval is usually yours.
- **Any pass that mutates identity invalidates measurements taken before it.** Merges,
  renames and retypes move node ids, names, hashes and vectors. Every figure computed
  before such a pass is describing a graph that no longer exists.

### The wider shape it belongs to

Four retractions passed across the fleet in one evening, and one of the retractions
was itself wrong. Every one came from reading a **rendering** as the thing:

- transient log lines read as standing queue state
- a timezone offset read as elapsed time (an 11:05Z instant against a 20:09 local
  clock, reported as nine hours stale, actually six minutes old)
- a blocker assumed to be leftover because it had been leftover once before
- a probe searching for `id="ref-1"` against minified HTML that emits `id=ref-1`,
  reporting 68 dangling citations where there were none
- a measurement quoted after the measurer had invalidated it

And the retraction that was wrong is the instructive one: a corrected artefact and an
artefact that was never broken **look identical afterwards**. The only way to tell is
to re-run the old predicate against current data - reproducing the fault, not
inspecting the state. That is what settled it: the old code path indexed 105 hashes
including all five disputed ones; the new path indexed 100 and none of them.

## A wrong comment is worse than no comment

The scheduler's digest index carried this, verbatim:

    # Canonical digests sit at the root of digests/; the variants/ subtree is
    # deliberately not scanned.

directly above `for y in records.rglob("*.yaml")`, which scans it. Every
model-comparison variant entered the index as an importable digest, and the queue
emitted five import jobs that could never succeed.

The bug is ordinary. What made it survive is the comment. **A confident, wrong
comment terminates the search**: anyone auditing the predicate reads it, agrees
that variants are excluded, and stops - so the comment does not merely fail to
help, it actively prevents the check that would have caught the code beneath it.
No comment at all would have sent the same reader to the loop.

This is the same family as the rest of this note. An absent row, an instrument
that was not running, a probe that found nothing, and a comment asserting the
opposite of the code all produce the same outcome: a reader concludes "checked,
fine" and moves on. The difference is only in what supplied the false
reassurance.

Practical form:

- **Treat a comment as a claim to verify, not as evidence.** Especially a comment
  that says what the code does NOT do - exclusions and negative guarantees are the
  ones that rot, because nothing fails when they stop being true.
- **When a comment and the code disagree, the comment is usually older than the
  bug.** It described the intent at the time; the implementation drifted, or never
  matched. Do not "fix the comment" without checking which side is wrong.
- **Write comments about WHY, not about what the code excludes.** A comment saying
  "variants are not scanned" is a fact that can rot silently. A guard function
  named `canonical_digests` cannot - if it stops excluding variants, its own tests
  fail.

## The related trap: a heuristic that overrides ground truth

The coreference case had a second failure underneath the first. The
applicability rule tried to *infer from prose* which spans were
context-dependent - when the human gold already said so directly, because
drawing a context edge **is** the reviewer declaring that span dependent.

A heuristic re-deriving something a human has already asserted is
strictly worse than the assertion, and it will disagree with it. If gold
data states a fact, read the fact; do not reconstruct it from the text
the gold was built against.

Related: [reading-a-model-comparison](reading-a-model-comparison.md) - a
metric identical across every arm is discriminating nothing, which is the
same class of silence.

## The test: could this instrument have returned the disconfirming answer?

Every instance in this note is the same fault, and after collecting a dozen of
them the useful output is not a longer list of shapes to watch for. It is one
question to ask of any check before trusting it:

**If the thing I am looking for were NOT true, could this instrument have told
me?**

Not "is this check careful". Not "did I write it correctly". Whether the
apparatus is *capable* of producing the answer that would disconfirm you. An
instrument that cannot is not a weak check, it is not a check - it is a machine
for confirming whatever you already believed, and it returns a number while doing
it.

Three found in one hour across three components, all passing, all trusted:

- **A probe stricter than the system it measures.** Comparing digest ref names to
  graph node names EXACTLY, when the importer deliberately resolves through
  aliases, acronym forms and fuzzy matching. It reported the system's correct
  behaviour as failure and produced "991 lost nodes", which was withdrawn one
  message before it would have been repeated forever.
- **A question that cannot fail.** Resolving a record through the hash THE PAGE
  cites, to ask whether the record exists. That hash is the stale one by
  definition, so the check answers "missing" for every page it examines. Ten
  pages read as blocked on an upstream component that had done nothing wrong.
- **An estimate with no input.** A pre-flight cost estimate that took the model
  name, multiplied two constants, and never opened the file. Nineteen pages, from
  a 9 KiB digest to a 2.4 MiB one, all quoted $0.05. It sat under every spend
  decision in the project and was structurally incapable of varying.

None of these was careless. Each was a reasonable thing to write, and each
returned a plausible number every time it ran.

### Applying it

- **Feed it a case you know should fail.** The estimate should have been run
  against two inputs of wildly different size before it was believed. Any check
  that has never once returned "no" has not been tested, only executed.
- **Ask what the check would say about a healthy system.** If the answer is the
  same as what it says now, the check is not measuring the system.
- **A recommended signal is an instrument too.** I gave another component a
  rebuild signal - live node, drift above zero, some claims remaining - and it
  passes for a page built from a 4-claim fragment of a 95-claim event. My own
  signal contradicted my own warning about that page in the same conversation.
  They caught it by adding a fourth state (evidence collapse: current claims below
  half the brief's) rather than by following the rule I gave them.
- **Absent measurement is not a pass.** When a page was missing from a manifest
  entirely, the right move was falling back to the slower direct check rather than
  letting the gap read as a clean bill. A silence is not a result.
