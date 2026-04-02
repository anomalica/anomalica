# Node Types

The knowledge graph contains typed nodes connected by relationships. This document defines the node types, their purpose, and how they relate. Each node uses a UUID as its primary key, consistent across all languages.

## Design principles

**AI-extractable at ingestion.** Every node type must be something the extraction pipeline can reliably classify from source text. Types requiring subjective judgement or thematic interpretation are deferred to the post-analysis layer.

**Claims are the connective tissue.** Domain nodes (person, organisation, place, event, matter, object) do not link directly to each other. Every relationship passes through a claim. There are no naked edges in the graph. This ensures every connection is traceable to a source record.

**Extensible without restructuring.** The schema links claims to nodes by UUID, not by type-specific foreign keys. New node types can be added without altering the core schema or reprocessing existing data.

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

These types are populated by the AI extraction pipeline during digestion.

### Person

A named human individual.

Examples: David Fravor, Luis Elizondo, Harry Reid, Leslie Kean.

### Organisation

A named entity distinct from any single person. This includes government bodies, military units, companies, research groups, programmes, publications, podcasts, news outlets, and any other named entity that is not a human individual. An organisation can be run by a single person - if it has its own name, it is its own entity.

Examples: the US Navy, AATIP, AAWSAP, Sol Foundation, GEIPAN, NewsNation, the Weaponized podcast, The New York Times, Anomalica.

Note: programmes (AATIP, AAWSAP, Project Blue Book) are organisations with temporal bounds, not a separate type. The "ongoing effort" aspect is captured through claims linking the organisation to events, people, and time periods.

### Place

A named geographic location or region.

Examples: Skinwalker Ranch, Area 51, the Nimitz operating area, Rendlesham Forest, Fukushima.

### Event

A discrete thing that happened at a specific time. If you can put a single date on it, it is an event.

Examples: the 2004 Nimitz tic tac encounter, Grusch's 2023 congressional testimony, the 1947 Roswell crash, the 2017 New York Times AATIP disclosure.

### Matter

An ongoing situation, effort, or process that spans a period of time. Has a start and possibly an end, but is not a single moment. If it unfolds over weeks, months, or years, it is a matter.

Examples: the push for congressional UAP disclosure, the alleged craft retrieval cover-up, the Galileo Project's observation campaign, the AARO investigation backlog.

The distinction from Event is temporal scope: an event has a date, a matter has a date range. The distinction from Organisation is that a matter is a situation, not an actor. AATIP (the programme) is an Organisation. The investigation AATIP conducted is a Matter.

### Object

A specific named physical thing. Craft, materials, devices, biological samples, sensor equipment.

Examples: the tic tac object, the Gimbal object, metamaterial samples, the Go Fast object.

Not for documents or information artefacts. The Wilson-Davis memo is a Record, not an Object.

### Record

A specific artefact that contains information. A podcast episode, a FOIA document, a congressional transcript, a news article, a book, a video, a case file. Records are what claims are extracted from.

A record node is a pointer, not a copy. It describes how to find the original material - a URL, book title, ISBN, archive identifier, FOIA reference number - but does not reproduce the content. Some records are protected by copyright, some may be confidential. The platform refers users to the original rather than hosting copies.

A record links to the person or organisation that produced it. A person or organisation that produces records is a source - this is a role, not a separate node type.

Examples: Lex Fridman Podcast #122 (David Fravor interview), the Nimitz encounter executive summary (AATIP report), Elizondo's resignation letter to Secretary Mattis, Coulthart's "In Plain Sight."

### Claim

An atomic assertion extracted from a record. The smallest unit of information in the knowledge graph and the mechanism by which all other nodes are connected.

A claim always has:
- **Source record** - which Record node it was extracted from
- **Location in record** - where in the record the assertion appears (timestamp, page number, paragraph, chapter)
- **Speaker** - who made the assertion (a Person node, which may differ from the record's producer - e.g. a guest on a podcast)
- **Attestation level** - first-hand, second-hand, or third-hand (see data model)
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

- **Concept** - a recurring idea, theme, or theoretical framework (reverse engineering, nuclear-UAP correlation, simulation hypothesis). Claims cluster around these thematically.
- **Pattern** - a recurring observational category (orb, triangle, tic tac, grey, mantis). Individual observations and objects get classified into these.
- **Classification** - broader taxonomic groupings of patterns or other nodes.

These require subjective judgement to assign and are better suited to human curation, community tagging, or a separate analytical pipeline than to initial AI extraction.

## Non-human intelligence

The current ingestion types are designed around the data as it exists today, which is overwhelmingly human testimony about anomalous phenomena. Person covers named human individuals.

If a named non-human intelligence appears in the data (an entity that communicates, is individually identifiable, and warrants its own node), the schema supports adding a new type (such as Being or Intelligence) without restructuring. Claims link to nodes by UUID, so a new type plugs in the same way Person does. This is a deliberate design choice: account for the possibility without over-engineering for it now.

Similarly, if distinct non-human groups or species emerge in the data, Organisation could potentially accommodate them, or a new type could be added.
