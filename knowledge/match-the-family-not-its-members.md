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
