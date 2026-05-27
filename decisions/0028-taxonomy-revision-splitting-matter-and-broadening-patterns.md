# Taxonomy revision: splitting matter and broadening patterns

Date: 2026-05-24
Status: accepted
Supersedes-in-part: 0011 (claims as the atomic unit), 0025 (concept as ingestion node type)
Amends: architecture/node-types.md

## Context

The current node-type schema (see `architecture/node-types.md`) was
defined when the corpus was small and the ingestion pipeline was the
only stage producing data. The schema landed on a deliberately compact
set of types:

- person, organisation, place, event, **matter**, object, record,
  concept, claim (ingestion)
- pattern, classification (post-analysis, planned but unimplemented)

Two pieces of operational experience now argue against parts of that
shape.

**Matter has degenerated into a catch-all.** The original definition
("an ongoing situation, effort, or process that spans a period of
time") was internally consistent, but in practice the current `matters/`
section of the public site collects a mix of distinct kinds of thing:

- formal programmes with budget and staff (`2007-2017-aatip-program`,
  `aawsap`)
- formal investigations with defined scope and findings
  (`elizondo-aatip-claims-investigation`)
- discrete dated events that were misfiled
  (`2004-nimitz-uap-incident` - a duplicate of an existing event)
- recurring cross-case phenomena (`non-human-craft-recovery-programs`,
  `uap-biological-effects`)

The label "matter" gives readers no information about which of these
they are about to read. It reads as amateurish in the site navigation
and obscures genuinely different kinds of object.

**Programmes-as-organisations is technically correct and practically
wrong.** Treating AATIP and Project Blue Book as organisations with
temporal bounds is defensible at the schema level (they have actors,
staff, budget). It works poorly at the navigation level: a reader
browsing `/organisations/` sees the US Navy, the New York Times, and
Project Blue Book listed alongside each other as equivalent objects.
They are not. Splitting programmes out reduces conceptual noise in
both categories.

**Pattern was scoped too narrowly.** The existing definition restricts
pattern to morphological observational categories (orb, triangle, tic
tac, grey, mantis). The corpus contains a substantially more important
kind of pattern - cross-case phenomena observed in the behaviour of
actors, in the procedural response to events, and in the effects on
witnesses. These patterns are the most important interpretive lens the
site can offer a reader, and the current schema has no place for them.

The shifting-account pattern around Roswell makes this concrete.
Coulthart's analysis in *In Plain Sight* documents a recurring shape:
initial admission, rapid retraction, decades of denial, partial
acknowledgement after independent disclosure forces it. This is a
synthetic claim about the corpus as a whole, not an atomic claim
about a specific event. The current pipeline extracts it as one claim
attributed to Coulthart, then loses it among thirty atomic claims on
the Roswell event page. The pattern is in the source material and
disappears in the published output.

## Decision

### Top-level node taxonomy

Replace the current ingestion taxonomy with a more granular set of
ten domain node types:

| Type | Definition |
|------|-----------|
| **Person** | A named human individual. (Unchanged from current schema.) |
| **Organisation** | A named entity that acts. Government bodies, military units, companies, research groups, publications, podcasts, foundations, news outlets. Programmes are no longer organisations - see Programme below. |
| **Programme** | A funded operational structure that exists to conduct work over time. Has a name, a sponsor, a budget, staff, and a temporal scope. Distinct from organisation in that a programme is the *work* a sponsoring organisation runs, not the actor itself. |
| **Investigation** | A formal probe with defined scope, conducted to answer a question, that produces findings. Distinct from programme in that an investigation has a question and an output report; a programme has ongoing operational work. |
| **Event** | A discrete occurrence with a date. (Unchanged from current schema.) |
| **Document** | An information artefact. Books, podcasts, videos, transcripts, FOIA releases, articles, reports, affidavits, press releases. Renames the existing "record" type to a less technical public-facing term; the schema name in code/database remains `record` to avoid migration churn. |
| **Object** | A specific named physical thing. (Unchanged.) |
| **Place** | A named geographic location. (Unchanged.) |
| **Concept** | A named idea, theory, framework, or principle that exists independent of any single document. (Unchanged.) |
| **Pattern** | A recurring phenomenon observed across multiple cases. Broadened from the previous morphological-only definition - see Pattern section below. |

The **matter** type is removed. All existing matters reclassify as
exactly one of the new types (see Migration).

### Tiebreakers between the new types

The classification rules in `architecture/node-types.md` are updated:

- **Programme vs Organisation**: an organisation exists in order to
  do many things; a programme exists in order to do one named thing.
  The Department of Defense is an organisation; AATIP is a programme
  the Department of Defense ran. The New York Times is an organisation;
  its UAP reporting beat is not a programme. The Galileo Project is
  a programme (a specific funded effort); the institution that hosts it
  is the organisation.
- **Programme vs Investigation**: a programme operates; an
  investigation probes. AATIP was a defence-intelligence programme
  studying UAP encounters - its purpose was operational research, not
  arriving at a finding. AARO's Historical Record Report is an
  investigation - its purpose was answering "what did the US government
  do, when, regarding UAP" and producing a report. Project Blue Book is
  an investigation despite being called "Project" - it ran in order to
  arrive at a stance on the UFO question and produced reports
  concluding it.
- **Investigation vs Event**: a hearing is an event; the
  multi-hearing inquiry that contains it is an investigation. A
  testimony is an event; the IG complaint that the testimony was given
  to is an investigation.
- **Investigation vs Document**: the probe is the investigation; the
  report it produces is a document. Both exist as separate nodes
  linked by claims.
- **Pattern vs Concept**: a concept is a named idea that exists
  independent of the corpus (general relativity, electromagnetic
  pulse). A pattern is a phenomenon visible *because* the corpus has
  multiple cases. "Anti-gravity propulsion" is a concept. "UAP observed
  near nuclear facilities" is a pattern.
- **What terminated the body?** A useful supplementary rule for
  programme-vs-investigation cases that the primary tiebreakers don't
  settle: if the body dissolved after delivering a report, it is an
  investigation. If it was cancelled by budget cut, programme failure,
  or absorbed into a successor, it is a programme. Catches AATIP-as-
  programme (cancelled 2012 when funding dried up) versus Project
  Blue Book-as-investigation (terminated 1969 with the Condon Report
  as its concluding output). UAPTF (the UAP Task Force) dissolved
  after delivering its 2021 preliminary assessment - investigation.
- **Established programme name overrides surface form.** When an
  extracted entity matches a known alias of an existing programme
  node ("AATIP unit", "AATIP office", "the Pentagon's AATIP"), the
  digester classifies it as that programme even when the surface form
  reads organisation-shaped. The existing alias lookup runs at
  extraction time; the new step consults the matched node's type
  before defaulting to organisation.
- **Operational pattern signals**: an entity with an advisory board,
  trustees, or board of directors is organisation-shaped, not
  programme-shaped - advisory boards exist around standing
  organisations, not around projects. Used to disambiguate cases
  like NIDS (National Institute for Discovery Science): it studied
  one named subject (anomalous phenomena) which sounds programme-
  shaped under the "one named thing" test, but it had an advisory
  board including Edgar Mitchell, which is an organisation pattern.
  NIDS is an organisation.

### Pattern (broadened definition)

A **pattern** is a recurring phenomenon observed across multiple cases
in the corpus. Patterns may be:

- **Morphological** - object shapes that recur across observations
  (orb, triangle, tic tac, grey, mantis). The original scope.
- **Behavioural** - behaviour of UAP that recurs across cases
  (hovering over restricted airspace, descending through extreme
  altitude in fractions of a second, paralleling nuclear facilities,
  reacting to weapons-grade fissile material).
- **Procedural** - patterns in the official response to events
  (shifting official accounts, document destruction after sensitive
  events, witness intimidation, NDAs on programme staff, denial
  followed by partial acknowledgement after independent disclosure).
- **Phenomenal** - effects on witnesses and equipment recurring
  across cases (biological effects, radiation exposure, time loss,
  electromagnetic disruption).

A pattern node is justified when **at least three independent cases**
in the corpus exhibit the same shape, and the pattern can be named in
a sentence that does not depend on any one of them. "UAP observed near
nuclear facilities" passes - it names the shape and works
independently of any specific facility. "What happened over Malmstrom
in 1967" fails - that is a single event, not a pattern.

#### How patterns enter the graph

Two distinct operations, run in separate stages:

**Pattern discovery** is a cross-corpus analytical pass over the
populated knowledge graph. It reads claim contents and node
references, runs clustering or behavioural-keyword analysis, and
proposes candidate pattern definitions for human review. Discovery
does *not* run per-record at extraction time - the input is the
populated graph, not the source document, and coupling per-record
extraction to cross-corpus analysis would conflate two unrelated
failure modes. Discovery runs as a separate analytical pass (likely a
`digester/analytics/patterns.py` module or a separate workspace).

**Per-claim pattern tagging** is the per-claim test: "does this
specific claim support pattern X's definition?" This can run anywhere
appropriate - the digester on a re-pass, a workbench backend job, or
a scheduled task. It is a smaller and more bounded operation than
discovery and the architecture should keep the two separate.

The full lifecycle:

1. **Discovery (cross-corpus, periodic)**: the analytical pass reads
   the populated graph and proposes candidate patterns - name,
   definition, supporting cases.
2. **Confirmation (human, workbench)**: a reviewer accepts, rejects,
   or edits the proposed pattern. Confirmed patterns become nodes
   with a `definition` field.
3. **Per-claim tagging (per-pattern, per-claim)**: for each confirmed
   pattern, the system suggests which claims support it, based on
   the pattern's definition. Implementation note: the naive shape -
   one LLM call per claim per pattern - scales as O(claims x
   patterns), which at ~4,300 claims and tens of patterns would burn
   tens of thousands of calls. **Pre-filter by embedding similarity**
   between the claim content and the pattern definition before issuing
   any LLM call. The LLM only adjudicates the high-similarity
   candidates.
4. **Confirmation (human, workbench)**: reviewer confirms or rejects
   each suggested claim-pattern tag.
5. **Assembly (per-page)**: the assembler generates the pattern page
   from the confirmed claim set, using the same prose pipeline as for
   any other entity. Event / programme / investigation pages link to
   the patterns they instantiate via a `patterns: [pattern-slug-1, ...]`
   field on the entity record; the assembler uses this list to open
   the page with framing prose drawn from the pattern's definition,
   not invented by the LLM.

The human role across the lifecycle is curation - proposing,
confirming, rejecting, naming - not narrative writing. Pattern names
and definitions are short structured metadata. Every published page
is AI-assembled from claims, with full provenance.

### Claim role (new tag axis, orthogonal to claim_type)

Claims currently carry one tag dimension - `claim_type` - which
captures the **epistemic** quality of the assertion (observation,
testimony, hearsay, opinion, measurement, administrative). This stays
unchanged.

Add a second orthogonal axis - `claim_role` - which captures the
**narrative function** the claim plays in the story being told. Values
are intentionally minimal:

| Role | Definition |
|------|-----------|
| `official_explanation` | A statement from a government, military, or other official actor explaining or attributing the event. Includes both the initial account and any subsequent revision. |
| `witness_testimony` | A statement from a person directly present for the event being described, or directly involved in the underlying matter. |
| `investigation_finding` | A statement from a formal investigation's published output. |
| `cover_up_evidence` | A statement that documents an instance of concealment, suppression, retraction, intimidation, or document destruction. |

`claim_role` is **optional**. Many claims play no narrative role -
background, definitional content, administrative facts - and leave the
field null. Roles are added only when a claim is structurally important
to how an article presents the case.

**Schema:** `claim_role` is a dedicated column on the claims table -
symmetric with the existing `claim_type` column - not a metadata JSON
field. The migration is `ALTER TABLE claims ADD COLUMN claim_role
TEXT;` with a CHECK constraint allowing the four values plus NULL,
and an index for the assembler's role-grouping queries. The corpus
is ~4,300 claims; SQLite handles the migration instantly. The metadata
JSON path was rejected because it would lose simple
`WHERE claim_role = ...` queryability and would be the only
narrative-relevant tag hidden inside metadata while `claim_type` sits
as a column.

`claim_role` is orthogonal to `claim_type`. The two axes describe
different things. Examples:

- A pilot's radar contact: `claim_type: measurement`, `claim_role: witness_testimony`
- A Pentagon press release attributing Roswell to MOGUL: `claim_type: administrative`, `claim_role: official_explanation`
- A book author's opinion that a cover-up is in progress: `claim_type: opinion`, `claim_role: cover_up_evidence`
- A measurement of craft performance pulled from declassified radar logs: `claim_type: measurement`, `claim_role: investigation_finding`

The digester proposes `claim_role` from speaker affiliation, source
type, and content. The reviewer confirms or overrides in the workbench.

The assembler uses `claim_role` to structure articles. Default
article shape for events:

1. What happened (witness_testimony, ordered by date or significance)
2. Official accounts of the event, in the order they were issued
   (official_explanation, chronologically)
3. Documented evidence the official accounts were incomplete
   (cover_up_evidence + investigation_finding where the finding
   contradicts the official account)
4. Patterns this event instantiates (linked pattern pages)
5. Other context (claims with no role)

This structure produces the editorial result the project wants -
contrast between official accounts and the documented record - without
requiring the LLM to be told "treat official accounts as suspect". The
contrast is **structural**; the voice remains neutral.

### Records keep their schema name; "documents" is the public label

The schema-level node type stays as `record` in code and database
fields to avoid a migration of every column reference. The
public-facing category label, URL, and assembler-generated page
heading become `document` / `/documents/`. The mapping is:

- Schema: `node_type: record`
- Display: "Document"
- URL: `/documents/<slug>`

This is the only naming-asymmetry between schema and presentation. All
other type names match.

## Consequences

### Migration

Existing matter-typed nodes reclassify:

| Current matter | New type | Notes |
|---|---|---|
| `2007-2017-pentagon-advanced-aerospace-threat-identification-program-aatip-ufo-program` | Programme | Operational research; cancelled by funding cut 2012 |
| `advanced-aerospace-weapon-system-applications-program` | Programme | Operational research with contractors |
| `elizondo-advanced-aerospace-threat-identification-program-aatip-claims-investigation` | Investigation | Probe into a specific question |
| `2004-nimitz-uap-incident` | Delete | Duplicate of `events/2004-uss-nimitz-encounter` |
| `non-human-craft-recovery-programs` | Pattern | Cross-case phenomenon despite the word "programs" in the slug |
| `uap-biological-effects` | Pattern | Cross-case phenomenal pattern |
| `2023-grusch-unidentified-anomalous-phenomena-uap-whistleblower-disclosure` | Split | IG complaint becomes Investigation; congressional testimony becomes Event; Debrief article publication becomes Event |
| `aaro-hr2-volume-i` | Investigation | HR2 had a defined question and produced a report |
| `aaro-hr2-program-of-analysis` | Collapse | Methodology subsection of the HR2 investigation; merge into that investigation node |
| `fy2020-ndaa-uap-task-force-provision` | Event | Legislative act on a date that established UAPTF; not a programme or investigation itself |

Existing organisation-typed nodes that should reclassify as programmes
or investigations (not exhaustive; reviewer pass required):

| Current organisation | New type | Notes |
|---|---|---|
| Project Blue Book | Investigation | Ran in order to arrive at a stance on the UFO question; terminated 1969 with the Condon Report as concluding output |
| AATIP, AAWSAP | Programme | Collapse with the matter-typed forms of the same body into single programme nodes |
| Galileo Project | Programme | Specific funded effort; the hosting institution stays the organisation |
| UAP Task Force (UAPTF) | Investigation | Time-limited body that dissolved after delivering the 2021 preliminary assessment; merge the "UAP Task Force" and "Unidentified Aerial Phenomena Task Force (UAPTF)" duplicates |

Existing organisation-typed nodes that **stay** as organisations under
the new tiebreakers (worth recording because they read programme-shaped
at first glance):

| Node | Reasoning |
|---|---|
| AARO (All-domain Anomaly Resolution Office) | Standing office, no fixed terminating report. Its HR2 work is an investigation it conducted, listed above. |
| NIDS (National Institute for Discovery Science) | Had an advisory board (Edgar Mitchell sat on it). Advisory-board pattern is organisation-shaped. The individual "NIDS X Investigation" matters reclassify as events (specific fieldwork on a date) or programmes (ongoing operational efforts like Skinwalker Ranch) - not investigations in the defined sense, because they were operational fieldwork, not probe-with-question-and-report. |

Existing concepts may reclassify as patterns under the broadened
definition (reviewer pass required). Anti-gravity propulsion stays a
concept (a named principle); recurring observed behaviours filed as
concepts may move to pattern.

The reclassification is a database-level update: claim records and
provenance stay intact; only node type and public section URL change.
No re-ingestion is required. A re-assembly pass produces the new
pages at the new URLs. Existing links to old URLs become redirects.

### Schema and pipeline impact

- Digester: new `claim_role` proposal logic; new pattern-suggestion
  pass run periodically over the claim corpus.
- Workbench: pattern proposal flow; claim_role confirmation UI.
- Assembler: structure-by-claim-role logic in the prompt; pattern
  framing field on entity records.
- Site: new section directories, new section index pages, URL
  redirects for the matter -> new-type moves.

### What this does not commit to

This decision sets the taxonomy and the workflow. It does not specify:

- The clustering / similarity algorithm the digester uses to suggest
  patterns.
- The exact UI in the workbench for pattern proposal and claim_role
  confirmation.
- The order in which existing nodes are re-classified.

Those are implementation concerns for the digester, workbench, and
assembler workspaces respectively.
