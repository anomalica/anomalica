# Data Model

See also: [node types](node-types.md). This document is the canonical home for platform terminology.

Asset, Selection, `record/3`, exact claim anchors and evidence units below are the
accepted 0051 migration model. Current component implementations remain on legacy
scalar Records and locations until their explicit migrations land.

## Core terms

| Term | Definition |
|------|-----------|
| **Source** | A role, not a node type. A person or organisation that produces records is a source. David Fravor is a Person node who is also a source because he has produced records (interviews, written statements). The New York Times is an Organisation node that is also a source. |
| **Asset** | One immutable acquired byte sequence, or an explicitly linked retained derivative, identified by its full SHA-256. A PDF, audio file, video, ebook, captured page, standalone image or retained render is an Asset. It owns archive, acquisition, format and rights/access metadata. |
| **Selection** | The ordered, typed choice of whole Assets or physical Asset pages that defines a Record. Order is identity-bearing. |
| **Record** | A node type. A stable named logical work defined by one ordered Selection over one or more Assets. One Asset may yield several Records and one Record may compose several Assets. See [decision 0051](../decisions/0051-asset-record-selection-and-evidence-identity.md). |
| **Ingest** | A generated readable representation of one Record, written by the ingester. A Record has one current Ingest and may have historical revisions. Exact body, pre-digest and Git hashes identify revisions; they are not Record identity. |
| **Digest** | The canonical claims file written by the digester from one Ingest. The current pipeline produces one canonical digest; planned comparison candidates remain inert unless a later selector chooses one. |
| **Claim** | A node type. An atomic assertion extracted from an Ingest, carrying a speaker and source location. Eligible page-mapped PDF/image `digest/2` claims carry one or more exact anchors back through the Record Selection to Asset/page intervals; `digest/1` claims retain only non-authoritative scalar display location and are ineligible for anchor-based evidence operations. The smallest unit of information in the knowledge graph and the mechanism by which domain nodes are connected. See [node types](node-types.md). |
| **Directive** | A durable instruction for the assembler, extracted by artificial intelligence from human edits. Affects presentation only (style, grammar, disambiguation, formatting, naming). Cannot alter factual content. |
| **Assemble** | What the assembler's artificial intelligence does with knowledge-graph data to produce articles: arrange existing claims, attributions, and relationships into readable prose. It does not create information. |

## Relationships

- A **person** or **organisation** produces one or more **records** (making them a source)
- One or more immutable **Assets** are chosen by an ordered **Selection** to define a **Record**
- A **Record** has one current generated **Ingest**, which is read to produce one canonical **digest**; prior Ingest revisions remain audit history
- A **record** contains one or more **claims**
- A **claim** has a **speaker** (the person who made the assertion, which may differ from the record's producer)
- An eligible `digest/2` **claim** has ordered anchors in the exact pre-digest body and corresponding Asset/page text. Every interval is half-open and contained by the Record Selection; a `digest/1` claim has no typed anchors and fails closed for overlap and evidence-unit derivation
- A **claim** is attributed to one or more **records** (the same claim may appear in multiple records, which may constitute corroboration if the provenance chains are independent)
- A **claim** references zero or more **domain nodes** (person, organisation, project, place, event, object, document, topic)
- Domain nodes do not link directly to each other. Every relationship passes through a claim.

## Record provenance: who made a record versus who made a claim

A record's source-origin metadata lives in one `provenance` block ([ingest-format.md](ingest-format.md#provenance), [decision 0043](../decisions/0043-canonical-provenance-block.md)) - `publisher`, `creators`, `published_date`, `source_url`, `identifiers`, `collection`, and the rest. Two roles matter for who-said-what:

- **`provenance.publisher`** - the entity that created the source (a channel, outlet, or committee), not the hosting platform.
- **`provenance.creators`** - the human creator(s): a document's author, a video or podcast host or presenter, a named channel owner. Person names in natural order.
- **`speaker`** (per claim) - who asserted a specific claim, which may differ from the record's creator (a guest on a host's podcast; a witness quoted in an article).

