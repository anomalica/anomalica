# 0021. Content review lifecycle

Date: 2026-04-02
Status: draft

> **2026-06-16 (reorg review).** Not ratified - this design is not yet built and exposes an open decision. The review/verification system (`review.yaml` + `verification.yaml`) does not exist in the content repo yet (zero such files). The directory model also conflicts with reality: the assembler emits FLAT entity articles (`content/pages/<section>/<slug>.<lang>.md`, no sidecars), while hand-authored pages (about, contact, legal) use the document-first directories this record specifies. Ratifying requires deciding flat versus document-first for entity articles - a cross-cutting call (assembler output path and multi-language emission, the site's Hugo content structure, the workbench's `review.yaml` location), not a doc edit. **Recommendation: document-first**, so an entity's language versions plus `review.yaml`/`verification.yaml` sit together and entity articles match the hand-authored pages; the assembler's flat output would change to comply. To be converged with assembler/site/workbench as a separate design workstream. (Also: `architecture/assembler.md`'s review section is currently wrong - it states the assembler writes a flat `<slug>.review.yaml` verification sidecar; the assembler writes no YAML at all. To be fixed when this lands.)

## Context

Anomalica publishes content before it has been reviewed by humans. This is deliberate - requiring review before publication would gate content behind reviewer availability and create bottlenecks. However, readers and contributors need to know whether content has been checked, and reviewers need a way to record their assessments.

The project already has artificial intelligence (AI) verification (0010) which checks whether assembled articles faithfully represent the knowledge graph (a structured database of interconnected facts). Human review is a separate concern: has a person read this content and confirmed it is correct, well-written, and appropriate?

Reviews must work across 30 languages (see the governance charter). A reviewer in any language should be able to review content in their language without needing English. The review system must not create a hierarchy where English reviews are privileged over others.

The system must also distinguish between reviews (audit trail) and directives (assembler instructions). These serve different purposes and have different consumers.

## Decision

### Separation of concerns

**Directives** are instructions to the assembler. They live in each document's frontmatter and in `_directives.yaml` files in the content hierarchy (as defined in the assembler architecture). The assembler reads directives as input. Humans write directives.

**Reviews** are an audit trail of human assessment. They record that a specific person read a specific version of the content at a specific time and left feedback. Reviews are historical records. They do not instruct the assembler directly.

**The bridge between them**: when a reviewer identifies an issue that requires a content change, a human reads the review and creates or updates a directive. Reviews inform humans. Directives instruct the assembler. The assembler never reads reviews.

### Review storage

Each document has a `review.yaml` sidecar file that sits alongside the content files. Reviews are stored as an append-only timeline:

```yaml
- date: 2026-04-02
  language: en
  reviewer: Mark Willard
  body_hash: "sha256:abc123..."
  comment: "Verified analytics section is accurate"

- date: 2026-04-03
  language: de
  reviewer: Hans Mueller
  body_hash: "sha256:def456..."
  comment: "Date format should use European convention"
```

Reviews are never deleted or modified. The log only grows. Each entry records the language reviewed, a cryptographic hash of the document body (excluding frontmatter) at the time of review, and the reviewer's comment. The hash is a fixed-length fingerprint computed from the content - if even one character changes, the hash changes, making it possible to detect whether the content has been modified.

### Computing review status

Review status is not stored as a field. It is computed at build time:

1. For each language version of a document, hash the current body content
2. Find the most recent review entry for that language in review.yaml
3. If the hashes match, the content has been reviewed since its last change
4. If they do not match, the content has changed since the last review
5. If no review entry exists for that language, the content has never been reviewed

This means reviews are never explicitly invalidated. When the assembler regenerates content, the body hash changes, and the computed status naturally becomes "unreviewed" without any reset mechanism.

### Review status display

At build time, Hugo reads review.yaml and computes the review status for the current language. The page renders one of:

- **Reviewed**: reviewer name, date, and comment are available. The content has not changed since this review.
- **Updated since last review**: a previous review exists but the content has changed. The previous review date is shown for context.
- **Not yet reviewed**: no review has ever been submitted for this language.

This is informational. Review status is never a gate - content publishes regardless.

### Relationship to AI verification

AI verification (0010) and human review are independent systems:

- AI verification checks whether the article faithfully represents the knowledge graph. It is automated and runs after each assembly.
- Human review checks whether a person has read the content and finds it correct. It is manual and happens when a reviewer chooses to review.

Both use hash-based verification to detect whether the content has changed since the check was performed. Both are informational, not gates. An article can have AI verification, human review, both, or neither.

### Document-first directory structure

Content is organised by document, not by language:

```
people/
  david-fravor/
    index.en.md
    index.ja.md
    index.zh.md
    review.yaml
    verification.yaml
```

All language versions, human reviews, and AI verification for a document live in one directory. This makes it easy to see at a glance which languages exist and whether reviews are present, and eliminates 29 duplicate directory trees.

Hugo supports this layout using filename-based language detection (the `.en.md`, `.ja.md` suffixes).

## Consequences

- Every document directory contains all its language versions and metadata in one place
- Reviews accumulate as an append-only log and never require maintenance
- Review status is always computable and never stale
- Reviewers in any language are equal - no English-first hierarchy
- The assembler's interface is unchanged - it reads directives, not reviews
- Humans bridge the gap between reviews and directives when action is needed
- The existing AI verification system (0010) continues to work alongside human review
- The directory structure change from language-first to document-first affects the assembler's output format and Hugo's configuration
