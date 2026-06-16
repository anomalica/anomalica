# Node Types

The knowledge graph (a structured database of interconnected facts) contains typed nodes (entries) connected by relationships. This document defines the node types, their purpose, and how they relate. Each node uses a universally unique identifier as its primary key, consistent across all languages.

## Design principles

**Extractable by artificial intelligence at ingestion.** Every node type must be something the extraction pipeline can reliably classify from source text. Types requiring subjective judgement or thematic interpretation are deferred to the post-analysis layer.

**Claims are the connective tissue.** Domain nodes (person, organisation, place, event, matter, object) do not link directly to each other. Every relationship passes through a claim. There are no unattributed connections in the graph. This ensures every connection is traceable to a source record.

**Extensible without restructuring.** The schema links claims to nodes by universally unique identifier, not by type-specific foreign keys. New node types can be added without altering the core schema or reprocessing existing data.

## Cross-cutting rule: portability (the card test)

Every node name must be identifiable on its own. If you wrote the name on an index card and handed it to a stranger who had never seen the document it came from, that stranger should be able to tell what it refers to.

This rules out names that only make sense in their surrounding context: "the hearing", "the testimony", "this document", "the meeting", "the briefing", "the report". A name like "the testimony" appearing alone in the knowledge graph is unfindable - which hearing, whose testimony, when?

Names that pass: "Luis Elizondo's written testimony to the House Oversight Subcommittee on Unidentified Anomalous Phenomena, 13 November 2024"; "House Oversight Subcommittee UAP hearing of 26 July 2023"; "2024 AARO Historical Record Report, Volume I".

The portability rule applies to every node type, and is the general form of the type-specific durability rules below (the place rule, the concept rule). It is the criterion the extraction pipeline uses to decide whether a candidate name is a node or just a sentence fragment.

### Acronyms in node names

The subject matter is heavy with acronyms (AATIP, AARO, VFA-41, CSG-11, FLIR, AAV). An acronym alone fails the card test: a reader who does not already know the field cannot tell what "VFA-41" or "AAV" refers to, and acronyms collide across domains.

The rule: acronyms in node names are written as "Full Name (ACRONYM)". "Strike Fighter Squadron 41 (VFA-41)" beats "VFA-41". "Carrier Strike Group 11 (CSG-11)" beats "CSG-11". "Carrier Intelligence Center (CVIC)" beats "CVIC". "Anomalous Aerial Vehicle (AAV)" beats "AAV". The expanded form makes the node identifiable; the acronym in parentheses preserves searchability for readers who only know the short form.

Inside claim text, acronyms are expanded on first use the same way: "forward-looking infrared (FLIR) pod", "weapons systems officer (WSO)". Subsequent uses within the same claim may use the acronym alone.

The original_excerpt field preserves the source's exact wording, which often uses the acronym alone. Normalisation lives in the node name and the claim text, not in the excerpt.

### Redacted and anonymous people

When a source identifies an actor only by job title with a redacted or unknown name ("the 3rd Fleet N2 (redacted)", "USS Louisville Commander (redacted)", "FASTEAGLE 01 WSO (redacted)"), there is no person to extract. A node "USS Louisville Commander (redacted)" is not a person - it is a role label attached to an unknown actor. Creating it as a person node clutters the graph with unidentifiable placeholders that the importer will never match across records.

The rule: do not create a person node for a redacted or anonymous actor. Attribute the claim to the relevant organisation (3rd Fleet Intelligence, USS Louisville, Strike Fighter Squadron 41), and describe the role in the claim text ("a 3rd Fleet intelligence officer stated..."). If a later document identifies the same actor by name, that document produces the person node and the earlier claim can be re-attributed during review.

Callsigns paired with redacted personnel (FASTEAGLE 01, FASTEAGLE 02) follow the same logic: the callsign is the aircraft-and-pilot together on a specific mission, not a durable identifier. Reference the actual aircraft type and the identified pilot (where named) as separate nodes; mention the callsign in claim text.

## Classification rules

These rules are used by the extraction pipeline to assign types. Apply them in order.

| Question | If yes | Type |
|----------|--------|------|
| Is it an artefact containing information (a document, episode, article, video)? | Yes | **Record** |
| Is it a single named human individual? | Yes | **Person** |
| Is it a named entity distinct from any single person? | Yes | **Organisation** |
| Is it a named geographic location? | Yes | **Place** |
| Can you put a single date on it (it happened at a specific time)? | Yes | **Event** |
| Does it unfold over a period of time (weeks, months, years)? | Yes | **Matter** |
| Is it a specific named physical thing you could point at or hold? | Yes | **Object** |

**Tiebreakers:**

