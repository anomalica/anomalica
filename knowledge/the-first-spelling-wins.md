# The first spelling wins

Internal method knowledge (a reference note). Entity resolution at import is
**greedy and first-wins**: the first form of a name to arrive creates the node, and
every later variant is scored against what already exists and merged into it if it
clears a threshold. That is a reasonable design for a corpus that accumulates
gradually. It behaves very differently when one record contributes hundreds of
entities in a single pass - which is what a book does.

Recorded because the symptom gets re-diagnosed as a one-off every time. It is not.

## The worked example: 30 claims filed under the wrong man

Found 2026-07-28 while measuring an unrelated migration.

The graph held one node for **Harry Reid**, the late US Senator, carrying
`"Reid, Garry"` as an alias. Garry Reid is a Pentagon official who ran the inquiry
into Luis Elizondo - a different person entirely. Thirty claims about him had been
filed on the senator's node, among them:

> The Department of Defense Inspector General concluded that Garry Reid violated
> Joint Ethics Regulations by creating a sexualised work environment.

Harry Reid died in 2021. Had that page been assembled, it would have been defamatory
of a named real person. (It had not: measured against the published corpus, the
misattribution was graph-only.)

The mechanism is arithmetic, not bad luck. Person names were then stored
surname-first, so the matcher compared comma components and merged when the weakest
cleared `STRUCTURED_COMPONENT_THRESHOLD = 0.80`:

```
levenshtein_ratio("garry", "harry") = 0.800     # exactly the threshold
```

The same computation, on the same day, also merged `"Almond, Andre"` into
`"Almond, André"` at 0.800 - correctly. One threshold, two pairs, one right and one
wrong, and nothing in the name distinguishes them. A cut that lands *exactly* on real
data is not calibrated, it is coincidence.

## Why books make this the normal case, not the edge case

Two books were already **51% of the claim corpus** (Imminent, 1457 claims / 659
nodes; In Plain Sight, 914 / 593) at the time of writing. Three things compound
during a single large import:

- **First-wins is decided by emission order, not by evidence.** Whichever spelling
  the extraction model happened to produce first becomes canonical for every later
  variant. Nothing prefers the better-attested form.
- **There is no corroboration signal to arbitrate.** Corroboration is cross-record;
  during the first book covering a subject there is, by construction, nothing to
  corroborate against. The matcher is deciding identity with the least evidence it
  will ever have.
- **Volume raises the collision rate.** Hundreds of new people arriving at once
  makes near-miss surname and forename pairs far more likely than the same count
  arriving spread over many records.

## The rule

1. **Treat a bulk import as a distinct regime.** Run duplicate-candidate detection
   and a similarity profile AFTER EACH large record, not once at the end. The
   duplicates a book creates are findable immediately and get harder to see once the
   next book piles on top of them.
2. **A threshold that sits exactly on observed values is not a threshold.** If real
   pairs score at the cut, it is separating nothing; look at what the cut is made of
   before adjusting the number.
3. **Prefer a missed merge to a false one, and make each cost visible.** A missed
   merge is two nodes a curator can join with one command. A false merge silently
   attributes one person's conduct to another, and reads as fact on a page.
4. **Structure that looks like precision may be the thing losing it.** The comma in
   surname-first names was documented as preserving matching precision. Measured, it
   was the source of the only false merge in the corpus: dropping it split Garry
   from Harry correctly, at the cost of one accent pair that a diacritic fold then
   recovered.

A caveat on tuning against today's corpus: every extraction to date ran at minimum
reasoning effort, so present-day name inconsistency partly reflects extraction
quality rather than the domain. Tune matching thresholds hard against this corpus
and you may be fitting to noise that a re-extraction removes.

Related: [match the family, not its current members](match-the-family-not-its-members.md),
[measuring tells you what is, not what survives](measuring-tells-you-what-is-not-what-survives.md),
[claims fusion as a robust SLAM back-end](claims-fusion-as-robust-slam.md).
