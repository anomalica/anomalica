# Populated is not decided

Internal method knowledge (a reference note). The companion to [absence is not a
verdict](absence-is-not-a-verdict.md), and the harder one to catch. That note is
about a missing value read as a decision. This one is about a PRESENT value read
as a decision when nothing decided it:

> **Ask what a field contains when no decision has been made. If the answer is
> "a value", its presence proves nothing.**

A NULL invites suspicion. A populated column invites none, which is why this
shape survives longer.

## Three instances in one day (2026-08-18)

**A seed that looks like a working layer.** `records.work_id` names the WORK a
record is a copy of, so that two files of one book count as one source. Every row
had it:

    SELECT COUNT(*), COUNT(DISTINCT work_id) FROM records;   ->  80 | 80
    SELECT SUM(work_id = id) FROM records;                   ->  80

80 of 80 populated, and 80 of 80 equal to the record's own id. The column is
seeded at insert precisely so consumers can `GROUP BY` it without handling NULL -
so "populated" is guaranteed and says nothing. The layer had never grouped a
single pair. The check that distinguishes a working dedup layer from an inert one
is not `COUNT(work_id)`, it is `COUNT(DISTINCT work_id) < COUNT(*)`.

**A default that looks like provenance.** The ingester mapped a video platform's
channel into `publisher` and its upload date into `date_published`. Both fields
were populated on every record and both described the REDISTRIBUTOR: a 1988
WXIA-TV news segment recorded as published by a YouTube channel in 2026. Nothing
was missing, so nothing looked wrong; the fields were answering a question nobody
had asked them ("who uploaded this copy") in the slot reserved for another ("who
published this work").

**A guard that looks like it is guarding.** `page_gate` counts sources with
`COALESCE(r.work_id, record_id)` - correctly work-aware - while
`provenance_root` returns the raw `record_id`. Both look right in isolation. Both
would report a number. On the day `link-works` first groups a duplicate they will
contradict each other about the same node, one saying one source and the other
saying eight, and neither will raise anything.

## Why it outlives the absence version

An empty column prompts "why is this empty". A full one prompts nothing, and any
check that asks "is it set" returns yes. All three instances above passed the
obvious verification. Two of them were reported as working before anyone compared
the value to the default.

It is also self-concealing in review: the code that seeds a default is usually
correct and well-commented (`work_id` defaults to the record's own id, with a
comment explaining exactly why), so reading the writer confirms the design and
tells you nothing about whether anything downstream ever changed it.

## The review question

For any field that is supposed to record a decision, judgement or grouping:

1. **What does it contain when nothing has decided?** If that is a value rather
   than NULL, presence is not evidence and every consumer needs the comparison,
   not the field.
2. **What is the query that distinguishes decided from defaulted?** Write it down
   next to the field. For a grouping key it is `COUNT(DISTINCT k) < COUNT(*)`;
   for a seeded id it is `k <> id`; for a provenance field it is whether the value
   could have been produced without anyone looking.
3. **Do two consumers of the same fact compute it the same way?** Where one is
   work-aware and another is record-aware, they agree only while the layer between
   them is inert - and the day it starts working is the day they diverge.

Related: [absence is not a verdict](absence-is-not-a-verdict.md), [you checked one
side and named the other](you-checked-one-side-and-named-the-other.md).
