# Anomalica editorial and voice style guide

A living guide to how Anomalica writes: plain language, neutral voice, and open disclosure of AI's role. It consolidates the editorial decisions formerly recorded as ADRs 0006 (plain language), 0007 (neutral voice), and the disclosure half of 0009 (transparent AI use). Edited in place; git is the history. See [decisions/0001](../decisions/0001-record-decisions.md) for how decisions are routed.

## Plain language

Jargon and unexplained acronyms select out readers and give cover to imprecision. All Anomalica documents - code comments, architecture docs, decision records, and public content - use plain language.

### Acronyms

- Spell out every acronym on first use in every document; do not assume the reader has read any other document. "Freedom of Information Act (FOIA)" first, then "FOIA".
- If an acronym appears fewer than three times in a document, spell it out every time. It earns its place only if the full phrase recurs often enough to be genuinely awkward.
- Universally understood computing terms are fine without expansion: URL, PDF, HTML. When in doubt, spell it out.

### Jargon

- When a technical term is necessary, explain it in plain terms on first use ("a provenance chain - the path a claim took from its original source to the knowledge graph").
- Prefer the plain version where it loses no precision: "evidence trail" over "provenance chain", "first-hand" over "primary attestation".
- Never use a complex word where a simple one works: "use" not "utilise", "show" not "demonstrate", "build" not "construct".

### Audience

- Architecture and code documentation: write for a competent programmer who may not know this specific domain.
- Public-facing content (website, README): write for a curious person with no technical background.
- Decision records: write so someone unfamiliar with the project can follow the reasoning.

## Neutral voice

The platform's model is wire-service reporting, not a magazine: report what sources say, attribute it, and let the reader draw conclusions. This applies to all content, whether AI-assembled or contributed by humans through the directive system.

- **No opinion pieces** - no editorials, perspective articles, or commentary.
- **No characterisation of the field or community** - articles do not call the topic "controversial", "fringe", or "legitimate"; they present what sources say.
- **No promotional language** - the platform does not call itself "groundbreaking" or "the first"; it states what it does.
- **No speculative conclusions** - no "this extraordinary claim" or "this compelling evidence"; the evidence score speaks for itself.
- **No assumption of truth or falsehood** - the platform does not declare claims true or false; it presents what sources say, how well-corroborated they are, and what the scoring produces.
- **Every assertion traces to a source** - if it cannot be attributed to a specific source in the knowledge graph, it does not appear (the architectural guarantee is [decision 0008](../decisions/0008-content-traceable-to-sources.md)).

Human directive contributions follow the same rules: corrections and additions must cite sources; the directive system is for factual input, not opinion.

## Quotation

Quotes are as long as they need to be to convey their point. The platform does not artificially truncate quotations or enforce a quote-length cap - a supporting quote runs to the length that conveys the fact, no more. Every quote is attributed to its source record.

This is lawful quotation (Japan's Copyright Act Article 32, with attribution under Article 48) and standard editorial practice, not a liberty the platform takes. It applies to the short evidential quotes that substantiate claims - NOT to full source bodies or transcripts, which stay behind the proof-of-possession gate (quote is not body). The copyright basis and the substantiality line are in [source types and copyright](../decisions/drafts/source-types-and-copyright.md#quotation-policy).

## Disclosing AI's role

AI is central to the platform and its use is communicated openly - never hidden, minimised, or apologised for. The methodology page on the website explains, in accessible terms:

- **Why AI is used** - maintaining articles across 30 languages with full source traceability is not feasible by hand; AI is the mechanism that makes the platform's promises possible, not a shortcut.
- **How AI is constrained** - articles are assembled only from knowledge-graph data, never from the model's training data; every claim traces to a source (see [decision 0008](../decisions/0008-content-traceable-to-sources.md)).
- **How quality is ensured** - a different model from a different provider independently verifies that every assertion traces to the graph (see [decision 0010](../decisions/0010-auditable-assembly.md)).
- **How humans participate** - all articles are open for human correction; edits become persistent directives the AI respects on future updates.

AI is involved at every stage (extraction, graph-building, assembly, translation) - unavoidable black boxes. The platform's answer is to make each box's inputs and outputs visible: the source document, the digest extracted from it, the assembled article, the verification report. The aim is not to remove the need for trust but to make every step as verifiable as possible.
