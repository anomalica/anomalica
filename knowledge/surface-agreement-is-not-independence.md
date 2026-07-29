# Surface agreement is not independence

Internal method knowledge (a reference note). Anomalica's central claim about
itself is that a fact is supported by *independent* sources. Independence is
expensive to measure, and every cheap proxy for it measures **agreement** instead
— that two things look alike, or came from two files, or were counted twice.
Agreement and independence diverge exactly where it matters, and every proxy
fails in the flattering direction: it reports corroboration that is not there.

Three instances turned up in one evening (2026-07-29), in three different parts
of the pipeline, each found separately. They are one shape.

## 1. Similarity: one event described twice is not one fact attested twice

Embedding cosine over cross-record claim pairs, full corpus, sampled and read by
band:

| Band | What the pairs actually are |
|---|---|
| ≥ 0.85 | Same fact, different records. Real corroboration. |
| 0.80–0.85 | **Same event, different facts.** |
| ≤ 0.75 | Same topic, no shared assertion. |

The 0.80–0.85 band is the trap:

    0.829  "...as Fravor moved to intercept the Tic Tac near the turbulent water"
           "...as Fravor's aircraft pulled to within about 800 feet"

Both are the 2004 Nimitz encounter. Neither attests the other. Counting them as
corroboration means **an event corroborates itself with its own narrative
detail** — the more richly a single source describes something, the better
attested it appears.

This is the band a threshold picked by eye lands in, and it lands there *because*
the pairs look right: they are unmistakably about the same thing. Reading the
counts alone would never have found it; the counts are monotonic and say nothing
about what is being counted.

## 2. Source count: two sources can be one book and a passing mention

The page gate counted `COUNT(DISTINCT record_id)` and admitted anything with two.
Measured across 226 page proposals, **120 (53%)** had a second source
contributing fewer than 3 claims — Jacques Vallée at 15 claims with 14 from one
copyrighted book, Area 51 at 17 with 16. The count was 2 in every case.

Severity ran *inverse* to claim count: 100% of proposals under 6 claims failed,
against 9% of those over 20. So the floor itself (3 claims from 2 sources) was
manufacturing the problem at the bottom of the range, not books contaminating it
from the top. A count with no notion of distribution cannot see this.

## 3. Record count: the guard inverts under duplication

Records are content-addressed by exact bytes, so one work becomes several records
on any re-download, re-export or edition change. That does not merely evade the
independence floor — it **reverses the metric built to detect the failure**:

    Jacques Vallée today          15 claims, top 14, second 1   -> flagged, correctly
    the same book ingested twice  14 claims, top 7,  second 7   -> reads as excellent spread

A duplicate turns the guard into an endorsement, and the pages it blesses most
confidently become the ones with the worst provenance. A metric that inverts
under the failure it exists to detect is more dangerous than no metric.

## Why every one fails flatteringly

None of these is a random error. Each proxy counts *occurrences of agreement*,
and every mechanism that breaks independence — reprinting, duplication, one
source describing itself at length — **creates more occurrences of agreement**.
The proxy therefore moves up exactly when independence goes down. There is no
version of this that errs toward under-reporting.

## The rule

1. **Name what the proxy measures, in the proxy.** "Distinct record count" is an
   honest name; "independent sources" is not, for the same number. The false name
   is what lets it be trusted.
2. **Read the members, do not just count them.** All three were found by looking
   at what fell inside a band or behind a count. Counts are monotonic and
   agreeable; they will never volunteer that they are counting the wrong thing.
3. **Ask what the failure mode does to the metric.** If the answer is "raises it",
   the metric cannot be a guard against that failure — and if the answer is
   "inverts it", the metric is worse than nothing.
4. **Independence has to come from provenance, not from resemblance.** ADR 0039
   requires counting by source/provenance-root; ADR 0044 carries the chain that
   makes it computable. Until those are populated, every independence number in
   the system is an agreement number wearing a better label, and should be banked
   rather than scored on.

Related: [absence is not a verdict](absence-is-not-a-verdict.md) — the same
flattering-direction argument for missing data; [the first spelling
wins](the-first-spelling-wins.md); [claims fusion as a robust SLAM
back-end](claims-fusion-as-robust-slam.md), which is the theory this sits under.