The **source** role (the person or organisation that produced the record) is `provenance.publisher` and/or `provenance.creators`. The `speaker` is claim-level, not record-level. All three may coincide (a solo essay) or all differ (a guest interviewed on a hosted show published by a channel).

**Provenance carries to claims.** A claim's authoritative provenance is a reference to its source record - the `record_id` it already carries - so the record's `provenance` block is the single source of truth and the corroboration logic (independence by provenance root) is unaffected. On top, the digest may denormalise `publisher` + `published_date` + `collection` onto a claim as a RENDER CACHE (recomputed on re-digest, never authoritative), so an article renders "from a 1949 Department of Energy document" without a join. A subject's incident place and date are claims about place and event nodes - never provenance.

## Source properties

Properties that accumulate as data flows through the knowledge graph, derived from data rather than assigned by editors:

| Property | Description |
|----------|-------------|
| **Track record** | How claims from this source's records fare when scored against independent records. |
| **Correction behaviour** | Whether and how quickly the source issues corrections when its claims are contradicted. Tracked as observable events. |
| **Independence** | Institutional and financial connections to the subjects the source covers. Documented factually, not scored as good or bad. |

## Domain versus infrastructure

Two kinds of statement live in a record, and the digest already separates them:
`domain_claims` route to `knowledge.db`, `infrastructure_claims` to
`infrastructure.db` ([digest-format.md](digest-format.md)). 1,825 infrastructure
claims exist today, so this is the primary partition rather than a refinement of one.

- **Domain** - about the subject. What the witness saw, what the document records,
  what was on screen that the words alone miss.
- **Infrastructure** - about the corpus. Which work a passage cites, where a quoted
  clip came from, what a reviewer needed to establish to read the material.

