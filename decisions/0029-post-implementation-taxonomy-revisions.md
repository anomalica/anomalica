# Post-implementation taxonomy revisions: topic and project

Date: 2026-05-27
Status: accepted
Supersedes-in-part: 0028 (taxonomy revision: splitting matter and broadening patterns)
Amends: architecture/node-types.md

## Context

[Decision 0028](0028-taxonomy-revision-splitting-matter-and-broadening-patterns.md) was drafted on 2026-05-24. Two of its calls did not survive the implementation phase that followed.

**Programme vs investigation as separate types** (0028's decision: two ingestion types, distinguished by tiebreakers including "what terminated the body?", advisory-board pattern, etc.).

In the 2026-05-25 implementation pass:

- The tiebreakers proved too subtle for the extraction model. Even with explicit prompt rules, the model misclassified the NIDS Skinwalker work, because the context required to apply the tiebreaker ("did this body dissolve after delivering a report, or did it get cancelled mid-operation?") usually is not present in the document being extracted from. Classification needs information the source rarely carries.
- The tiebreakers proved too subtle for humans. During the 157-matter reviewer triage, NIDS-vs-AAWSAP was the canonical "we genuinely don't know" case. Several review notes ended in "going with programme but flag for further discussion" - a smell.
- User navigation expectation breaks under the split. A reader searching for AATIP does not know whether the project chose to call itself a programme or an investigation. They expect to find AATIP under one stable URL. Splitting forces the user to learn the ontologist's framework, not their own mental model.
- No external taxonomy validates the split as natural. Schema.org puts Project as a subclass of Organization (one slot for "named goal-aimed effort"). STIX uses Intrusion Set and Campaign for related work but neither matches programme-vs-investigation. CIDOC CRM does not carry the distinction.

**Concept as the type name** (0028's decision: keep Concept as the type, no rename).

The extraction code was carrying a temporary rename to `principle` to avoid the "concept aircraft" misclassification the original name was producing. The digester ran an empirical comparison on coulthart-ch23 with identical strict inclusion criteria in the prompt - one run using `principle`, one using `topic`. The five emitted nodes were near-identical content across both runs; TR-3B went to object correctly in both. The word does not change extraction behaviour; strictness lives in the prompt rules, not the type name. The right call is to pick the word that reads best in the public URL.

## Decision

### Project replaces programme and investigation

The ingestion node type `project` replaces the separate `programme` and `investigation` types introduced by ADR 0028.

| Type | Definition |
|------|------------|
| **Project** | A named goal-aimed effort. Has a name, a sponsor, a temporal scope, and work it exists to do. Subsumes what 0028 split into "programme" (operational effort) and "investigation" (probe with a question and a report). The distinction proved unworkable in practice; the union is what users search for. |

The tiebreakers in 0028 between programme and investigation no longer apply. The remaining tiebreakers (project vs organisation, project vs event, project vs document) carry over unchanged from 0028, substituting "project" for "programme".

The public URL section is `/projects/`. AATIP, Project Blue Book, AAWSAP, the AARO HR2 review, the Condon Committee inquiry, the Galileo Project, and UAPTF all live under `/projects/`.

### Topic replaces concept

The ingestion node type `topic` replaces the `concept` type. The code, the public-facing display label, and the URL section all use the same word - no schema-vs-display split.

The definition is unchanged from 0028's Concept entry: a named idea, theory, framework, or principle that exists independent of any single document. The boundary rule in `architecture/node-types.md` (recognised independent of the document; strict exclusions for touchable objects, time-bound events, named actors, vague catch-alls, jargon, and claimed capabilities) carries over unchanged. Only the type's name changes.

The public URL section is `/topics/`.

### Finer distinctions live in metadata.kind, not in node-type

For consumers that genuinely need finer distinction within `project` (e.g. a curator listing "investigations only" on the projects page), the recommended pattern is a `metadata.kind` field on the project node carrying values like `programme`, `investigation`, `inquiry`, `committee`, `task_force`. This is a filterable attribute, not a URL routing decision.

Populating `metadata.kind` is optional and not required at extraction time. The digester may emit it where the document makes the distinction obvious; the workbench may set it during review. Consumers should not depend on its presence.

### What this does not change from 0028

- The removal of the matter type (matter-typed nodes still reclassify per 0028's migration table, with the only adjustment being that 0028's "programme" and "investigation" destinations now both resolve to `project`).
- Pattern's broadened definition (morphological, behavioural, procedural, phenomenal) and its lifecycle (discovery, confirmation, per-claim tagging, assembly).
- The `claim_role` field (`official_explanation`, `witness_testimony`, `investigation_finding`, `cover_up_evidence`) - the name `investigation_finding` is kept verbatim despite the type rename; the role describes the narrative function of a claim from a formal investigative output, regardless of whether that output came from a project sub-classed as investigation or not.
- The records-keep-their-schema-name convention for the document display.

## Consequences

### Migration

ADR 0028's migration table updates as follows:

| 0028 destination | 0029 destination |
|---|---|
| Programme (AATIP, AAWSAP, Galileo Project, etc.) | Project |
| Investigation (Project Blue Book, AARO HR2, UAPTF, etc.) | Project |
| All other 0028 destinations | Unchanged |

Existing project-typed nodes in the database (if the implementation collapsed before 0029 landed) are correct as-is. The legacy `programme` and `investigation` entries that may still exist in the code's NodeType enum remain as deprecated back-compat - not removed, to avoid breaking older database states, but not emitted by current extraction.

### Pipeline impact

- Digester: extraction emits `project` not `programme`/`investigation`. NodeType enum keeps legacy entries marked deprecated. Optional `metadata.kind` population where source makes the distinction clear.
- Workbench: project listing shows all entries together; optional filter on `metadata.kind` when populated.
- Assembler: project pages use the same structure regardless of underlying kind. Pattern framing and claim_role grouping unchanged from 0028.
- Site: `/projects/` is the single section; `/programmes/` and `/investigations/` redirect to `/projects/`. `/topics/` replaces `/concepts/` (with redirect). i18n strings update for the new section names.

### Open implementation work

- ADR 0028's pattern migration table referenced "matter" entries reclassifying into Programme; those map to Project under 0029.
- Site templates currently hardcode the 10-category public taxonomy with `programmes` + `investigations` + `concepts`. The new shape is 8 categories: people, organisations, projects, events, places, documents, objects, topics (plus patterns as the post-analysis ninth category). Site has consolidated layouts/i18n/redirects ready to land in one pass.

## Rationale note

This ADR exists because two of 0028's decisions emerged as wrong within a day of being drafted. The pattern is worth recording: ADRs drafted in advance of implementation can capture intent that does not survive contact with the model or with reviewers. The right response is a follow-up ADR that supersedes the bad calls explicitly, not an edit to the original or a silent deviation in code. 0028's broader thrust (remove matter, broaden pattern, add claim_role) stands; only the points enumerated above are revised.
