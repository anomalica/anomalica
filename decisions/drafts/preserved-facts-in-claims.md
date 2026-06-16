# Preserved facts in claims

Date: 2026-05-23
Status: draft

## Context

The assembler reads claims from the knowledge graph and rewrites them into prose via an artificial-intelligence model. The model has full latitude over phrasing, paragraph structure, and which related entities to link, which is desirable - readable encyclopaedic prose is the goal.

But the model also has latitude over *specific factual tokens* inside claims, and this is where corruption sneaks in. Two recent incidents observed on the live site:

- The Roswell UAP Crash article body contained the sentence "On 2025-07-05, ranch foreman Mac Brazel discovered the wreckage" for a 1947 event. The originating claim in the SQLite knowledge graph had `date: '1947-07-05'`, the original_excerpt in the digest YAML carried "On 5 July 1947", the claim's content field said "On 5 July 1947". Every layer of the digester was clean. The assembler-stage model wrote `2025` regardless.
- Earlier reviews of book-extracted claims found numbers being rounded differently in body text than in the originating claim (60,000 feet quoted at 24,384 metres in the article body where the claim explicitly said "approximately 24,000 metres" with the source's "about" hedge intact).

These are not hallucinations in the sense of inventing facts out of nothing - the model is staring at the correct number in the claim it is supposed to be rewriting, and choosing to write a different one. It is *confabulation around a specific factual token*. Dates are easy to detect; numbers, named persons, and direct quotes are harder but the failure mode is identical.

A defence that requires no architectural change works for dates (every date in the body must trace to a date in the claim's content / dates / excerpt / record date) but does not generalise without effort to numbers, persons, or quotes. The graph already knows which tokens were verbatim from the source - we just are not surfacing them as a constraint for the assembler.

## Decision

The digester emits a `preserved_facts` field on every claim. It carries the subset of the claim's data that is guaranteed verbatim from the source - tokens the assembler must reproduce exactly, not paraphrase.

Per-claim shape:

```yaml
- id: <claim_uuid>
  type: observation
  text: "On 5 July 1947, ranch foreman Mac Brazel found crash debris..."
  preserved_facts:
    dates:
      - "1947-07-05"
    numbers:
      - {value: 120, unit: "kilometres"}
    persons:
      - "Brazel, Mac"
    places:
      - "Roswell, New Mexico"
    direct_quotes:
      - "I'm probably about a half mile away..."
  refs: [...]
```

The assembler is told: every value in `preserved_facts` must appear in the assembled body when the claim is cited. The deterministic post-process verifies this and fails loud (refuses to write the article) on any divergence.

Categories, in order of priority for implementation:

1. **dates** (year, year-month, or full ISO date) - already covered by the deterministic guardrail in assembler.py as of 2026-05-23
2. **numbers with units** (altitudes, distances, durations, monetary amounts) - needs unit-aware tolerance (the source's "about 80,000 feet" and the assembled "approximately 24,000 metres" must both round-trip correctly through the unit normalisation rule)
3. **named persons** (canonical-form person names) - any person reference in the body must point at a claim that cites that person
4. **direct quotes** (verbatim spans wrapped in source quotation marks) - if the assembler renders a quote, it must appear verbatim in the source's `original_excerpt`

The digester populates `preserved_facts` deterministically at extraction time:

- `dates` - parse all date-shaped tokens from the claim's content / original_excerpt / date / date_end fields; include the claim's structured `date` and `date_end`
- `numbers` - regex extract number+unit pairs from content (after metric normalisation, per existing rule 12)
- `persons` - cross-reference the claim's node_references where the referenced node has type `person`
- `direct_quotes` - any text inside double-quotes in the original_excerpt

The assembler reads `preserved_facts` for every claim it cites, builds an allow-set of (date | number | person | quote) tokens, and the deterministic post-process refuses to ship an article whose body contains a date / number / person / quote token outside that allow-set.

## Consequences

- Increases the digest YAML size modestly. Each claim gains a small structured block. Existing claims work without it (guardrail is a no-op when `preserved_facts` is absent).
- Makes the failure mode "article fails to assemble" rather than "article ships with corrupted fact". The site never publishes a fabricated date again.
- The assembler's prompt can also surface the `preserved_facts` to the model as an explicit "do not change these tokens" instruction, raising compliance before the deterministic check has to fire.
- Provides a foundation for the independent-verification pass (decision 0010) - the verifier has a structured target rather than scanning prose.
- Does not constrain the model's freedom to rephrase, restructure, link, or summarise. Only the specific tokens marked as preserved are protected.

## Open questions

- **Unit tolerance for numbers.** A claim saying "approximately 24,000 metres" should accept "approximately 24,000 metres" and "approximately 24 kilometres" but not "24,384 metres" (over-precise) or "30,000 metres" (different value). The unit normalisation rule (rule 12 in the digester prompt) already enforces metric and rounded units at extraction time, so this is tractable - but needs a defined tolerance band.
- **Quote granularity.** A long verbatim quote in original_excerpt that the model breaks into two sentences in the body should pass. Sentence-level fingerprinting rather than exact substring match.
- **Migration.** Existing 4,317 claims do not have preserved_facts. They can be backfilled deterministically from their existing fields - no AI required.
