# A replayed decision meets a graph that moved

Internal method knowledge (a reference note). Curation decisions - merges, renames,
rejections, vetoes - live in durable ledgers and are replayed over a freshly rebuilt
graph, because a rebuild wipes the database and only the digests and the ledgers
survive. The ledger is keyed on **natural identity** (name + node type) rather than
node id, precisely so a decision survives the ids churning on every re-import.

That key is the right idea, and it has two failure modes that are both silent and
both point the wrong way. A replay runs against a graph the corpus has changed
underneath it, and neither "the thing I decided about has moved" nor "my decision is
now wrong" is something a replay can see.

## Failure 1: the decision is discarded because its anchor moved

Discovered 2026-07-29, assimilator `5fb6c4f`.

Every curation merge in the corpus is CROSS-TYPE: the same name under two node
types, where the curator's job was to pick which type to keep. The replay resolved
the chosen **survivor** first and abandoned the whole op if it was absent:

```
survivor_id = _resolve_natural(conn, e["survivor"])
if survivor_id is None:
    log(f"replay skip ...: survivor not in graph")   # and the victims stand
```

But the survivor is exactly the node most likely to be gone. The curator kept the
`investigation`; the digester now emits `organisation` and `project`. The op was
discarded and the two duplicates stayed live - the merge did not half-apply, it
vanished, and the log line read like routine housekeeping.

It presented as "15 of 46 merges skipped", which sounded catastrophic. Measuring
each op against a fresh graph gave the real split: **1** genuinely lost merge (a live
`organisation`/`project` duplicate that should have been one node), **12** where only
one node remained so there was nothing left to collapse, and **2** where no node
survived at all. Worth separating, because the three want different responses and a
single "skipped" counter hid all three.

The fix is to stop treating the survivor as the anchor. A merge asserts *these nodes
are one thing*; if any two of them are present, that assertion still applies. Replay
now follows whichever nodes exist and takes the most-cited as survivor.

## Failure 2: the decision is applied and silently undoes newer work

Same day, same session. A migration rewrote person names to natural order
("Fravor, David" -> "David Fravor") across every digest. One node came back from the
rebuild still surname-first: `School, Harvard Medical`. The migration had rewritten
it correctly; a merge op in the ledger carried `canonical_name: "School, Harvard
Medical"`, and `merge_nodes` unconditionally applies the ledger's canonical name to
the survivor at the end of the merge. The ledger, faithfully replayed, reverted a
migration that ran after it was written.

**A ledger entry is a decision made against a snapshot of the graph.** Replaying it
verbatim asserts that decision is still current, which a corpus-wide migration may
have made false. Nothing in the replay path can detect this: the write succeeds, the
node exists, the name is a name.

## The rule

Replaying a durable decision over a rebuilt graph needs three things that are easy to
omit:

1. **Anchor on the assertion, not on one participant.** "These are the same thing"
   survives one participant disappearing. Resolve every participant, then decide
   whether the assertion still has anything to act on.
2. **Separate and count the outcomes.** applied / absorbed (nothing left to do) /
   lost (unrecoverable) are three different states. One "skipped" counter reports a
   dropped human decision in the same breath as a no-op, and the flattering reading
   wins - see [absence is not a verdict](absence-is-not-a-verdict.md).
3. **Log the unrecoverable one as an error.** The 15 skips had been happening on
   every rebuild for a month and were found only because someone asked a direct
   question about merge provenance. A decision that cannot be applied must be as
   loud as a crash, because there is no other signal that it is gone.

The second failure has no clean fix yet and is recorded as a known hazard: a ledger
op can carry a value (here, a name) that a later corpus-wide change invalidates, and
replay will restore the stale value. Whichever ledger owns a field should be the only
one that writes it - naming belongs to `renames.yaml`, not to a merge's
`canonical_name` - and until that is enforced, a migration must be re-checked against
the graph AFTER replay, not just after import.

Related: [which layer is authoritative](which-layer-is-authoritative.md),
[absence is not a verdict](absence-is-not-a-verdict.md),
[defaults are where the bugs hide](defaults-are-where-the-bugs-hide.md).