- **Organisation vs Matter**: does it act, or does it unfold? A group with staff and a name is an organisation. The work that group does over time is a matter. Both can coexist as separate nodes.
- **Event vs Matter**: one date or many? A single hearing is an event. A multi-year investigation is a matter.
- **Object vs Record**: physical thing vs information artefact. Metamaterial samples are objects. A memo is a record. Something can be both (the Rosetta Stone is an object and a record - two separate nodes).
- **Person vs Organisation**: a human individual is a person. Anything with its own name that is not a human individual is an organisation - even if run by a single person. Joe Rogan is a person. The Joe Rogan Experience is an organisation. Anomalica is an organisation even if founded by one person.

A single real-world thing may produce multiple nodes of different types. This is expected, not an error.

## Ingestion types

These types are populated by the artificial intelligence extraction pipeline during digestion.

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

A named entity distinct from any single person. This includes government bodies, military units, companies, research groups, programmes, publications, podcasts, news outlets, and any other named entity that is not a human individual. An organisation can be run by a single person - if it has its own name, it is its own entity.

Examples: the US Navy, the Advanced Aerospace Threat Identification Program (AATIP), the Advanced Aerospace Weapon System Applications Program (AAWSAP), Sol Foundation, GEIPAN, NewsNation, the Weaponized podcast, The New York Times, Anomalica.

Note: programmes (AATIP, AAWSAP, Project Blue Book) are organisations with temporal bounds, not a separate type. The "ongoing effort" aspect is captured through claims linking the organisation to events, people, and time periods.

### Place

A named geographic location or region.

Examples: Skinwalker Ranch, Area 51, the Nimitz operating area, Rendlesham Forest, Fukushima.

### Event

A discrete thing that happened at a specific time. If you can put a single date on it, it is an event.

Examples: the 2004 Nimitz tic tac encounter, Grusch's 2023 congressional testimony, the 1947 Roswell crash, the 2017 New York Times AATIP disclosure.

### Matter

An ongoing situation, effort, or process that spans a period of time. Has a start and possibly an end, but is not a single moment. If it unfolds over weeks, months, or years, it is a matter.

Examples: the push for congressional unidentified anomalous phenomena disclosure, the alleged craft retrieval cover-up, the Galileo Project's observation campaign, the All-domain Anomaly Resolution Office (AARO) investigation backlog.

The distinction from Event is temporal scope: an event has a date, a matter has a date range. The distinction from Organisation is that a matter is a situation, not an actor. AATIP (the programme) is an Organisation. The investigation AATIP conducted is a Matter.

### Object

A specific named physical thing. Craft, materials, devices, biological samples, sensor equipment.

Examples: the tic tac object, the Gimbal object, metamaterial samples, the Go Fast object.

Not for documents or information artefacts. The Wilson-Davis memo is a Record, not an Object.

### Record

A specific artefact that contains information. A podcast episode, a Freedom of Information Act document, a congressional transcript, a news article, a book, a video, a case file. Records are what claims are extracted from.

A record node is a pointer, not a copy. It describes how to find the original material - a URL, book title, ISBN, archive identifier, Freedom of Information Act reference number - but does not reproduce the content. Some records are protected by copyright, some may be confidential. The platform refers users to the original rather than hosting copies.

A record links to the person or organisation that produced it. A person or organisation that produces records is a source - this is a role, not a separate node type.

Examples: Lex Fridman Podcast #122 (David Fravor interview), the Nimitz encounter executive summary (AATIP report), Elizondo's resignation letter to Secretary Mattis, Coulthart's "In Plain Sight."

### Concept

A named idea, theory, framework, phenomenon, or recurring theme that a document treats as a thing in its own right. Concepts are referenced by claims, not derived from them: a concept is a first-class node like every other domain node, and being referenced by a claim is sufficient for it to exist - it does not need to be the subject of an asserted claim. General relativity is referenced throughout the corpus ("Einstein's relativity predicts gravitational waves") but never itself asserted; it is still a concept node that many claims point at.

Examples: general relativity, anti-gravity propulsion, reverse engineering of recovered craft, the simulation hypothesis, the Pais Effect.

Boundary rule (controls over-extraction of every abstract noun):

- The concept must be **recognised and exist independent of the document** - a reader could look it up and find it defined elsewhere (general relativity, superconductivity, zero-point energy). An ad-hoc theory named only within one document ("the test-flight theory") is not a concept; it is captured as the speaker's opinion claim.
- Strict exclusions, do not emit a concept for: anything touchable (object - "room temperature superconductor" is an object, "room temperature superconductivity" the concept; "X device/reactor/craft" is the object, "X" the principle is the concept); anything tied to a specific time (event or matter); a person, place, or organisation; an effort people run over time - research, a programme, an investigation (matter); a vague catch-all where almost anything fits the label ("the big secret", "the phenomenon"); jargon or a mechanism lifted from quoted technical/patent text; a claimed capability or consequence.
- A concept must be nameable and durable: someone reading only the node name should know which idea it is, and it should be the same idea wherever it recurs. Merge synonyms to one node (superluminal travel = faster-than-light travel = warp speed: one concept, the rest aliases). This is the concept analogue of the place rule (specific and durable) and the object rule (subject, not illustration).

