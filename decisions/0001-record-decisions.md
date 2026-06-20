# 0001. How and where decisions are recorded

Date: 2026-03-21 (retroactive; the first batch of records were written on this date to capture decisions already made)
Revised: 2026-06-15 (replaced the single immutable-numbered-ADR scheme with split-by-concern routing - see below)
Status: accepted

## Context

Decisions are made through conversation and research. Without a record, the reasoning behind choices is lost and future contributors (human or artificial intelligence) rediscover the same ground.

The project originally recorded every significant decision as a sequentially numbered, immutable architecture decision record (ADR) in `decisions/`. As the corpus grew it became clear that only about a third of those records are genuinely architectural; the rest are data-model conventions, editorial rules, governance commitments, operational choices, or brand decisions that had been forced into the ADR mould. Mixing concerns made the folder hard to navigate, and the immutable-supersede rule produced churn chains (a taxonomy decision revised three times leaves three records, only the last of which is current).

This record defines where each kind of decision now lives, and how records are maintained.

## Decision

### Decisions are routed by concern

| Concern | Home | Form |
|---------|------|------|
| **Architecture** - how the system is built: pipeline, interchange formats, storage, assembly, ingestion, evidence scoring | `decisions/` (numbered ADRs; `decisions/drafts/` for in-progress) | ADR: Context, Decision, Consequences |
| **Data model, terminology, taxonomy** - node types, naming conventions, claim/extraction conventions, the shared vocabulary | living docs in `architecture/` (`data-model.md`, `node-types.md`, `record-format.md`) | edit-in-place, current state only |
| **Editorial and voice** - how content reads: plain language, neutral voice, AI-authorship disclosure | `guides/editorial-style.md` | living guide |
| **Governance and founding** - what the project is and how it is run: founding aims, name, licensing, funding, scope commitments, disclosure policy | `guides/governance.md` | living charter |
| **Operations and infrastructure** - running the service: domains, hosting, analytics, AI billing and cost controls, jurisdiction | the `operations` repo | operations' call |
| **Visual identity** - logos, palette, design tokens | the `brand` repo | brand's call |

A new decision goes to the home that matches its concern. When a decision spans two (for example, a principle with an operational consequence), the load-bearing half goes to its natural home and the other is a cross-reference, not a copy.

### Numbered ADRs keep their numbers

Architecture ADRs retain their existing numbers. Gaps left where records moved to another home are expected and fine; renumbering would break cross-references for no gain. New architecture ADRs continue the sequence. A numbered ADR may carry `Status: draft` in place while its decision is still being settled (for example 0021, 0031); `decisions/drafts/` holds only unnumbered in-progress drafts not yet promoted to a number.

### Maintenance policy depends on release state

The project is pre-public (nothing is live). While that holds:

- **Consolidate, don't accumulate.** Merge what merges into a single current record; delete records already superseded; collapse churn chains. The living docs hold the current state, not its history - git is the history.

Once the project is public, this tightens for ADRs:

- **Material changes are superseded, not silently rewritten.** A change of decision is recorded as a dated amendment in the record, or as a new record that says what it supersedes and why, so the reasoning trail survives.

Upkeep edits - renamed references, typos, broken links, clarifications - are always fine, in any state, in any home. Git is the audit trail.

## Consequences

- The reasoning behind every choice stays searchable and auditable, but in the home that fits its concern rather than one undifferentiated numbered list.
- The high-churn data-model and taxonomy decisions live as current-state living docs, so a reader sees what is true now without walking a supersede chain.
- Operational and brand rationale lives with the teams that own those surfaces.
- This record is the canonical statement of the routing rule; the inherited root CLAUDE.md carries a concise pointer to it so agents working in any component file decisions correctly.
