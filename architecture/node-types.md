# Node Types

The knowledge graph (a structured database of interconnected facts) contains typed nodes (entries) connected by relationships. This document is the current contract for what the extraction pipeline produces; it is edited in place as the taxonomy evolves (git is the history). Each node uses a universally unique identifier as its primary key, consistent across all languages.

> **Taxonomy status.** This documents the live extraction contract (the two-pass nodes prompt). Digests produced before this taxonomy landed still carry the older types: as of 2026-06-21 the live graph holds 217 such nodes (matter 134, concept 58, programme 16, investigation 9) across 18 of 23 records, plus 112 names with old framing ("...Detection Matter"). The chosen cleanup is **re-digestion, not reclassification**: re-extraction reclassifies from the source (handling matter's four-way fold, which no mechanical remap can) and regenerates the names, and a full rebuild then clears the dead-type nodes. A mechanical reclassify has already failed here - a node retyped matter->event kept its "Matter" name and left a same-typed duplicate. Re-digestion runs BEFORE any graph-curation merges ([decision 0038](../decisions/0038-graph-curation-replayable-ledger.md)), since the merge ledger keys on names that re-digestion rewrites; timing is a paced subscription run. Document the contract here, not the stale data.

## Node type summary

**Domain node types** (extracted by artificial intelligence at ingestion): person, organisation, project, place, event, object, document, topic.

**Structural types:** record (the source artefact every claim is extracted from) and claim (the atomic assertion, and the connective tissue between all other nodes).

**Curator-populated:** pattern (a cross-case phenomenon; created by a future cross-corpus curator pass, never emitted by extraction).

Types no longer in the taxonomy: **matter** (folds into event / organisation / project / topic), **concept** (renamed **topic**), **programme** and **investigation** (folded into **project**), **classification** (dropped). These names may linger in the code's type enum as deprecated read-only back-compat but are never emitted.

## Design principles

**Extractable by artificial intelligence at ingestion.** Every domain node type must be something the extraction pipeline can reliably classify from source text. Types requiring cross-corpus interpretation (pattern) are deferred to a curator pass.

**Claims are the connective tissue.** Domain nodes do not link directly to each other. Every relationship passes through a claim. There are no unattributed connections in the graph; every connection is traceable to a source record.

**Extensible without restructuring.** The schema links claims to nodes by universally unique identifier, not by type-specific foreign keys. New node types can be added without altering the core schema or reprocessing existing data.

**Node completeness.** Extraction sweeps every domain type, including the easily-missed: the central phenomenon as a topic (e.g. "Unidentified Aerial Phenomena (UAP)"), military branches, legislative bodies and committees as organisations, schools and academies, and named aircraft/vehicle/vessel types as objects (e.g. "F/A-18").

## Cross-cutting rule: portability (the card test)

Every node name must be identifiable on its own. If you wrote the name on an index card and handed it to a stranger who had never seen the document it came from, that stranger should be able to tell what it refers to.

This rules out names that only make sense in their surrounding context: "the hearing", "the testimony", "this document", "the meeting", "the briefing", "the report". A name like "the testimony" appearing alone in the knowledge graph is unfindable - which hearing, whose testimony, when?

Names that pass: "Luis Elizondo's written testimony to the House Oversight Subcommittee on Unidentified Anomalous Phenomena, 13 November 2024"; "House Oversight Subcommittee UAP hearing of 26 July 2023"; "2024 AARO Historical Record Report, Volume I".

The portability rule applies to every node type, and is the general form of the type-specific durability rules below (the place rule, the topic rule). It is the criterion the extraction pipeline uses to decide whether a candidate name is a node or just a sentence fragment.

### Acronyms in node names

The subject matter is heavy with acronyms (AATIP, AARO, VFA-41, CSG-11, FLIR, AAV). An acronym alone fails the card test: a reader who does not already know the field cannot tell what "VFA-41" or "AAV" refers to, and acronyms collide across domains.

The rule: acronyms in node names are written as "Full Name (ACRONYM)". "Strike Fighter Squadron 41 (VFA-41)" beats "VFA-41". "Carrier Strike Group 11 (CSG-11)" beats "CSG-11". "Anomalous Aerial Vehicle (AAV)" beats "AAV". The expanded form makes the node identifiable; the acronym in parentheses preserves searchability for readers who only know the short form.

Inside claim text, acronyms are expanded on first use the same way: "forward-looking infrared (FLIR) pod", "weapons systems officer (WSO)". Subsequent uses within the same claim may use the acronym alone.

The original-excerpt field preserves the source's exact wording, which often uses the acronym alone. Normalisation lives in the node name and the claim text, not in the excerpt.

### Redacted and anonymous people

When a source identifies an actor only by job title with a redacted or unknown name ("the 3rd Fleet N2 (redacted)", "USS Louisville Commander (redacted)", "FASTEAGLE 01 WSO (redacted)"), there is no person to extract. A node "USS Louisville Commander (redacted)" is not a person - it is a role label attached to an unknown actor. Creating it as a person node clutters the graph with unidentifiable placeholders that the importer will never match across records.

The rule: do not create a person node for a redacted or anonymous actor. Attribute the claim to the relevant organisation (3rd Fleet Intelligence, USS Louisville, Strike Fighter Squadron 41), and describe the role in the claim text ("a 3rd Fleet intelligence officer stated..."). If a later document identifies the same actor by name, that document produces the person node and the earlier claim can be re-attributed during review.

Callsigns paired with redacted personnel (FASTEAGLE 01, FASTEAGLE 02) follow the same logic: the callsign is the aircraft-and-pilot together on a specific mission, not a durable identifier. Reference the actual aircraft type and the identified pilot (where named) as separate nodes; mention the callsign in claim text.

## Classification rules

These rules are used by the extraction pipeline to assign domain types. Apply them in order.

| Question | If yes | Type |
|----------|--------|------|
| Is it a single named human individual? | Yes | **Person** |
| Is it a named entity that acts (body, unit, company, outlet, foundation)? | Yes | **Organisation** |
| Is it a named goal-aimed effort with a sponsor and temporal scope (programme, investigation, inquiry, task force, research project)? | Yes | **Project** |
| Is it a named information artefact (book, report, FOIA release, transcript, article, podcast, video, memo, testimony, patent)? | Yes | **Document** |
| Is it a named geographic location? | Yes | **Place** |
| Can you put a single date on it (it happened at a specific time)? | Yes | **Event** |
| Is it a specific named physical thing you could point at or hold? | Yes | **Object** |
| Is it a named idea, theory, framework, or principle that exists independent of any one document? | Yes | **Topic** |

**Tiebreakers:**

- **Project vs Organisation**: an organisation exists to do many things; a project exists to do one named thing. The Department of Defense is an organisation; AATIP is a project it ran. An entity with an advisory board, trustees, or board of directors is organisation-shaped (advisory boards exist around standing organisations, not around projects) - so NIDS, despite studying one named subject, is an organisation.
- **Project vs Event**: a hearing is an event; the multi-hearing inquiry that contains it is a project. A testimony is an event; the complaint it was given to is a project.
- **Project vs Document**: the effort is the project; the report it produces is a document. Both exist as separate nodes linked by claims.
- **Topic vs Project**: a topic is a named idea independent of the corpus (general relativity, electromagnetic pulse); a project is a named effort. "Anti-gravity propulsion" is a topic; "the Galileo Project" is a project.
- **Object vs Document**: a physical thing versus an information artefact. Metamaterial samples are objects; a memo is a document. Something can be both as separate nodes (the Rosetta Stone is an object and a document).
- **Person vs Organisation**: a human individual is a person; anything else with its own name is an organisation, even if run by a single person. Joe Rogan is a person; The Joe Rogan Experience is an organisation.
- **Topic vs Pattern**: a topic exists independent of the corpus; a pattern is visible only because the corpus has multiple cases, and is curator-created, not extracted (see Pattern).

Finer distinctions within **project** (programme, investigation, inquiry, committee, task force) live in an optional `metadata.kind` field, not in the node type - the programme-versus-investigation split proved unworkable for both the model and reviewers, and users search for the union.

A single real-world thing may produce multiple nodes of different types. This is expected, not an error.

## Domain node types

### Person

A named human individual.

**Canonical form: "Last, First Middle", plain legal name only - no titles, ranks, honourifics, or suffixes.** "Fravor, David", not "Commander David Fravor"; "Rubio, Marco", not "Senator Marco Rubio".

- **No titles or ranks.** A title or rank is a property of a person at a point in time, not part of their identity, so it is captured as a dated claim ("David Fravor held the rank of Commander in the US Navy") rather than baked into the name. Names stay stable as people change roles, and the graph accumulates a career history as records are ingested.
- **Surname first.** The surname is the durable identifier (first names vary: Lue/Luis, Dave/David), is often the only part initially known ("Captain Fravor" before any first name appears), sorts usefully, matches official identification, and follows the project's "most important first" convention (cf. dates YYYY-MM-DD, places largest-unit-first).
- **Aliases.** Informal names, shortened forms, transliterations, and the reverse "First Last" order are stored as aliases on the node, not as the canonical name (canonical "Elizondo, Luis"; aliases "Lue Elizondo", "Luis Elizondo"). The digester's matcher tolerates either ordering during integration.
- **Non-Latin names** use the person's own script as canonical, with romanisations as aliases (canonical 岸田文雄; aliases Kishida Fumio, Fumio Kishida).
- **Single-name figures and pseudonyms** remain as-is (Madonna, Whiskey-99).

Presentation reordering and culturally appropriate titles ("Commander David Fravor", "フレーバー司令官", "le commandant Fravor") are the assembler's job, drawn from claims and language directives; storage uses the one canonical form.

Examples: Fravor, David; Elizondo, Luis; Reid, Harry; Kean, Leslie.

### Organisation

A named entity that acts: government bodies, military units, companies, research groups, publications, podcasts, foundations, news outlets, and any other named entity that is not a human individual. An organisation can be run by a single person - if it has its own name, it is its own entity. Programmes, investigations, and task forces are not organisations; they are projects.

Examples: the US Navy, Sol Foundation, GEIPAN, NewsNation, the Weaponized podcast, The New York Times, Anomalica.

### Project

A named goal-aimed effort: a name, a sponsor, a temporal scope, and work it exists to do. Subsumes operational programmes, formal investigations and inquiries, task forces, and research efforts - the programme-versus-investigation distinction is not a type boundary (it proved unworkable for the model and reviewers, and users search for the union). Where the distinction matters to a consumer, an optional `metadata.kind` (programme, investigation, inquiry, committee, task_force) carries it.

The public URL section is `/projects/`.

Examples: AATIP, AAWSAP, Project Blue Book, the Galileo Project, the UAP Task Force (UAPTF), the AARO Historical Record Report review.

### Place

A named geographic location or region.

- Place node names carry no locational qualifier: "USA, California, San Diego", never "San Diego (vicinity)" or "(offshore)". The vicinity nuance belongs in the claim text.
- Names use largest-unit-first ordering ("USA, Nevada, Area 51"), the same "most important first" convention used for dates and person surnames.
- Bare countries, regions, and military operating areas are not place nodes; that geography lives in the claim text.

Examples: Skinwalker Ranch, Area 51, Rendlesham Forest, Fukushima.

### Event

A discrete thing that happened at a specific time. If you can put a single date on it, it is an event.

Examples: the 2004 Nimitz tic tac encounter, Grusch's 2023 congressional testimony, the 1947 Roswell crash, the 2017 New York Times AATIP disclosure.

### Object

A specific named physical thing: craft, materials, devices, biological samples, sensor equipment, and named aircraft/vehicle/vessel types. Not for information artefacts - those are documents.

Examples: the tic tac object, the Gimbal object, metamaterial samples, the Go Fast object, the F/A-18.

### Document

A named information artefact: a book, report, Freedom of Information Act release, congressional transcript, news article, podcast episode, video, memo, testimony, patent, or case file. A document node is a pointer, not a copy - it describes how to find the original (URL, ISBN, archive identifier) but does not reproduce the content (some are copyrighted or confidential; the platform refers users to the original). A document links to the person or organisation that produced it - a producer is a source, which is a role, not a type.

The public URL section is `/documents/`. (In code the type is `document`; it is distinct from the structural `record` type below - a referenced information artefact versus the ingested source a claim is extracted from.)

Examples: Lex Fridman Podcast #122 (David Fravor interview), the Nimitz encounter executive summary, Elizondo's resignation letter to Secretary Mattis, Coulthart's "In Plain Sight".

### Topic

A named idea, theory, framework, principle, or recurring theme that a document treats as a thing in its own right. Topics are referenced by claims, not derived from them: being referenced by a claim is sufficient for a topic to exist; it need not be the subject of an asserted claim. General relativity is referenced throughout the corpus ("Einstein's relativity predicts gravitational waves") but never itself asserted; it is still a topic node that many claims point at.

The public URL section is `/topics/`.

Examples: general relativity, anti-gravity propulsion, reverse engineering of recovered craft, the simulation hypothesis, the Pais Effect.

Boundary rule (controls over-extraction of every abstract noun):

- The topic must be **recognised and exist independent of the document** - a reader could look it up and find it defined elsewhere (general relativity, superconductivity, zero-point energy). An ad-hoc theory named only within one document ("the test-flight theory") is not a topic; it is captured as the speaker's opinion claim.
- Strict exclusions, do not emit a topic for: anything touchable (object - "room-temperature superconductor" is an object, "room-temperature superconductivity" the topic); anything tied to a specific time (event or project); a person, place, or organisation; an effort people run over time (project); a vague catch-all where almost anything fits the label ("the big secret", "the phenomenon"); jargon or a mechanism lifted from quoted technical/patent text; a claimed capability or consequence.
- A topic must be nameable and durable: someone reading only the node name should know which idea it is, and it should be the same idea wherever it recurs. Merge synonyms to one node (superluminal travel = faster-than-light travel = warp speed: one topic, the rest aliases).

Topics carry no truth status. Whether anyone believes a topic is expressed through claims that reference it, with their own attestation and provenance, exactly as for every other node type.

## Structural types

### Record

The source artefact a claim is extracted from - a podcast episode, a document, a transcript, a video, or a case file as it exists in the ingest store. Every claim traces to exactly one record (its source) plus a location within it. A record is a pointer to the original material, not a copy.

The record is distinct from the `document` domain type: a record is the ingested source a claim comes from; a document is a domain node for an information artefact referenced or discussed in the graph. The same real-world book can be both - a record (if it has been ingested) and a document (as a referenced entity). The producer of a record - the person or organisation behind it - is its source (a role, not a type).

### Claim

An atomic assertion extracted from a record. The smallest unit of information in the knowledge graph, and the mechanism by which all other nodes are connected.

A claim always has:

- **Source record** - which record it was extracted from.
- **Location in record** - where the assertion appears. For audio and video this is an `HH:MM:SS.D-HH:MM:SS.D` timestamp range (an assertion spans seconds, and a question-and-answer claim spans both turns); for documents, a page, section, paragraph, or chapter.
- **Speaker** - the person who made the assertion (a Person node, which may differ from the record's producer - e.g. a guest on a podcast). Absent for claims that have no speaker (for example a reviewer's visual observation, which is attributed to the reviewer, not a speaker).
- **Claim type** - the nature of the assertion (below).
- **Node references** - zero or more links to domain nodes. A claim can reference any number, or none ("The universe is a simulation" is a valid claim with no domain-node references; it still has provenance).

Optional:

- **Attestation** - how close the speaker was to the events described: first-hand, second-hand, or third-hand. Set only when there is a genuine evidential stance about the events; omitted for plain narration, framing, or a bare fact with no stance.
- **Claim role** - the narrative function the claim plays (below).

Conventions for claim text:

- **Units: SI, spelled out.** Claim text uses metric SI written in full ("kilometres per hour", "metres", "kilograms"), never abbreviations and never imperial. The original imperial value survives only in the verbatim excerpt. Preserve the source's precision and hedges ("about", "approximately"); never fabricate precision.
- **Assertion, not reported speech.** The claim text is the fact; a reporting-verb anchor naming the speaker ("X stated/said/noted that ...") is forbidden, because the speaker is already in the structured speaker field. When the speaker merely relays a fact about something else, drop the name and state the bare fact; when the speaker is the actor, observer, or opinion-holder, name them as the subject with a substantive verb ("David Fravor observed ...", "Ryan Graves considers ...").
- **Question and answer.** The claim is the answer, attributed to the answerer; a leading question that contains the fact does not make the interviewer the source. The verbatim quote for a Q&A claim contains both turns, each speaker named, and the location spans both.

#### Claim types

| Type | Definition | Example |
|------|-----------|---------|
| **Observation** | The source directly perceived something. | "I saw an object hovering at 50 metres altitude." |
| **Testimony** | The source is formally stating something on record or under oath. | "Under oath, I can tell you I was briefed on a crash retrieval programme." |
| **Hearsay** | The source is relaying what someone else said. | "Colonel X told me there are recovered craft." |
| **Opinion** | The source is expressing a belief or interpretation. | "I believe the government is hiding recovered craft." |
| **Measurement** | Instrument or sensor data. | "Radar showed an object descending from 24,000 metres in 0.78 seconds." |
| **Administrative** | Dates, funding, personnel assignments, organisational facts. | "AATIP was funded at $22 million per year." |

Claim type is orthogonal to attestation. A claim can be first-hand opinion, second-hand testimony, or third-hand hearsay about a measurement.

#### Claim role

A second axis, orthogonal to claim type, capturing the narrative function the claim plays in the story an article tells. Optional - many claims (background, definitional, administrative) leave it null; it is set only when a claim is structurally important to how an article presents a case.

Intended use is to let the assembler structure articles by role (what happened, then official accounts, then documented evidence the accounts were incomplete - producing the contrast structurally, without instructing the model to treat any account as suspect). This is designed but NOT yet implemented: the assembler does not currently read `claim_role`; it assembles free-form prose from claims in chronological/document order (see [assembler.md](assembler.md)). Role-based structuring is a planned feature, not current behaviour.

| Role | Definition |
|------|-----------|
| `official_explanation` | A statement from a government, military, or other official actor explaining or attributing an event - initial account or later revision. |
| `witness_testimony` | A statement from a person directly present for the event, or directly involved in the matter. |
| `investigation_finding` | A statement from a formal investigation's published output. |
| `cover_up_evidence` | A statement documenting concealment, suppression, retraction, intimidation, or document destruction. |

Example: a pilot's radar contact is `claim_type: measurement`, `claim_role: witness_testimony`; a Pentagon press release attributing Roswell to a balloon programme is `claim_type: administrative`, `claim_role: official_explanation`. The digester proposes the role; the reviewer confirms or overrides.

#### How claims connect nodes

Example: "Luis Elizondo ran AATIP from 2007 to 2012." Produces a Claim node with record (the Elizondo interview), location (timestamp range), speaker (Person: Luis Elizondo), claim type (administrative), temporal bounds (2007 to 2012), and references (Person: Luis Elizondo, Project: AATIP).

Example: "David Fravor observed a tic tac shaped object over the Nimitz operating area on 14 November 2004." Produces a Claim node with record (the Fravor interview), location (timestamp range), speaker (Person: David Fravor), claim type (observation), attestation (first-hand), date (2004-11-14), and references (Person: David Fravor, Object: tic tac object, Event: 2004 Nimitz encounter). The operating area is described in the claim text, not as a place node.

## Curator-populated types

### Pattern

A recurring phenomenon observed across multiple cases in the corpus. **Not emitted by extraction** - a pattern is created by a future cross-corpus curator pass over the populated graph and confirmed by human review. A pattern is justified when at least three independent cases exhibit the same shape, nameable in a sentence that does not depend on any one of them ("UAP observed near nuclear facilities" passes; "what happened over Malmstrom in 1967" is a single event, not a pattern). Patterns may be:

- **Morphological** - recurring object shapes (orb, triangle, tic tac, grey, mantis).
- **Behavioural** - recurring UAP behaviour (hovering over restricted airspace, paralleling nuclear facilities).
- **Procedural** - recurring patterns in the official response (shifting accounts, document destruction, denial followed by partial acknowledgement after independent disclosure).
- **Phenomenal** - recurring effects on witnesses and equipment (biological effects, radiation exposure, electromagnetic disruption).

Lifecycle: cross-corpus discovery proposes candidate patterns; a human confirms, rejects, or names them; per-claim tagging suggests which claims support each pattern (pre-filtered by embedding similarity before any model call); the assembler generates the pattern page from the confirmed claim set. The human role is curation - proposing, confirming, naming - not narrative writing.

Status: the type exists; the discovery pass is not yet built, so there is currently zero pattern output.

## Node slugs

Every node maps to a URL slug for its page. The slug is `metadata.explicit_slug` if the node carries one, otherwise the output of the canonical slugifier in `anomalica-common` - a single-producer helper (the discipline used for claim_hash) imported by both the assimilator and the assembler so the two cannot diverge. The slugifier uses **first-last order for persons** (`david-fravor`) - note this differs from the last-first canonical node name (`Fravor, David`) - and applies deterministic disambiguation for genuinely-distinct same-name entities. The slug is resolved once, by the synthesiser, into the brief (`page.slug` and `related_nodes[].slug`); the assembler is writer-only and does not read node metadata, so a slug not pre-resolved into the brief would silently break pattern-slug URLs and their cross-links. (The shared slugifier is landing now in anomalica-common, resolving a brief-vs-deployed slug divergence; it supersedes the earlier per-caller `slugify(title)`.) See the [brief format](brief-format.md) and [decision 0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md).

## Non-human intelligence

The current types are designed around the data as it exists today, which is overwhelmingly human testimony about anomalous phenomena. Person covers named human individuals.

If a named non-human intelligence appears in the data (an entity that communicates, is individually identifiable, and warrants its own node), the schema supports adding a new type (such as Being or Intelligence) without restructuring. Claims link to nodes by universally unique identifier, so a new type plugs in the same way Person does. This is a deliberate design choice: account for the possibility without over-engineering for it now. Similarly, if distinct non-human groups or species emerge, Organisation could accommodate them, or a new type could be added.