Concepts carry no truth status. Whether anyone believes a concept is expressed through claims that reference it, with their own attestation and provenance, exactly as for every other node type.

See [decision 0025](../decisions/0025-concept-as-ingestion-node-type.md) for why this is an ingestion type rather than a post-analysis one.

### Claim

An atomic assertion extracted from a record. The smallest unit of information in the knowledge graph, and the mechanism by which all other nodes are connected.

A claim always has:
- **Source record** - which Record node it was extracted from
- **Location in record** - where in the record the assertion appears (timestamp, page number, paragraph, chapter)
- **Speaker** - who made the assertion (a Person node, which may differ from the record's producer - e.g. a guest on a podcast)
- **Attestation level** - how close the speaker was to what they are describing: first-hand, second-hand, or third-hand (see data model)
- **Claim type** - the nature of the assertion (see below)
- **Node references** - zero or more links to domain nodes the claim mentions

A claim can reference any number of domain nodes, or none at all. "The universe is a simulation" is a valid claim with no domain node references. It still has provenance (who said it, in which record, on what date).

#### Claim types

| Type | Definition | Example |
|------|-----------|---------|
| **Observation** | The source directly perceived something. | "I saw an object hovering at 50 metres altitude." |
| **Testimony** | The source is formally stating something on record or under oath. | "Under oath, I can tell you I was briefed on a crash retrieval programme." |
| **Hearsay** | The source is relaying what someone else said. | "Colonel X told me there are recovered craft." |
| **Opinion** | The source is expressing a belief or interpretation. | "I believe the government is hiding recovered craft." |
| **Measurement** | Instrument or sensor data. | "Radar showed an object descending from 24,000 metres in 0.78 seconds." |
| **Administrative** | Dates, funding, personnel assignments, organisational facts. | "AATIP was funded at $22 million per year." |

Claim type is orthogonal to attestation level. A claim can be first-hand opinion, second-hand testimony, or third-hand hearsay about a measurement.

#### How claims connect nodes

Example: "Luis Elizondo ran AATIP from 2007 to 2012."

This produces a Claim node with:
- Record: Lex Fridman Podcast #2194 (Elizondo interview)
- Location in record: timestamp 00:45:12
- Speaker: Person:Luis Elizondo
- Claim type: administrative
- Attestation: first-hand
- Temporal bounds: 2007 to 2012
- References: Person:Luis Elizondo, Organisation:AATIP

Example: "David Fravor observed a tic tac shaped object over the Nimitz operating area on 14 November 2004."

This produces a Claim node with:
- Record: Lex Fridman Podcast #122 (Fravor interview)
- Location in record: timestamp 01:23:45
- Speaker: Person:David Fravor
- Claim type: observation
- Attestation: first-hand
- Date: 2004-11-14
- References: Person:David Fravor, Object:tic tac object, Place:Nimitz operating area, Event:2004 Nimitz encounter

## Post-analysis types

These types are not populated during ingestion. They are added later through user contributions, editorial review, or analytical processes run over the existing graph. The schema supports adding new node types without structural changes.

Potential future types include:

- **Pattern** - a recurring observational category (orb, triangle, tic tac, grey, mantis). Individual observations and objects get classified into these.
- **Classification** - broader taxonomic groupings of patterns or other nodes.

These require subjective judgement to assign and are better suited to human curation, community tagging, or a separate analytical pipeline than to initial artificial intelligence extraction.

(Concept was previously listed here. It is now an ingestion type - see the Concept section above and [decision 0025](../decisions/0025-concept-as-ingestion-node-type.md). The post-analysis layer may still refine concepts, but is no longer their source.)

## Non-human intelligence

The current ingestion types are designed around the data as it exists today, which is overwhelmingly human testimony about anomalous phenomena. Person covers named human individuals.

If a named non-human intelligence appears in the data (an entity that communicates, is individually identifiable, and warrants its own node), the schema supports adding a new type (such as Being or Intelligence) without restructuring. Claims link to nodes by universally unique identifier, so a new type plugs in the same way Person does. This is a deliberate design choice: account for the possibility without over-engineering for it now.

Similarly, if distinct non-human groups or species emerge in the data, Organisation could potentially accommodate them, or a new type could be added.
