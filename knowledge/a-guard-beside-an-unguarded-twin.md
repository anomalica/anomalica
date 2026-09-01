# A guard beside an unguarded twin

Internal method knowledge (a reference note). When a codebase compares things,
it usually grows **more than one comparison path** - a name path and an alias
path, a whole-string path and a per-component path, a fast path and a careful
one. The guards that make the comparison correct get added to whichever path
the author was looking at. The others keep working, keep returning plausible
numbers, and are wrong across the corpus.

Recorded because it happened three times in one week in the same file, and each
time it was diagnosed as a fresh incident rather than as the class.

## The three

All three were ONE line. All three sat within a few lines of a correct,
guarded version doing the same job.

1. **The alias comparison.** `match_node` compared an incoming name against a
   node's aliases with raw `levenshtein_ratio`, while comparing it against the
   node's *name* two lines below with the structure-aware
   `fuzzy_name_similarity`. Event names carry a mandated tail - "... Unidentified
   Flying Object (UFO) incident" is 35 of 53 characters - so any two events
   scored above threshold on the boilerplate alone.

2. **The component comparison.** `_component_similarity` compared one
   comma-component of a structured place name with no distinctive-token guard,
   while the whole-name path applied one. " Air Force Base" is most of the
   string, so Walker scored 0.82 against Kirtland. The structured branch takes
   the *minimum* component score, so that single unguarded comparison decided
   the merge.

3. **The fix for the first one.** `collapse_acronym_expansions`, added to
   repair (1), required exactly one acronym letter per expansion word. "Infrared
   (IR)" draws two letters from one word and "Deoxyribonucleic Acid (DNA)" three
   from two, so it silently refused them and cost four true matches. A guard can
   be too strict in exactly the same silence as one that is missing.

## Why it is invisible

An unguarded comparison is not broken. It is *right on the cases anyone
happens to try*, because the pairs a person reaches for to sanity-check a
matcher are pairs they already believe are similar. It only fails on the
corpus, at a rate nobody measures, in a direction nobody looks.

Both of these ran for months:

- 118 aliases naming other events accumulated on one node.
- Fifteen Californian places were absorbed into a **Bolivian** node and fifteen
  English ones, RAF Woodbridge among them, into **London** - misattributing the
  claims, not merely the names. "LeftBrainRight, LLC ... Santa Monica,
  California" was a claim about Bolivia.

## The amplifier: a system that records its own matches

Neither would have reached that size without a write-back loop. The importer
records every fuzzy match as a **new alias**, and aliases are themselves match
targets. So one wrong match widens the catchment for the next. Nobody made 118
errors; one correct curator merge deposited one boilerplate-shaped alias, and an
unguarded comparison compounded it.

The corollary is operational and cost us the ordering of a whole day's work:
**a merge deposits every victim name as an alias on the survivor**, so merging
duplicates *mints* fresh boilerplate-shaped aliases. Fixing the comparison is
not tidy-up that precedes a merge - it is what makes the merge safe. Measured
on the same post-merge graph with five unrelated event names: the previous
comparison sent four of five to the wrong node, the fixed one none.

## What to do

- When you find a missing guard, **do not fix the instance**. Enumerate every
  comparison path in the module and check each one.
- Write the test as the *class*: iterate the paths, assert each rejects a
  hard-token conflict and a substituted distinctive word, and each still accepts
  an identical pair. Adding a fourth path then forces a decision.
- Verify the test fails when a guard is removed. A guard test that passes
  vacuously is the same failure one level up.
- Do not tune a threshold to compensate for an unguarded comparison. The
  threshold is not what is wrong, and moving it trades one direction for the
  other; fixing the mechanism improves both at once. See
  [[the-first-spelling-wins]] for why greedy first-wins resolution makes the
  blast radius large, and [[absence-is-not-a-verdict]] for the habit of checking
  the direction that would disconfirm you.

## It generalises past comparisons: one side of a seam

Three more instances the same day, and only the first is about comparing things.
The common shape is a rule applied on one side of a boundary and not the other,
with the correct behaviour sitting a few lines or one directory away.

- **Two comparison paths.** The alias comparison unguarded beside the guarded
  name comparison; `_component_similarity` unguarded beside the guarded
  whole-name path.
- **Two ends of a normalisation.** Country forms were normalised on INCOMING
  place names but not on the ones already stored, so the fix that was meant to
  stop duplicates would have minted them - `UK, London` failing to find
  `United Kingdom, London`. The fix is only complete when both sides agree.
- **Two copies of an output.** `prune_retired_briefs` ran during synthesis on the
  SOURCE brief directory and never on the PUBLISHED one, so every merge and
  rename tidied one side and left the other pointing at a node that had moved.
  23 published briefs were unbuildable - 7 for retired nodes, 16 at a slug their
  node no longer had, which is one entity getting two pages.

**The question to ask of any rule:** where else does this data exist, and does
the rule reach there? Not "is the rule correct" - it usually is - but "is it
applied everywhere the thing it protects can be found". A rule that runs on the
write path and not the read path, on the new rows and not the old ones, or on
the working copy and not the published one, is not half-safe. It is unsafe in
exactly the cases nobody is looking at, because the half that works is the half
someone tested.

**Why it stays hidden:** each of these was correct on the path its author was
looking at, so every test they wrote passed. The divergence only shows when
something moves at volume - all three surfaced on a day that moved more nodes
than the corpus normally sees in a month.
