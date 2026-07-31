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
