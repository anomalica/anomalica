# Brief format

The brief is the interchange between the synthesiser (producer) and the assembler/writer (consumer), schema `anomalica/brief/1`. It holds exactly the graph slice that feeds ONE page - language-neutral, before any prose - and is the writer's sole input (see [decision 0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)). Like the digest format (0027), it is a versioned interchange spec.

> **Scaffold - field detail pending.** The brief's internal fields are being iterated under v1 as the assimilator builds the synthesiser. This document fixes the parts already settled (below); the field-level schema is filled from the synthesiser's first real brief artefact rather than guessed, so the spec documents a real brief, not a guess. Until then, treat the field list as indicative, not final.

## Settled now

- **Schema id:** `anomalica/brief/1`, in the frontmatter - the same versioning convention as `anomalica/record/1` (0019) and `anomalica/digest/1` (0027). Breaking changes bump the integer; consumers refuse what they do not understand.
- **Shape:** markdown + YAML frontmatter, a self-contained bundle (like the record format). The body carries the page's graph slice in structured, language-neutral form.
- **Language-neutral.** A brief holds facts, not prose, in no particular language. One brief feeds all N language articles for its page; the writer produces per-language prose from it (per the translation-directives draft).
- **Content = one page's graph slice, before prose:** the nodes for the page, the selected claims with their provenance (source record, location, speaker, attestation), and the relationships among them. Exactly the slice the page is built from - nothing the writer could invent beyond it. This is what makes 0008 enforceable by construction.
- **One brief per page**, emitted by the synthesiser. The page-existence decision (the "enough" threshold) is the synthesiser's and is gated on evidence scoring (0036).
- **Input hash = 0010's audit hash.** The brief's input hash is the "knowledge-graph data" prompt-component hash that 0010 already mandates - the same value used as the per-page staleness/diff unit and the scheduling model's "Something changed?" primitive. One hash, three roles; not a parallel staleness scheme (0036).

## Pending the synthesiser's first real brief

- The exact frontmatter fields: page identity/slug, the node / claim / relationship field names and shapes, the provenance sub-structure, and the hash field's name and exactly what it covers.
- How selected claims carry provenance - mirror the digest's reference shape (0027) or a brief-specific form.
- Whether relationships are explicit edges or implied via shared claims.
- How the page-identity maps to the site's URL sections (the node taxonomy).

The assimilator will hand over the first-cut real brief shape; this spec is filled from that.
