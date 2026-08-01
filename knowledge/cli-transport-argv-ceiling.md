# The CLI transport's argv ceiling

If a component dispatching through the subscription CLI fails with a bare
`E2BIG` that names no argument, this is why.

## The limit

Linux caps a **single argv element** at `MAX_ARG_STRLEN` - 32 pages,
131,072 bytes. This is separate from, and much smaller than, the ~2MB
`ARG_MAX` total. A prompt passed as one `-p <prompt>` argument therefore
has a hard 128KB ceiling however much room the total budget has left.

Measured against the real corpus (11,437 node names, mean 26.7 characters)
at 3,017 nodes:

| Passed in argv | Size | |
|---|---|---|
| Node directory inside the prompt | 143 KB | **over the cap - this was the failure** |
| Claims schema carrying the node enum | 91 KB | always fitted; never the problem |

Fixed by moving the prompt to **stdin**, which has no such limit
(anomalica-common `072bc8b`, digester `989f746`), verified in both
directions rather than reasoned about.

## The ceiling that remains

`--json-schema` has no file form, so the schema necessarily stays in argv
and keeps a ceiling of its own. Current headroom is roughly **37KB, about
1,278 more nodes** - a catalogue-shaped corpus trips it again somewhere
near **4,300 nodes**.

Write that number down wherever it next matters. The next person to hit it
will not connect `E2BIG` to a node count.

## It is a ceiling on complexity, not size

This is the part that makes it a corpus-coverage property rather than a
component bug. What trips it is **many distinct named entities per
kilobyte** - catalogue-shaped sources - not file size:

- *In Plain Sight*, 778KB, runs fine.
- *Passport to Magonia*, smaller, failed.

So the limit excludes a **class** of source, and it does so silently: a
bare `E2BIG` names no argument, and a source that failed quietly would
simply not be in the corpus with nothing recording why. A coverage gap
produced by an infrastructure limit looks exactly like a source nobody got
round to ingesting.

## The wrong cause was more expensive than the bug

For two days the blocked-items file carried "do not re-add until the
schema-in-argv fix lands" - a fix for something that was never broken. The
schema was the largest plausible culprit and was written down as the cause
without being measured.

Had anyone implemented it, they would have shrunk the schema, watched the
book fail identically, and had no idea why. See
[measuring-tells-you-what-is-not-what-survives](measuring-tells-you-what-is-not-what-survives.md)
for the general form: a confidently recorded wrong cause is worse than no
cause at all.