BODY ANNOTATIONS SIT ON THE SAME AXIS, and which side an annotation falls on
determines whether the extraction model should ever see it. A span note is domain
context and is preserved into the pre-digest, because "the witness was pointing at a
map" is information about the subject. A cited work
([ingest-format.md](ingest-format.md#cited-works)) is infrastructural and is stripped,
because which book we have acquired says nothing about UAP and invites the model to
extract claims about acquisition.

Folding the two into one marker family is what makes that undecidable: a consumer
handed one bucket cannot tell context about the material from a fact about our
holdings, and both then reach the model as though they were the same kind of thing.

## Asset, Record and work identity

An Asset is the bytes. A Record is an ordered Selection over Assets. A work is the
intellectual or performed object that may have several manifestations. These are
different identities: two byte-identical downloads are one Asset, a re-encoding is
a different Asset, and an evidenced same-work relation may connect Records over
different Assets without making their bytes or selections identical.

URLs are locators and provenance, not identity inputs. Several live Records may
legitimately share one source URL or Asset when they select different works or page
sets. `also_published_at` records evidenced alternate publication locations; it
does not collapse different selections. Structural split/composition lineage and
one-to-one replacement supersession are likewise separate relations.

An optional `work_provenance: {root_id, evidence}` asserts work identity only when
a human-curated, non-empty evidence list supports it. Absence is unknown. Graph
import may populate `records.work_id` only from this field or replayable curation;
it never falls back to Record id, title, URL, Asset or page boundary.

The decisive reason is corroboration, not tidiness. Claims cite records, and
independence is assessed by provenance root, so filing one recording as two records
makes a single account look like two independent sources agreeing with each other.
That inverts the measure meant to detect single-sourcing: the corpus reads
better-corroborated the more duplicates it holds. An evidenced locator alias closes
the duplicate-acquisition path for the same bytes or work, but URL match alone never
proves that a requested Record Selection already exists.

**An alias is an assertion, so it carries its evidence.** A wrong alias may suppress
needed acquisition or point at the wrong candidate work. Matching an alias therefore
finds candidates only; canonical Selection equality decides whether the Record is
already held. An alias is added on evidence, never title resemblance. Running time
to the centisecond is a useful acquisition fingerprint: a re-encode may match while
a cut-down or re-recording does not, but neither result substitutes for Selection
identity or work-provenance evidence.

## Record unit: whole containers versus selected works

Most acquired Assets initially map to one whole-Asset Record. A large container may
instead yield several Records, and a logical work may compose several Assets. The
choice remains by relevance density rather than size:

- **Whole-container record** - the container's full text is the record body, and sub-parts are located nodes and claims within it. Right when the container is mostly SIGNAL: a UAP FOIA release, a UAP hearing. (The Elizondo resignation letter is not a separate record; it is held-within the FOIA release that reproduces it, located by page range - so a FOIA is a whole-container record even though it "contains" letters.)
- **Selected Record** - the Record contains only ordered complete physical pages or whole standalone images; every source Asset remains archived independently. Right when the container is mostly NOISE, or one work spans several Assets.

The test is **whole when extracting the container is mostly signal, excerpt when it is mostly noise.** Size is a symptom, not the criterion: a short mostly-irrelevant source may excerpt, a long mostly-relevant one stays whole.

A selected Record is anchored by the full ordered list of Asset hashes and canonical
selectors. `content_hash` is the domain-separated hash of that list, never a free-text
scope and never the generated body. The Assets remain at `records/{asset_hash}.{ext}`.
A different selection is a different Record without reacquisition. The exact codec,
selector vocabulary and legacy whole-Asset interpretation are in
[decision 0051](../decisions/0051-asset-record-selection-and-evidence-identity.md).

The whole-versus-selected call is a **human judgement**. Initial acquisition safely
creates a whole-Asset Record. A PDF/image Record explicitly marked
`structure_status: temporary` may later be split or composed in the private
Workbench, which previews and atomically commits exact final outputs from ordered
physical-page/image selectors. Whole audio, video, web and ebook Records are not
structurally edited by this first contract. Unsupported or missing source maps fail
closed; no model infers a scope and no synthetic PDF is made.

## Claim attestation

Each claim carries an attestation level (how close the speaker was to what they are describing) describing the chain between the speaker and the events described:

| Level | Definition | Example |
|-------|-----------|---------|
| **First-hand** | The speaker directly observed or participated in what the claim describes. | "I saw an object hovering over the field." |
| **Second-hand** | The speaker is reporting what someone else directly observed. One step removed. | "My colleague told me he saw an object." |
| **Third-hand** | The speaker is reporting what someone heard from someone else. Two or more steps removed. | "There are reports from personnel who say colleagues witnessed an object." |

Attestation depth affects evidence scoring. A first-hand claim corroborated by another independent first-hand claim is stronger than a third-hand claim with no first-hand backing.

Attestation is **derived from the provenance chain**, not judged by feel ([0044](../decisions/0044-claim-provenance-chain-is-required.md)): `origin_kind: speaker` with an empty relay is `first_hand`; one remove is `second_hand`; two or more removes is `third_hand`; `unattributed` has no evidential stance and omits it.

**Grade by the whole chain, not by the last mouth it passed through.** A speaker naming their immediate contact does not make a claim second-hand if that contact was themselves relaying someone else - count the removes. An assertion reaching the speaker as a forwarded email from an anonymous source is `third_hand`, however confidently the speaker names the person who forwarded it.

## Claim text and load-bearing attribution

A claim's `text` normally states the bare fact, with the speaker held in the structured `speaker` field - naming the relayer in the text would turn the graph into a pile of quotations rather than portable facts. That rule holds **only where the speaker is a conduit** for something that stands independently of who relayed it.

It reverses where the attribution is load-bearing - `origin_kind: anonymous`, or `type: hearsay`, or an attestation of `second_hand`/`third_hand`. There, **the attribution goes inside the `text`** ([0044](../decisions/0044-claim-provenance-chain-is-required.md)).

The reason is not stylistic. For such a claim, the proposition is not a fact about the world and is not what the source establishes; the fact about the world is *that someone asserted it*. Stripping the attribution does not tidy the claim, it changes what the claim says - from a true statement about an assertion into a false statement about reality. `text` is what flows into articles, so a claim must be safe read alone; safety cannot depend on every consumer, forever, remembering to check a sidecar field.

## Only sincere assertions are claims

Exhaustive extraction means never skimming and never curating for importance. It does not mean literalising every sentence spoken. A claim is extracted only where the source **sincerely asserts** a fact. The following are not claims, even though the words appear verbatim in the source: jokes, deadpan, irony and running bits (comedic self-description is not biography, and deadpan gives no signal a joke is underway); hypotheticals and rhetorical questions; statements quoted in order to be rejected; and hyperbole or figures of speech, which are never converted into measurements.

Omitting a joke costs little. Asserting one as fact manufactures a false fact, which is the worst output this system can produce.

## Record classification

A record's classification describes its relationship to the events it covers - distinct from a claim's attestation, which describes the speaker's proximity to what they assert:

| Classification | Definition | Examples |
|----------------|-----------|----------|
| **Primary** | First-hand account or original data - direct observation or participation. | Witness testimony, sensor data, official investigation reports, Freedom of Information Act releases, scene photographs |
| **Secondary** | Reporting on or analysis of primary records. | News articles based on interviews, documentaries, analytical papers |
| **Tertiary** | Commentary on secondary records. | Opinion columns, podcast discussions of news articles, social-media commentary |

A single record may mix classifications: a news article can carry a direct witness quote (primary), the journalist's summary (secondary), and editorial framing (tertiary). Record classification (primary/secondary/tertiary) and claim attestation (first/second/third-hand) are related but distinct - a primary record (an original Freedom of Information Act document) may contain second-hand claims (an official reporting what a witness said).

## Claim types

Each claim carries a type describing the nature of the assertion. See [node types](node-types.md) for the full list: observation, testimony, hearsay, opinion, measurement, administrative.

Claim type is orthogonal to attestation level. A claim can be first-hand opinion, second-hand testimony, or third-hand hearsay about a measurement.

## Provenance chains

Every claim has a provenance chain (the path a claim took from its original source to the knowledge graph). Provenance chains are used to determine genuine independence when assessing corroboration.

Two claims corroborate each other only if their provenance chains do not share a common root. Ten outlets all reporting the same press release is one source, not ten.

The chain is a **required** field on every claim ([0044](../decisions/0044-claim-provenance-chain-is-required.md)) - the extraction schema will not accept a claim without it, so "where did this come from?" is a question the model must answer rather than one it may skip:

```yaml
provenance_chain:
  origin_kind: anonymous        # speaker | named | anonymous | document | unattributed
  origin: "a person claiming to work inside the Defense Intelligence Agency"
  origin_ref: dia-email-source  # optional; stable only within this record
  relay:                        # ordered, origin -> speaker; empty when the speaker IS the origin
    - "an email"
    - "an intermediary known to the speaker"
```

| `origin_kind` | The root of the chain |
|---------------|----------------------|
| `speaker` | The speaker originated it - they observed it, did it, or hold it. `relay` is empty. |
| `named` | An identifiable person, organisation, or document. It is a node, and must also appear in `refs`. |
| `anonymous` | An unnamed or unidentifiable source. **It cannot be a node** (see [node types](node-types.md)), so this field is the only place it can survive. |
| `document` | A document or record the speaker is reading from or citing. |
| `unattributed` | The source asserts it with no attribution offered - ordinary narration. |

`origin_kind` is what corroboration keys on. An `anonymous` root matters most: because an anonymous actor can never be a node, dropping the chain does not merely lose detail - it silently promotes an anonymous assertion into an institutional one ("an anonymous person claiming to work inside the Defense Intelligence Agency said X" collapses into "the Defense Intelligence Agency said X").

`origin_ref` distinguishes recurring anonymous sources within one record without inventing a global identity. Different refs in one record establish different roots there. Matching refs across records establish nothing: using `(record_id, origin_ref)` as a corpus-wide identity would turn several records relaying one anonymous source into several independent roots. Missing `origin_ref` means not distinguished, never a licence to count each claim or record independently.

This claim-level chain is distinct from the record's `provenance` block ([0043](../decisions/0043-canonical-provenance-block.md)): provenance says where the **document** came from (publisher, dates, URL); the provenance chain says who, **inside** the document, asserted the claim and through whom it reached the speaker. A claim has both.

## Pipeline outputs

Each pipeline stage has a named output:

| Stage | Output | Shareable | Description |
|-------|--------|-----------|-------------|
| Ingester | **Ingest** | No (copyright) | The record converted to structured text with metadata, plus any extracted media (images today; figures from PDFs and video keyframes later). Contains the actual content. |
| Digester | **Digest** | Yes | Claims, nodes, and provenance extracted from one ingest. No copyrighted content. Planned: N model-variants reconciled into one derived canonical digest per ingest; only the canonical is assimilated ([decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md)). |
| Assimilator | **Knowledge graph** | Yes (derived) | The unified SQLite graph built from all digests: cross-record entity resolution, provenance, scoring, embeddings. Derived data, rebuildable from the digests. |
| Assembler | **Article** | Yes | Readable prose assembled from knowledge graph data in a specific language. Public-eligible images from ingests are copied into the assembler's output for serving on the site. |

## Storage

The source of truth for the knowledge graph is the collection of digests in the digests repository. These are human-readable, version-controlled, and reviewable.

The SQLite database (a lightweight file-based database) is built and maintained by the assimilator, which imports the digests into the graph (see [assimilator.md](assimilator.md)). It serves as the query and distribution format - downloadable, torrentable, and verifiable - but is derived data, not primary. If deleted, it can be rebuilt from the digests. Embedding vectors are stored separately from core data to keep the primary download small.

The assimilator MAINTAINS the graph, it does not merely import it. Import is
mechanical. Maintenance separates semantic agreement, evidence identity and
provenance independence. Claims with anchors overlapping on one physical Asset
page in the same exact page-text frame belong to one evidence unit and never corroborate or count twice, including overlap across
different Records. Disjoint selections are not automatically independent:
independence requires evidenced distinct work or assertion-origin roots, and
unknown lineage adds no independent count. Separate documents inside one bundle
inherit the shared Asset/container root unless Record metadata establishes
distinct roots. See [decision 0051](../decisions/0051-asset-record-selection-and-evidence-identity.md).


## A repair applied to one side of a seam

Four faults this project has hit share one shape: the correct behaviour existed, a
few lines or one directory away, and was not applied on both sides of a boundary.

- The name comparison applied a guard; the alias comparison beside it did not. Result:
  118 aliases naming other events accumulated on one node, and a lookup for
  "1947 Roswell UFO incident" returned a 2004 Navy encounter.
- The whole-name comparison applied the guard; the place-component comparison did not.
  Result: fifteen Californian cities became aliases of a Bolivian town, and claims
  about Santa Monica were filed under Bolivia.
- Country names were normalised on incoming data and not on stored nodes, so the next
  import minted the duplicates the normalisation existed to prevent.
- Stale briefs were pruned in the source directory and not in the published one, so
  every merge cleaned up one copy and left the consumer's pointing at a node that had
  moved.

The failure is not carelessness and is not caught by testing the repair: each fix works
on the side it was applied to. It is caught by asking, of any correction, WHERE ELSE
THIS COMPARISON, NORMALISATION OR CLEANUP HAPPENS - and treating a boundary between two
copies, two directories, or two code paths as the place to look first.

The general form: a system with two representations of the same thing needs every rule
applied to both, or the rule creates a divergence rather than removing one.
