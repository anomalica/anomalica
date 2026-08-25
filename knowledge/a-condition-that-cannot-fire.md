# A condition that cannot fire

Internal method knowledge (a reference note). Deferring an action until things
"settle" sets a trigger that never arrives, and the deferral is invisible: no
error, no alarm, just work sitting undone while everyone believes it is queued.
Cadences that fire are per-artefact or per-interval. "When it stops moving" is
not a condition, it is a hope about the future.

## The worked example (2026-07-31): the tranche that never stopped

The digester was producing books continuously. The ruling was that digests would
be committed "once the tranche stops moving" - sensible-sounding, and correct in
its concern, which was that committing mid-tranche freezes an arbitrary midpoint
of another workspace's output.

Books landed continuously for **8.5 hours**. The condition never became true, so
the week's entire output stayed untracked: 9 modified files and 86 untracked in
`digests/`, and separately a `curation` ledger whose last commit predated every
curation decision made that week while an hourly timer replayed it.

Nobody forgot. The trigger was simply unreachable, and an unreachable trigger
looks exactly like a pending one.

## Why it is worse than forgetting

A forgotten task is discovered by asking "what have I not done". A deferred one
answers that question wrongly: it IS accounted for, there IS a plan, the plan is
just conditioned on an event that will not occur. Every status check returns
"waiting for X" and everyone reads that as progress.

The same shape, from the same week:

| Deferred until | Why it never fired |
|---|---|
| "commit when the tranche stops" | books landed continuously for 8.5 hours |
| "import when the queue dispatches import jobs" | the queue generated none; the graph fell 22 records behind |
| "recompute the figures on a settled corpus" | the corpus grew for the whole week |

The third was correct - measuring a moving corpus twice is waste - but it needs
an explicit re-check date, or it becomes the first two.

## The rule

1. **Trigger on an artefact, not on an absence.** "Commit each book as it lands"
   fires 11 times; "commit when the books stop" fires never. Per-item cadences
   are also finer-grained than the thing they replace, so a partial tranche stops
   being a hazard.
2. **If it must be time-based, name the time.** A timer, a cron, a dated
   re-check. `systemctl list-timers` will tell you it is still armed; an
   intention will not.
3. **State what makes the condition true, and check it is reachable.** "When the
   tranche stops" required the digester to stop, which nobody had asked it to do.
   Writing the precondition down is usually enough to see that it is not coming.
4. **A safety property must not rest on someone else's quality setting.** Adjacent
   failure from the same week: an invented hex-fragment URL
   (`/projects/...-aaro-fca513ac`) never shipped ONLY because the assembler's
   working floor was 10 claims and the node had 5. That floor was chosen for
   article quality, not as a guard, and could be lowered by someone who has never
   heard of the slug bug. Depending on it is the same error as depending on a
   condition nobody has agreed to make true.

Related: [absence is not a verdict](absence-is-not-a-verdict.md) - the deferred
action is another absence read as a state; [the diligent version is the wrong
one](the-diligent-version-is-the-wrong-one.md).

## The mirror image: a guard that always passed

The note above is about a trigger that never fires. This is the same fault seen
from the other side - a protection that never failed, and was therefore invisible
until somebody removed it.

**The instance (2026-08-25).** The assimilator's graph ran in SQLite's default
`journal_mode=delete`, where a reader holds a lock that blocks every writer. That
cost real work: a 30,000-query analytical scan made the graph unwritable for its
whole duration, a merge pass died on its first statement despite a five-minute busy
timeout, and a five-minute busy timeout had already been added weeks earlier to
paper over the same thing. Switching to WAL fixed it - readers stopped blocking
writers, verified by running the failing case.

Within the hour, two `embed` processes ran at once and collided on a primary key.
Under the old mode that could not happen: the second writer blocked on the lock and
waited its turn. Nobody had ever written code to serialise those two writers,
because nobody had ever needed to - **the lock was doing two jobs and only one of
them was a problem.** Removing the first removed the second.

**The general form: any accidental mutual exclusion that has never failed is
invisible, and you only learn it was load-bearing by removing it.**

Why it evades every normal check:

- **It has no code.** There is nothing to grep for, no guard to read, no comment to
  find wrong. The protection is a side effect of a mechanism whose stated purpose is
  something else entirely.
- **It has no failure history.** A guard that fires leaves logs; a lock that
  serialises leaves nothing but slightly slower runs. There is no incident to search
  for and no test that covers it, because it never broke.
- **Its removal is justified on the other job.** Every argument for the change was
  about readers and writers. All of them were correct. None of them mentioned the
  second job, because nobody knew about it.

What to do, given you cannot enumerate them in advance:

- **Before removing a mechanism, ask what ELSE it happens to prevent** - not what it
  is for. "What used to be impossible here that now becomes possible?" is a
  different question from "what is this for?", and only the first finds these.
- **Expect the discovery to arrive as a new error immediately afterwards**, and read
  a novel failure in the hours after an infrastructure change as evidence about the
  change rather than as an unrelated bug. The collision above appeared within the
  hour and looked at first like plain operator error.
- **Prefer to find it on something re-runnable.** This surfaced on an embed pass that
  could simply be run again. The same latent exclusion protecting a non-idempotent
  write would have been discovered the expensive way.

The consolation: the old behaviour was silent (wait, succeed, no trace) and the new
one is loud (fail on a constraint). Louder is better - but it is no longer
self-correcting, so the serialisation now has to be written down somewhere it can be
read.
