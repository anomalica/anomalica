# 0006. Plain language in all documents

Date: 2026-04-03
Status: accepted

## Context

Jargon and unexplained acronyms select out readers. They signal insider knowledge and discourage people who are new to a topic from engaging. They also provide cover for imprecision - a term like "attestation level" sounds authoritative but means nothing to someone encountering it for the first time.

This project aims to be transparent and accessible across languages and backgrounds. The documentation, code comments, and public-facing content should be readable by someone who is interested in the subject but has no prior exposure to the terminology.

## Decision

All Anomalica documents use plain language. This means:

### Acronyms

- Spell out every acronym on first use in every document. Do not assume the reader has read any other document. Write "Freedom of Information Act (FOIA)" on first use, then "FOIA" is acceptable after that.
- If an acronym appears fewer than three times in a document, spell it out every time. An acronym only earns its place if the full phrase appears often enough that repeating it is genuinely awkward.
- Universally understood computing terms are acceptable without expansion: URL, PDF, HTML. When in doubt, spell it out.

### Jargon

- When a technical term is necessary, explain it in plain terms on first use. "Every claim has a provenance chain - the path it took from the original source to the knowledge graph, showing each step along the way."
- Prefer the plain version where it works just as well. "Evidence trail" over "provenance chain" if no precision is lost. "First-hand" over "primary attestation."
- Do not use a complex word where a simple one works. "Use" not "utilise." "Show" not "demonstrate." "Build" not "construct."

### Audience

- Architecture and code documentation is read by developers, but not all developers share the same background. Write for a competent programmer who may not know this specific domain.
- Public-facing content (the website, the README) is read by anyone. Write for a curious person with no technical background.
- Decision records are read by contributors and the public. Write them so that someone unfamiliar with the project can understand the reasoning.

## Consequences

Documents will be slightly longer where terms are explained. This is a worthwhile trade-off for accessibility.

Existing documents will be retrofitted to comply. New documents follow this convention from the start.
