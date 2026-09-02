# Match the family, not its current members

Internal method knowledge (a reference note). When code acts on a FAMILY of things defined by a shared invariant - a marker prefix, a file-type group, a set of node types, a class of events - match the invariant, never an enumeration of today's members. A pattern pinned to the current members is a standing invitation for the next member to slip through, and it does so silently: nothing errors, the new case just goes unhandled, and the guarantee the code was enforcing is quietly void.

## The worked example (2026-07-20): the pre-digest overlay strip

The pre-digest must strip the reviewer-overlay marker family - `highlight-start`, `highlight-end`, `note-*`, `link-start`, `link-end`, `highlight-context` - so reviewer annotations never reach the extraction model (ADR 0042's eval-only guarantee: a highlight the model can see biases the very extraction it exists to grade blind).

The strip was written as `\{\{(?:highlight|link)-(?:start|end): ...\}\}` - the suffixes `start`/`end` hardcoded. It matched the members that existed the day it was written. Then:

- Highlights had already been leaking earlier for a different reason (the transform never touched them at all) - caught and fixed (digester `d277345`).
- The **next** family member, `{{highlight-context: [...]}}`, sailed straight through the "fixed" glob into the model input - because `context` is not `start` or `end`. It reopened the exact leak, the day the annotation was specified (`48b2512`, now `\{\{(?:highlight|link)-<anything>: ...\}\}`, with a test asserting the general case).

An overlay family is defined by its PREFIX. A pattern that enumerates its suffixes is not matching the family - it is matching a snapshot of the family, and every future member is a silent leak until someone happens to notice reviewer text in the model input.

## The rule

Match by the invariant that defines the family - the prefix, the type-group, the interface - not by listing its current members. Where you must enumerate, assert the GENERAL case in a test: "any overlay-prefixed marker is stripped", not "highlight-start and highlight-end are stripped". Then adding a new member without extending the handler fails the test, instead of passing while the member leaks. The failure mode here is always silent - the enumeration keeps working for the cases it names and quietly ignores the rest - which is why it must be a test that fails, not a review that has to remember.

Related: [which layer is authoritative](which-layer-is-authoritative.md) and [validating embedding spaces](validating-embedding-spaces.md) - all three are cases where a check that looked complete was silently measuring, or matching, less than it appeared to.

## It recurs one level up

The same file has now produced the same failure twice, at two levels of
the same pattern.

`_OVERLAY_MARKER` in `anomalica_common.pre_digest` originally enumerated
**suffixes** - `(start|end)` - so `{{highlight-context: ...}}` reached the
model input the day it was specified. The fix matched any suffix within a
family, which closed the suffix hole.

It left the **family** list enumerated: `(highlight|link|note|cites)`. That
is the identical shape one level up, and it is what let
`{{classification: ...}}` through into claim extraction.

Fixing an enumeration by widening it inside one axis does not remove the
enumeration - it moves the hole outward. Ask which axis is still a list of
names, and whether the safe answer there is an allow-list or a deny-list.
Here the allow-list fails open: an unlisted family is passed through to the
model rather than held back, so every future annotation type is a leak
until someone adds it.

## It recurs one axis over: the notation, not the family

Found 2026-09-02, in the workbench, while investigating why a reviewer's two
panes disagreed about which page they were on.

A page marker is a comment carrying a `file_page` line. Most records write it
inline:

    <!-- file_page: 12 -->

Three records write it as a block, grouped with the printed page number:

    <!--
    file_page: 12
    printed_page: 4
    -->

Both were produced by the same handler; the shape is not a version, and a
single record can mix the two. The matcher was written as
`<!--\s*file_page:\s*(\d+)\s*-->`, which is not an enumeration of family
members - it is an enumeration of **punctuation**. `\s` spans newlines, so the
pattern looks like it tolerates the block form, and it does not: the
`printed_page` line sits between the number and the `-->`.

It found 0 of one record's 63 markers, 3 of another's 16, and 12 of a third's
13.

## Why this instance is worse than a leak

The two earlier instances passed something through that should have been held
back. This one produced a REPORT. The survey did not fail, return nothing, or
look partial - it named three specific records as missing their pages, with
counts, in the same format as the two records that really were broken. Five
faulty records, three of them fiction. The corpus owner's own read said two,
and the honest resolution was to go and find out which instrument was wrong
rather than to average the answers.

A leak is discovered when someone notices the wrong thing downstream. A wrong
census is acted on: it was minutes from becoming a re-extraction request for
three clean records, which is model spend against a fault that does not exist.

## The rule, restated for this axis

Parse the thing, then look inside it. A page marker is a comment CONTAINING a
`file_page` line - so match any comment, then test its contents. Matching the
delimiters, the whitespace, or the line breaks is matching a snapshot of how
the family is currently spelled, and the next writer spells it differently
without anyone deciding to.

The test that catches it asserts the general case across notations: the same
record parsed both ways yields the same count. A test written against the
notation you had in front of you passes forever and proves nothing.

Related: [the instrument answers in the expected shape](the-instrument-answers-in-the-expected-shape.md).
