# Which layer is authoritative when a doc and the code disagree

Internal method knowledge (a reference note). When an audit finds a spec and the code contradicting each other, the instinct is to decide which side is stale and edit it. That instinct is wrong often enough to be dangerous: most apparent doc-vs-code conflicts are really *doc-vs-the-wrong-code-layer*. Establish the layer before you touch either side.

## The layers, in order of what they actually prove

- **A schema / enum is a PARSER, not a policy.** `VALID_NODE_TYPES`, a `NodeType` enum, a JSON-schema `enum` - these are permissive on purpose, because they must still read old artefacts and old database rows. A deprecated value sitting in an enum proves only that something once emitted it. It is not a claim that anything emits it now. Enums usually say so in a comment; read the comment.
- **A prompt is the POLICY** - what the model is actually taught to emit. But prompts move. A module-level constant is not the registry file, and the registry file is not necessarily the one that is *wired*. Follow the call path to the prompt the live path loads.
- **Emitted output is the TRUTH.** What did the model actually produce, on real records, recently? One query over the store settles in seconds what reading code argues about for an hour.

The order matters: enum < prompt < emitted output. Never conclude from the enum. Prefer the output.

## The trap: a test can defend the wrong side

A migration completes everywhere except one corner, and the corner survives because **a test is enforcing it**. The stale code then looks maintained rather than abandoned - it is green, it is covered, nobody suspects it. When a doc and code disagree and the code side looks deliberate, check whether a test is holding the stale side in place. That is the tell for an abandoned corner wearing a maintained costume.

## Worked example (2026-07-16): the node-taxonomy "conflict"

A drift audit reported `architecture/digester.md` as stale against `node-types.md`. Reading `digester/workspace/digester/extract.py` appeared to show something far worse - the canonical taxonomy contradicting the live extractor on three points: `project` missing, `concept` instead of `topic`, `pattern` extracted despite being curator-only. It looked like a taxonomy decision that blocked bulk digestion.

All three evaporated:

- The live policy is `prompts/nodes.txt` (loaded via `prompt_registry`), whose `node_type` enum is `node-types.md`'s eight verbatim, and which states outright that matter/concept/pattern are not extraction types and that patterns are curator-created.
- The contradiction was `extract.py`'s `EXTRACTION_PROMPT` - a **module constant**, the legacy single-pass prompt, teaching the whole pre-0029 taxonomy (matter x14, concept x8, pattern x7, `project` zero times) and still wired into a `extract()` nothing called.
- One query over emitted nodes across six real variants disproved all three at once: `project` 14, `topic` 21, `document` 29, `concept` 0, `pattern` 0, `matter` 0.

What kept it alive: a test named `test_concept_is_a_first_class_node_type`, actively enforcing the superseded taxonomy. Outcome: the spec was correct and unchanged, `digester.md` needed one missing type added, and 634 lines of legacy prompt/schema/extractor plus seven tests were deleted (digester `fe6a22b`).

The cost of getting this wrong is asymmetric. "The doc is stale, edit it to match the code" would have rewritten the canonical taxonomy to a design abandoned months earlier, and every record digested afterwards would have been re-digest fodder. Dead code that teaches a superseded design is not merely confusing - any caller that reaches it silently gets the old design, and fallbacks are exactly the callers that appear later without anyone noticing.

## The rule

Settle doc-versus-code with emitted output, not by reading either side. If you cannot query output, follow the call path to the wired policy. Only then decide which side is stale - and check for a test defending it before you believe the code was deliberate.
