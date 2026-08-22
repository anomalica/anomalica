# Ingest Format

The ingest format is the interchange format between the ingester and the digester.
Each record - the original artefact, in whatever format it arrived - is transcribed
into exactly one ingest, a `.md` file in this format.

NAMING. A **record** is the original: the PDF, the audio file, the ebook, the
captured web page. An **ingest** is the markdown we transcribe it into. They are
not the same object and must not share a word: an ingest has its own hash, its own
character offsets, and its own edit history, while the record it came from is
immutable. Code and directories that call an ingest a "record" predate this and are
being corrected; [data-model.md](data-model.md) holds the canonical terms.

See [architecture decision record 0019](../decisions/0019-record-interchange-format.md) for why this format was chosen.

The canonical machine-readable field list is [`reference/format-specs.yaml`](../reference/format-specs.yaml) (`types.ingest`); this document is its narrative companion (body grammar, parser behaviour, examples).

## Structure

A record file has three parts:

1. **Frontmatter** - YAML (a human-readable metadata format) block at the top, fenced with `---`. Document-level metadata.
2. **Content** - markdown text. The actual content as it naturally reads.
3. **Annotations** - either block-level (YAML inside HTML comments) or inline (`{{YAML}}`).

All annotations use YAML throughout - the same data format as the frontmatter. Block annotations for structural markers (page boundaries, speaker turns, images). Inline annotations for mid-sentence markers (redactions, illegible text, actions).

The first `---` fenced block is always the frontmatter. All HTML comments in the body are annotations - the ingester does not produce any other HTML comments. Text between annotations is content.

**The body in this file is not the space claim spans index.** A digest's claim `location` counts characters in the **materialised pre-digest** - this body after deterministic model-prep (whitespace collapsed, annotations stripped, irrelevant regions removed, timestamps dropped), produced by `anomalica_common.pre_digest.materialise()`. Resolving a span against the raw body below lands consistently off, in one direction, growing with position. To resolve a claim to its text, materialise first; the frame and its rules are specified in [digest-format.md](digest-format.md#a-span-must-declare-its-frame).

This is stated here rather than only in the digest spec because the mistake is made by consumers reading *records*, who have no reason to open the digest format at all. A frame mismatch is invisible when made: every figure stays internally consistent, monotonic and reproducible, and because the error can only run one direction it produces a clean 100%-positive drift that reads as strong evidence of a systematic bug. One such investigation cost about five hours and produced a corpus-wide table of 1,589 "drifted" claims across seven books, all of which were correct.

**There is no `---`-fenced annotation form.** `---` closes the frontmatter and never opens anything again: every subsequent occurrence is ordinary body text - a markdown thematic break, which prose uses freely as a section divider. A parser that treats a bare `---` in the body as opening a fence will discard everything to the next one, and it will do so **silently**, because the result is still a well-formed record that simply contains less. One 622KB book parsed to 88KB (14.2%) that way, yielding 9 claims and a digest written at exit 0.

**The fix is in the reader, never in the body.** The ingester used to rewrite a standalone body `---` to `***` so a naive reader could not trip. That was removed 2026-08-20: it repaired the document instead of the parser, and in a corpus whose whole claim is faithful reproduction, silently substituting a character the source printed is the worse failure. All ten parsers in the pipeline are already correct - six non-greedy regexes and four `split("---", 2)` calls, every one stopping at the FIRST closing fence - so the collision cannot occur. A reader splits once at the top and never looks again. If one is ever found that does not, fix that reader.

The rule for recognising an annotation is therefore positive and total: **a block annotation is an HTML comment whose content parses as a YAML mapping with a known annotation key; nothing else is an annotation.** Anything failing that test is content. A consumer never needs to infer a delimiter, and a construct absent from this document is not one a parser may invent.

## Frontmatter

Required fields:

```yaml
---
schema: anomalica/record/1
title: "Document title"
source_type: pdf
provenance:
  publisher: "..."
  published_date: 2023-07-26
  source_url: "https://..."
---
```

Every frontmatter field - its type, whether it is required, which source types it applies to, and a description - is listed once in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.ingest`. That YAML is the canonical field list; this document does not repeat it. The hash fields (`content_hash`, `source_hash`) are explained in narrative under [Store](#store); the body-annotation sub-fields (image, chapter, snapshot roles) are specified in their sections below.

### Provenance

Every record carries a `provenance` block - the canonical home for source-origin metadata, consolidating what used to be scattered across separate top-level fields (`publisher`, `source_url`, `date_published`, `source_id`, `creators`, and the rest). One block, one source of truth ([decision 0043](../decisions/0043-canonical-provenance-block.md)).

```yaml
provenance:
  collection: "war.gov UFO reading room"      # curated grouping this record belongs to
  publisher: "Department of Energy"           # issuing body / channel / author-org (not the hosting platform)
  creators: ["Edward Teller"]                 # human author(s) / host(s), person names in natural order
  published_date: "1949-03"                   # the source's own publication or upload date (ISO 8601, may be partial)
  acquired_date: "2026-07-11T09:00:00Z"       # when Anomalica brought the source in
  source_url: "https://www.war.gov/..."       # canonical URL of the original
  fetched_url: "https://web.archive.org/..."  # the URL actually retrieved, when different from source_url
  also_published_at:                          # other URLs this same record is published at (see below)
    - "https://www.youtube.com/watch?v=..."
  source_file: "los-alamos-1949.pdf"          # original filename, for a source ingested from a local file with no URL
  identifiers:                                # native source identifiers, keyed by scheme
    virin: "..."
    youtube: "aB8zcAttP1E"
  description: "..."                           # the source's OWN blurb, verbatim - never AI-generated
```

Each source type fills what it has; a sub-field with no value is OMITTED, never set to null. Origin-unknown is simply the absence of `source_url`, `fetched_url`, `source_file`, and `identifiers` - there is no separate marker (this replaces the old scalar `provenance: unknown`).

**`also_published_at` is a dedup key, not a citation list.** One artefact is often
published in more than one place - an episode on the publisher's own channel and a
repost on another. Those uploads are not separate records: they are one record
reachable at several URLs. When duplicates of it have been ingested and are then
merged, the surviving record keeps a single `source_url` and lists the other
listings here. Every consumer that decides "do we already hold this?" MUST match
against these as well as `source_url`: re-encountering an alias otherwise ingests it
afresh and recreates the duplicate the merge removed. Aliases follow the record that
carries them - on a `superseded_by` record they are retired with it and match
nothing.

It does not confer independence, and the two questions are separate. Independence
is about who stands behind a claim, counted by provenance-chain root
([0044](../decisions/0044-claim-provenance-chain-is-required.md)); a record
answering to more URLs never raises it.

Two boundaries are load-bearing:

- **Source facts, not subject facts.** Provenance is about the SOURCE - who issued it, when it was published, where to find it. A subject's incident place and incident date are NOT provenance; they are extracted as claims about place and event nodes, so they stay inside the scored, corroborated evidence model. `published_date` is strictly the source's publication or upload date.
- **Copyright is not mirrored here.** `copyright` (and `copyright.status`) is the single authoritative copyright field, top-level; provenance carries no `license`. `classification` likewise stays top-level. The `description` is the source's verbatim blurb, never AI-written - and reproducing a `licensed` or `restricted` source's blurb is itself reproduction, so it is omitted or truncated for those sources, exactly as the source text is gated.

#### The work and the copy are different things

A redistributed source has two publication layers, and recording only one files the redistributor as the originator.

```yaml
publisher: "WXIA-TV"            # the WORK - who issued it
date_published: "1988"
posted_by: "Eyes On Cinema"     # the COPY - the channel this copy came from
posted_date: 2026-08-13         # when that channel posted it
```

`posted_by` and `posted_date` describe **the copy the fetcher actually saw**, which is all it can observe. `publisher` and `date_published` keep their existing meaning - the work - and the handler no longer writes them from channel metadata. On a fresh ingest they are simply **absent** until someone identifies the work, which is the same not-evidenced convention as [date precision](#date-precision-record-only-what-the-source-evidences). Where the channel *is* the originator, all four are filled and the pairs match; there is no special case.

`posted_date` is also distinct from `acquired_date`: the channel posted the copy, we fetched it. Different actors, different dates.

`container_title` records the journal, book, or programme a work appeared in - "Topological Foundations of Electromagnetism" for a chapter, "Scientific Reports" for a paper, "11Alive News Extra" for the WXIA segment. One field for all three, following CSL's `container-title`: the venue is the same relation whether it is bound, published, or broadcast, and splitting it into book-specific and journal-specific fields buys nothing. It is a different axis from `posted_by` - the venue **of the work**, against the channel that reposted **a copy**.

**The attribution is false on its own terms.** A 1988 WXIA-TV segment records Eyes On Cinema as its publisher and 2026 as its publication year; a 1967 recording of James McDonald's Australia tour is filed as published 2026-08-11. Live: 15 records attributed to one archival channel, and a single 1997 Art Bell broadcast filed as 8 records.

**It does not, however, drive the independence count - and fixing it does not fix that.** Measured 2026-08-18: `provenance_root` reads four columns (`speaker_id`, `record_id`, `origin_kind`, `origin`), all on `claims`. Publisher lands in `records.metadata` and nothing in the independence path opens it. The real inflation is a **fallback to `record_id`** where `origin_kind` is `speaker` or `unattributed` and no speaker resolved - 7,165 of 27,966 claims, **26%**, across 58 of 80 records. So N re-uploads of one work are N roots for a quarter of the corpus's claims, regardless of publisher, and this change moves that in neither direction.

Stated plainly because the tempting misreading is that the provenance fix handled it. It did not; the fallback is separate work.

**An absent publisher is an unknown root, never a distinct one.** This is a rule for whoever builds the count, not a description of a wire that exists today. Two records with no publisher are two *unknowns*, and treating each as its own root inflates independence exactly as a false publisher would - more quietly, because it reads as missing data rather than as a bug.

**`posted_by` is not a grouping key.** The 8 Art Bell records *are* one work and share a `posted_by`; the 15 Eyes On Cinema records are 15 *different* works and also share a `posted_by`. A key that groups by uploader cannot tell eight parts of one broadcast from fifteen unrelated segments off one channel. Work identity needs `publisher` plus `date_published` - the pair that stays absent until a human supplies it - so re-uploads need identification before any mechanical grouping helps.

**Absence has to be tolerated because identification often fails.** A 1988 WXIA-TV news segment in the corpus never names its station in the audio: an extraction pass yields "a local television news segment, Georgia, c. 1988, reported by Bruce Erion" and stops. "WXIA-TV, 11Alive News Extra" came from outside research. A `publisher` that defaults to whatever the fetcher saw would have filled that gap with a falsehood rather than leaving it open.

**Roles stay out of frontmatter.** No `creators` list with role labels, no confidence or basis marker, no nested `copy` block - all three were considered and rejected. An anchor, a reporter, a producer are roles, and [node-types.md](node-types.md) already holds that a document node is the work while a producer is a source in a role, not a type. The ratified precedent is the [`release`](#release-and-declassification) block: the declassifying officer becomes a node through a digester administrative claim, never directly from frontmatter. A reporter arrives the same way, and the transcript supports it - the WXIA segment has Kelly Morgan handing over ("Bruce Erion tells us about an Athens man and his close encounter. Bruce?") and Erion signing off ("John, Kelly."), so anchor-versus-reporter is extractable with real quotes. A basis field would have been a second, weaker evidence model sitting beside `attestation` and `provenance_chain`.

**A described author is bracketed, exactly like a described speaker.** `creators` holds person names, and consumers build person nodes from it, so a value that describes rather than names must say so: `[senior US intelligence officer]`, not `Senior U.S. Intelligence Officer (Anonymous)`. The unbracketed form becomes a person, and merges with any other document describing its source the same way - the pollution the brackets exist to prevent, arriving through a field rather than a speaker comment. The value is usually faithful rather than invented: an extraction model transcribing what the title page said, which is the right instinct spelled the wrong way. Same notation, same rule, wherever a person can appear ([Speaker change](#speaker-change)).

**A withheld author is `[redacted]`, not an omission and never `{{redacted}}`.** Omitting the field says no author was given; `[redacted]` says the document named one and the name was withheld, which is a different and evidenced fact about the document. `{{...}}` is body-annotation syntax and must never appear in a frontmatter value - a consumer reading that list gets the literal string `{{redacted}}` as somebody's name, and it is the same class of leak as a classification marker reaching the digester: a construct escaping the body it was defined for.

**Correcting existing records is not mechanical corpus-wide.** Moving `publisher` to `posted_by` and clearing `date_published` is safe only where the channel is a redistributor; applying it where the channel is the originator would delete a true publisher. Correct the identified archival channels, leave the rest.

#### Date precision: record only what the source evidences

**A date carries the precision the source supports and no more.** `2020`, `2020-08`, and `2020-08-09` are all valid values; the day is *omitted* when the source does not state one, never guessed to fill the field.

This is already the contract elsewhere - a claim's `date` accepts `2017` ([digest-format.md](digest-format.md#claims)), and `provenance.published_date` is specified as "ISO 8601, may be partial". Only the flat `date_published` demanded a full date, and demanding one is what produces fabrication: given a source whose evidence is "August 2020", an extractor obliged to emit a day emits a plausible one. One record carried `2020-08-09` where its 6-page scan states no date at all and its filename says only `...Persian-Gulf-August-2020`. Nothing in the record distinguished that invented day from a CIA report's `26 December 1973`, which is printed on the page.

The principle is the one already applied a level up - a valueless field is omitted, never nulled - applied inside the value itself.

**Emit a reduced-precision date as a QUOTED string; a full date bare.** `date_published: 1988` parses as the integer 1988, and across the corpus `date_published` has been read as four different Python types - `date`, `datetime`, `str` and `int` - purely from how the value was written. So `2020-08-09` is written bare and reads as a date, while `"2020-08"` and `"1988"` are quoted and read as strings. This applies to every date field carrying reduced precision, `posted_date` included. **Precision is the evidence marker**: a record reading `2020-08` is telling you the day was not evidenced, and needs no separate flag to say so.

Two consequences that must be honoured downstream, or the fabrication simply moves:

- **Sort by the earliest instant the value can denote**, with precision as the tiebreak: `2020` sorts at 2020-01-01, `2020-08` at 2020-08-01. Deterministic and total, so a reduced-precision value never needs padding to become sortable.
- **Display exactly the stored precision.** `2020-08` renders "August 2020", never "1 August 2020" and never "8 August 2020". Coercing a partial date to a day at the render layer reintroduces the invention one stage later, where it is harder to see and reads to a reader as a fact about the document.

**Existing day-precision values on scanned sources are not trustworthy** and cannot be audited automatically - establishing whether a stored day is evidenced means reading the source. There is no backfill: records carry honest precision as they are re-ingested, and the cohort extracted before this rule is identifiable by `date_extracted`. Until then a day on such a record is not authoritative and should not be rendered as though it were.

Two provenance sub-fields carry *how a source came to exist and how it became available*. They are not copyright, not medium, and not publisher credibility - the same body produces sources that differ on both.

```yaml
provenance:
  audience: internal        # internal | public - who it was written FOR
  disclosure: foia          # published | declassified | foia | subpoena | leaked | unknown
```

**`audience` is the evidential axis.** A memo written for internal circulation by people who expected it to stay secret has no performative incentive: it was created to inform a colleague, not to hold a position in front of an audience. A report written for publication by an institution with a public stance is a different kind of artefact, and historiography has always weighted the two differently. Today a FOIA-released 1952 memo and a 2024 agency report are both just "a government document" to this model, which loses the distinction that matters most about them.

**`disclosure` is the authenticity axis, and it must not be folded into the first.** An internal memo released under FOIA and an internal memo that leaked share `audience: internal` and differ enormously in chain of custody: the FOIA release is attested by the holding agency, the leak is attested by nobody. Collapsing them would let an unauthenticated document inherit the credibility of a compelled release, which for an evidence platform is the more dangerous error of the two.

**Apply the principle to the whole corpus, not only to institutions.** The property that makes an internal memo valuable is the *absence of a performative incentive at creation* - and by that test a monetised podcast interview, produced for an audience and rewarded by its reaction, carries a stronger performative incentive than most agency reports do. This axis is not "official bad, internal good": it is a statement about who the author was performing for, and it indicts a large part of a corpus built on interview material as readily as it does an institutional report. A model that down-weights official output while treating podcast testimony as neutral has not applied the principle; it has swapped one institutional prior for another.

Which is also why **an official determination is held, never used as a reference standard.** Recording that a body investigated a case and classified it under its own scheme is valuable precisely because it can be *compared* against the declassified internal record - "the public report called it a balloon; the memo released under FOIA says otherwise" is the comparison this platform exists to surface. Folding that determination into our own confidence number would destroy the comparison and import the body's institutional priors as ground truth. Hold both; weight them by these fields; never let one define the scale.

A claim's authoritative provenance is a reference to its source record (the `record_id` it already carries); the digest may additionally denormalise `publisher` + `published_date` + `collection` onto a claim as a render cache, so an article renders "from a 1949 Department of Energy document" without a join. The cache is derived and refreshed on re-digest; the record's block is authoritative. See [data-model.md](data-model.md).

### Document type

`source_type` records **how a source was acquired** (`pdf`, `audio`, `video`, `web`, `ebook`, `image`). `document_type` records **what it is** - the form of the artefact, independent of how it reached us.

```yaml
source_type: web
document_type: email
```

A bare image (`jpg`, `jpeg`, `png`, `webp`) is a photographed or scanned **document**, not a new container: it runs the PDF handler's vision path, is hashed as source bytes like any other scan, and carries `pages: 1` with a single `file_page: 1`. It is the clearest case of the split - a photographed slide and a scanned PDF of the same memo differ in `source_type` and share a `document_type`. TIFF and HEIC are deferred: browsers cannot render them, so they need a decoded display derivative in `snapshots[]` first.

The two are orthogonal, and they come apart immediately. The same email is `web` when scraped from a publication, `pdf` when it arrives inside a FOIA release, and RFC822 when downloaded as `.eml`. Making email a sixth `source_type` would therefore make every email inside a PDF invisible to it - and the corpus already holds that case.

`document_type` is an open set - `email`, `letter`, `memo`, `report`, `statute`, `affidavit`, `transcript`, `interview` - naming the artefact's form, never its subject. "Document" carries the sense it has in the node taxonomy: an information artefact whatever the medium, so a recorded interview is as much a document as a memo is. It exists to drive extraction, not to classify for its own sake.

**Emit it only where it is derivable without inference; otherwise leave it absent.** The test is whether the artefact *states* its own form, not whether it resembles one. RFC822 headers parse or they do not, and a page headed `MEMORANDUM FOR RECORD` says what it is - both derivable. A photographed page that merely *looks* like a memo is not, and asking a model to choose between `memo`, `letter`, `report` and `slide` from appearance is asking for a judgement it cannot ground, which returns a fluent value indistinguishable from a correct one.

Absence is the not-evidenced marker here as everywhere else in this format, and it is the useful state: **a missing `document_type` invites a human to look, while a wrong one does not.** A reviewer sets it where it matters; as with other reviewer corrections, the who and when ride on the git commit rather than an inline stamp.

This also keeps the field one kind of thing. Were derived and guessed values to share it with no way to tell them apart, a consumer would hold two different classes of value under one name - the shape that has bitten this format repeatedly - and the fix would be a basis marker, which is worse than simply not guessing.

**It describes the WHOLE record, so it never applies to a container.** FOIA release 18-F-0324 is a `pdf` whose body contains many emails; its `document_type` is not `email`, because the record is the release. Correspondence inside a container is marked in the body instead, with [message boundaries](#message-boundary). A record-level `document_type: email` asserts the entire record is one message - an `.eml`, or a page publishing a single message.

**Not to be confused with the nested `document_type` in 15 legacy records.** Those carry a `provenance:` block of war.gov reading-room catalogue metadata whose `document_type: AUD` is *war.gov's own* cataloguing code, a foreign vocabulary that happens to share the word. Only the top-level field is this vocabulary. The two do not collide mechanically - different nesting levels - but a reader meeting both in one corpus will reasonably assume they are one scheme, so the legacy code should be namespaced as source-native metadata when that block is reconciled.

### Email headers

Where `document_type: email`, the RFC822 headers are parsed deterministically - the standard-library `email` parser, no model involved - and split between two homes.

The normalised, project-wide facts go to the record's ordinary date and author fields, so every consumer reads them without knowing the format:

| Field | Taken from | Home once [0043](../decisions/0043-canonical-provenance-block.md) lands |
|---|---|---|
| `date_published` | The `Date` header. Authoritative. | `provenance.published_date` |
| `creators` | The `From` participant, name in natural order. | `provenance.creators` |
| `email.message_id` | The `Message-ID`. | `provenance.identifiers.message_id` |

**Write these to the flat fields that exist today, not to 0043's block.** That block is accepted but unimplemented - no handler emits it, and no record carries `provenance.published_date` or `provenance.creators`. Email fields ride the 0043 migration with every other record type when it happens; they are not special-cased ahead of it, and nothing writes into a block that nothing produces or reads. `message_id` sits in the `email` block until that migration gives it a home in `identifiers`.

The format-native structure that provenance cannot represent goes in an `email` block:

```yaml
email:
  from: {name: John Podesta, address: john.podesta@gmail.com}
  to: [{name: Bob Fish, address: robertbfish@earthlink.net}]
  cc: []
  subject: 'Re: Leslie Kean book comment'
  in_reply_to: '<003501d05799$...@earthlink.net>'
  references: ['<...>']
```

It does not repeat `published_date` or `creators` - it carries what those cannot, the addresses and the threading. Recipients matter because an email is a dated communication between named parties, which is a real relationship for the graph rather than "a page that happened to mention some names".

Taking the `Date` header as `published_date` is a correction, not a refinement. A scraped email page yields whatever date the surrounding HTML exposes: one Podesta record landed on 2000-01-01, lifted from a date-picker widget in the page's own JavaScript, fifteen years from the message's actual date.

**`dkim_verified` is optional, and absence is not failure.** Set it only where the source itself carries a `DKIM-Signature` that was checked. Absent means *no signature was present in this copy* - never *verification failed*. A Gmail-sent copy legitimately carries no signature while a received copy of the same message does, so collapsing absent to false would mark genuine unsigned copies as suspect and hand evidence-scoring a penalty nothing earned.

### The archived original

Every record whose source was archived carries `archived_ext` - the bare extension of that archived object, which lives at `sources/{content_hash}.{archived_ext}`. That pair is the whole address: consumers build it to fetch or play the source (the workbench serving a reviewer the audio behind a transcript, for instance).

**The extension is not derivable, and must never be re-derived from `container`.** `codec` and `container` under `processing.source` describe the STREAM; the extension is a property of the FILE. yt-dlp writes `.opus` while reporting `container: ogg`, and a file downloaded as `.ogg` reports an identical stream - so the same metadata legitimately backs both extensions. Before this field existed, 76 of 122 records said `container: ogg` against a `.opus` file on disk, and a container-derived URL 404'd for the majority of the library. There is no glob on the CDN, so a wrong extension is simply a miss. Write the extension down; never infer it.

`archived_ext` is also **distinct from `source_file`**, which is the ORIGINAL filename of a local-file ingest. They describe different files and may legitimately disagree: a video ingested from `interview.mkv` and archived audio-only carries `source_file: interview.mkv` alongside `archived_ext: opus`. That is correct, not an inconsistency - do not reconcile them.

### The waveform peaks sidecar

An audio or video record may carry a peaks sidecar at `sources/{content_hash}.peaks.json` (schema `anomalica/peaks/1`) - an amplitude envelope of the archived original, computed once at archive time. A reviewer aligning a word's timestamp needs to see the sound's onset; the envelope is what draws that waveform.

```json
{"schema": "anomalica/peaks/1", "hex_hash": "5a05136d...",
 "bins_per_second": 100, "duration": 470.04, "peaks": "<base64>"}
```

One unsigned byte per bin, base64. Each bin is the **maximum** absolute sample in its slice, never the average - an average flattens the attack at a word's start, which is the only feature the waveform exists to show. The reduction is single-sourced in `anomalica-common` (`peaks.py`) because two components run it and a drift between them is invisible: nothing errors, the waveform just stops matching the audio.

**`duration` is derived from the decoded audio, and it is the authoritative span.** A consumer must map the peaks onto THIS value, not onto a player's or media element's duration: `len(peaks) / duration == bins_per_second` holds by construction here and nowhere else. A YouTube player rounds its reported duration to the whole second (4685 for a file that is really 4684.89), and an `<audio>` element measures the container rather than the decode - either will drift the x-axis by enough to misplace an onset. Do not map onto the record's frontmatter `duration` either; that is the file's length, a different quantity, and it was wrong on every record in the corpus until 2026-07-17.

**Access: peaks follow the TRANSCRIPT's rule, not the original file's.** This is the one place where a derivative is served more openly than the thing it derives from, and it is deliberate (Mark's ruling, 2026-07-17):

| Object | Open for |
|--------|----------|
| The archived original (`sources/{hash}.{archived_ext}`) | `public_domain`, `open_licence` |
| Its peaks (`sources/{hash}.peaks.json`) | `public_domain`, `open_licence`, **`publicly_accessible`** |

So for a `publicly_accessible` source the audio stays gated while its peaks are served openly. The reasoning: peaks are in the same disclosure class as the transcript body, which is already public for those sources - the sources are publicly accessible already, ours are just more accurate transcripts, and an envelope is a weaker derivative still (100 amplitudes per second, no words, cannot reconstruct the audio). Everything outside both lists - `licensed`, `restricted`, unknown, absent - fails closed.

**Do not collapse these two allow-lists.** They look like a copy-paste divergence and are not. Merging them either withdraws the ruling (no waveform for the majority of the library) or serves the copyrighted audio itself. Any router must decide per object kind, never once per record.

### Release and declassification

Government documents carry their provenance **stamped on the page rather than typed in it** - a red declassification overlay, a handling caveat, a release-control footer. For a project whose claim is documented provenance, that footer *is* provenance: it names the releasing authority, the control number, who it was released to, and when.

```yaml
release:
  declassified_by: "Richard A. Harrison"      # the officer, as a person name
  declassified_by_title: "MG, USCENTCOM Chief of Staff"
  control_number: "USCENTCOM 26-0028"
  released_to: "AARO"
  release_date: 2026-03-16
  handling: ["FOUO", "PA applies"]
  markings:                                    # verbatim, as stamped
    - "Declassified by MG Richard A. Harrison, USCENTCOM Chief of Staff"
    - "FOUO/PA applies"
    - "Approved for Release to AARO"
```

**This is the evidence behind [`provenance.disclosure`](#audience-and-disclosure).** That field says *how* a document became available (`declassified`, `foia`, `published`); this block is the documentary proof of it, and the two must agree. It is a separate block rather than more `provenance` fields because it records a **status transition** with its own actor and date - a 1952 memo has an origin (creators, published_date) and, seventy years later, a release. Different events, different people.

It is also distinct from [`classification`](#frontmatter), which records what the document *was* marked. Classification is the prior state; release is how it left it.

**`markings` is required whenever the block is present, and may be empty.** That is what makes absence testable: `markings: []` asserts *examined, none found*, while an absent `release` block means *not examined*. Without that distinction a consumer cannot tell a document carrying no release provenance from one whose provenance was dropped at extraction, which is the absence-read-as-a-value failure this format has met in several places.

The absent case is narrow, and narrower than it first appears: a record extracted before this block existed, or a source type with no page furniture to carry stamps. **It is not "scanned PDFs".** The PDF handler reads every page as an image, so a scan without a text layer is examined exactly as a native-text document is - the officer's name comes off an image-only stamp the same way. A text-layer tool such as `pdftotext` will report those documents as empty, which makes them look unexaminable when measuring from outside the pipeline; that is a property of the measuring instrument, not of the handler.

**Sequence numbers are per-page, not per-record.** A Bates-style `000001` in a release footer numbers *that page* within the release, so a forty-page record has forty of them and a record-level scalar would be wrong. Carry them on the [page boundary](#page-boundary) annotation where they belong, or not at all.

**The person becomes a node through a claim, not through frontmatter.** The ingester records what the page says; the digester decides whether to emit an administrative claim ("Harrison declassified this document on 2026-03-16"), and the person node follows from that claim by the ordinary route. No new node-creation path, and the releasing officer earns a page only under the usual [page-worthiness](node-types.md#page-worthiness-which-node-types-earn-a-page) floor - which most will never meet, correctly. The value is cumulative: an officer appearing across many releases is a real pattern about who released what, and it only exists if the individual records carry the name.

**Extraction must stop treating these as furniture.** A release footer is literally a footer and a red declassification stamp reads as a watermark, so a prompt instructing "skip page furniture: page numbers, running headers, running footers, watermarks" removes them correctly by its own lights, while a markings rule covering only classification banners gives it nothing to catch them with. The instruction has to name release provenance positively; the erratic result otherwise - one document keeping `USCENTCOM` while dropping `Declassified` from the same page - is the signature of a rule that does not mention the thing at all.

### Text quality

A knowingly variable-quality corpus is acceptable; an *unlabelled* one is not. A record whose text is damaged is usable as long as its condition is stated, so every claim drawn from it can be discounted knowingly. The `quality` block states that condition.

```yaml
quality:
  replacement_chars: 0        # U+FFFD count in the body
  substitution_score: 0.0     # OCR proper-noun inconsistency
  page_anchors: 412           # printed_page marker count
  chapter_markers: 38         # count of <!-- chapter: --> annotations
  chapter_titles: 36          # count of <!-- chapter_title: --> annotations
```

**`chapter_markers` and `chapter_titles` are both counts, and the pair is the signal.** Markers is how many chapters were found; titles is how many carry a real title. `titles < markers` means chapters whose titles the extractor did not recover - *Hair of the Alien* at 28 markers against 1 title is a book whose titles were lost, which is precisely the defect an ebook re-extraction chases.

`titles > markers` is legal and not an error: an unnumbered section - front matter, a part divider - carries a `chapter_title` with no `chapter` annotation. *American Cosmic* reads 7 markers against 18 titles for that reason. Only the shortfall direction is damage.

`chapter_titles` was specified here as a boolean ("chapters carry real titles") until 2026-08-16. Nothing on disk was ever a boolean; all 17 ebooks carry integers. The drafting error is instructive - a boolean of that shape is a *judgement over a measurement*, which the rule below says not to store. Counts were right and the summary was the mistake.

**It describes the text as delivered, and attributes no fault.** Not `source_quality`: a U+FFFD cannot be attributed between a damaged source and a bad decode on our side, and the distinction is usually unrecoverable. Naming it after the source would assert an attribution we do not have and point a consumer at the wrong thing to discount. What matters downstream is that the text is damaged, not whose fault it was.

**It is a derived cache, regenerated by the detector, never authoritative.** The body is the truth; this block exists so a consumer can filter or sort the whole corpus without parsing every body. Same standing as the digest's denormalised provenance render cache, and the same rule: if the two disagree, the body wins.

**Cache only what costs a body read.** A field derivable from frontmatter sitting beside it is not cached, because a stored copy of an adjacent value can drift from it and buys nothing:

| Not stored | Derive from |
|---|---|
| `garbled` | `replacement_chars` against the current threshold |
| `author_present` | `creators` |
| `title_sane` | `title` |

**`garbled` in particular must not be stored**, threshold or no threshold: it is a *judgement* over a measurement, and the threshold will move. A stored flag computed under an old threshold is silently wrong afterwards, exactly as a stored notional cost is wrong after a price change. Store the count; derive the verdict at read time.

**Omit a field the source type cannot have; never null it.** `chapter_titles` and `page_anchors` are absent for audio, because `source_type` already tells a consumer they are inapplicable - absence is unambiguous. Where the type *can* have them, they are present with their value **including zero**: `page_anchors: 0` on a PDF means "measured, none found", which is a real finding and must not be confused with "not applicable". This follows the existing convention that a valueless sub-field is omitted rather than set to null.

Additive-optional frontmatter is **not** a breaking change and does not bump `schema`. `anomalica/record/2` denotes the word-timestamp body grammar, not an accumulation of frontmatter fields - `document_type`, `email`, `overlay_next_id`, `copyright.media`, and the provenance axes all landed at `record/1`.

### Review units: a book is not a big article

**Review coverage is measured over SECTIONS, not over whole records**, wherever a record has sections. Settled 2026-07-29.

The whole-record unit works at 20KB, where "reviewed" honestly means someone read it. At book length it stops meaning anything: the store's largest records run 759-879KB, up to 2,512 blocks and 122,000 words, and a whole-record coverage figure for one of those asserts that a human read a book - roughly eight hours of the project's scarcest resource. Digest twenty books against that unit and every one sits permanently near 4% reviewed. The number does not merely become unimpressive; it stops carrying information, corpus-wide, and it does so silently as the corpus grows. That is the partial-denominator failure this project has now met in three places (see [audit-format.md](audit-format.md#adjudication-coverage)) - a figure that degrades smoothly with scale and never announces itself.

No interface change fixes it, because the unit is wrong rather than the presentation. A book is not a big article.

**The stored datum does not change.** `review.json` holds observed spans over blocks, and it continues to. Section-level coverage is an *aggregation boundary over the same spans* - a different denominator, not a different measurement. Three things follow, and they are the reason this can be decided without blocking anything:

- Existing review state stays valid. The four book records already in the store are **re-aggregated, never re-reviewed**; their spans mean exactly what they meant.
- Extraction stores nothing derived from the review unit, so digestion does not wait on this spec.
- Changing the unit again later is a read-side change, not a migration.

**Report sections, not an average.** A record carries per-section coverage and its record-level state is "N of M sections reviewed" - naming which. A single averaged percentage recreates the problem it was introduced to solve, and a coverage figure never prints without its denominator.

Partial review becomes an honest state rather than an unfinished one. A reviewer can cover the three chapters a claim set actually draws on and have that recorded as what it is.

#### What a section is

Follow the record's own structure where it has one; derive it where it does not:

| Record | Section |
|---|---|
| Ebook | Chapter - already where the digester takes book locations (chapter-relative offsets, since global offsets die at the next `prep_version` bump) |
| PDF | Page range, from the existing page boundaries |
| Transcript (audio/video) | A **time-anchored** segment, aligned to speaker-turn boundaries so a segment never splits a turn |

**A derived section boundary must be stable across re-extraction.** This is the load-bearing constraint and it is easy to get wrong: segment a transcript by block index and re-transcription silently re-points every boundary, orphaning review state - the same failure that body-anchored identity produced for records. Time is anchored to the audio and survives re-transcription; block indices do not. Segment transcripts by time.

Records with no sections and no length problem stay whole-record. The threshold for deriving sections on an unsectioned record is calibratable and starts at roughly 100KB of body - below that the whole record is one honest unit.

### Copyright status: what a source gets by default

`copyright.status` is one of `public_domain`, `open_licence`, `publicly_accessible`, `licensed`, `restricted`. Only the first two serve the ORIGINAL file openly; the rest gate it behind proof of possession. What differs between them is not whether *you* can reach the content, but whether Anomalica may redistribute the original file.

**`copyright.status` describes the content the publisher produced and licensed - not everything the file contains.** A publication can embed third-party material its publisher never held the rights to sublicence, and a single status per record cannot describe that. `copyright.media` carries the status of embedded media separately; absent, it inherits `status`.

The case that forces it: Argentina's Air Force publishes its UAP case reports under CC BY 4.0, but the reports are built around photographs and video stills submitted by private witnesses, which the licence's own "*excepto cuando se declare lo contrario*" carve-out excludes. The analysis text is genuinely open; the witness photographs are not the Air Force's to license. So `status: open_licence` with `copyright.media: restricted`.

**Do not collapse this to "the record's status is the most restrictive of its parts".** That gates the publisher's own openly-licensed analysis behind proof of possession - hiding public government material for no benefit, which is the same error the `.gov` default exists to prevent, and here it would gate exactly the officially-adjudicated text most worth surfacing.

The two errors are not symmetrical, so the defaults are not either:

- Over-gating open text is recoverable - a reviewer widens it later.
- Publishing a witness's photograph we hold no licence to is **irreversible** once served from the content-delivery network, and it is a third party's rights, not ours to risk.

So `copyright.media` is set at acquisition, by a human, wherever the source's licence carries a third-party carve-out - the handler cannot infer it, exactly as it cannot infer an [excerpt scope](data-model.md#record-unit-whole-containers-versus-scoped-excerpts). Where a record genuinely mixes rights-holders across its images, an individual [image annotation](#image) may override; that is the exception, and one status for the media class covers the normal case. Media whose status is absent, unknown, or unresolved fails closed.

An ingester assigns the status from HOW the source was acquired. Most specific wins:

| Acquisition | Default | Why |
|-------------|---------|-----|
| An explicit `--copyright` | that value | The caller knows (e.g. the war.gov importer stamps `public_domain`). |
| A `.gov` / `.mil` URL | `public_domain` | US government works carry no copyright (17 USC 105). There is nothing to protect, so gating one hides a public document from its own reviewer for no benefit. |
| Any other `http(s)` URL | `publicly_accessible` | We retrieved it anonymously, which PROVES it is publicly accessible. The original still stays gated - we don't redistribute someone else's copyrighted file - but the extracted text is surfaced. |
| A local file | `restricted` | Unknown provenance: we cannot assert anything about it, so fail closed. |

Two things this encodes, both learned the hard way:

- **Fetching from a public URL is evidence.** A source we pulled anonymously cannot honestly be called `restricted`. Every handler defaults a URL fetch to at least `publicly_accessible`; a PDF that defaulted to `restricted` was an outlier bug, not the policy.
- **The `.gov`/`.mil` rule matches the HOSTNAME, never the string.** `example.com/fake.gov/report.pdf` and `example.gov.uk` must not qualify - a substring match here opens copyrighted material.

These are DEFAULTS, not licence determinations - a government site can host a contractor report that retains copyright, so a reviewer can always override the status in the workbench. Widening one (gated -> open) is irreversible once served, so it is a human decision, never an automated upgrade.

### Web record snapshots

For `source_type: web` records, the ingester captures three artefacts from a single page load and lands each in the sibling `sources/` directory. The frontmatter exposes them like this:

```yaml
source_hash: sha256:904c041f...   # raw post-render HTML asset
snapshots:
  - role: page_render
    hash: sha256:82f42514...
    content_type: application/pdf
  - role: single_file
    hash: sha256:e7115739...
    content_type: text/html
```

| Role | What it is | Use it for |
|------|-----------|------------|
| (raw HTML via `source_hash`) | Post-render DOM, no external resources inlined | Fidelity check on the extraction. Renders unstyled in a sandboxed iframe because external CSS won't load - not the right surface for visual review. |
| `page_render` | Single-page PDF rendered at 1024 px wide, sized to the document's scrollHeight (no internal pagination) | Printing; PDF.js review panes. |
| `single_file` ("frozen page") | Self-contained HTML produced by `single-file-cli` with every external resource inlined as data URIs | **Canonical review surface.** Renders identically to the original page under `sandbox=""`. |

Consumers preferring fidelity should pick `single_file` first, fall back to `page_render`, and use the raw HTML only as a last resort.

Snapshot roles are an extensible registry. New roles can be added without bumping `schema` provided consumers ignore unknown roles. Known roles as of `anomalica/record/1`: `page_render`, `single_file`.

## Content

Standard markdown. Headings, paragraphs, lists, bold, italic, links, and tables all work as normal.

The body carries the extracted content only - the ingester does not inject the title into it. The title lives in frontmatter `title:`, which the workbench and consumers (the digester parses it from the frontmatter, not the body) read from there. For web records the page's own leading title heading - which trafilatura emits and which merely duplicates `title:` - is stripped; a source document's own in-content headings (e.g. a PDF's printed heading) are preserved as faithful content. The body may begin with an optional `*Published <date>*` stamp, omitted when the body already states the publication date in a byline or when the date is unknown.

## Block annotations

YAML inside HTML comments. Single-field annotations use inline comments. Multi-field annotations use multi-line comments. Used for structural markers that sit between content.

> **Adding an annotation type carries three obligations, not two.** Update this document in the same change, and update the emitter - both understood. The third is easy to miss: **decide and record how the pre-digest treats it**, stripped or preserved as context, and tell the digester. The digester cannot infer the disposition of a type it has never seen.
>
> **The fallback is currently the unsafe direction, so do not rely on it.** `anomalica_common.pre_digest` matches an **allow-list** of four families (`highlight`, `link`, `note`, `cites`); anything outside them passes straight through to the model as literal text. So an undecided annotation type is not hidden from extraction - it is *shown* to it, and our own syntax arrives in the model input as if it were source text. That is why `{{classification: ...}}` reaches claim extraction today. This lives in the shared module, so it binds the assimilator as well as the digester. If the fallback is later inverted to strip-by-default, the obligation is unchanged and only the consequence of forgetting changes - from "our syntax reached the model" to "a new annotation went missing". Cheap to write down now; expensive to discover in a digest six weeks later.



### Page boundary

```markdown
<!-- file_page: 2 -->
```

`file_page` is always the PDF page number (1-indexed from the start of the file). If the page has its own printed page number that differs, include `printed_page` on a separate line:

```markdown
<!-- file_page: 19 -->
<!-- printed_page: 15 -->
```

`printed_page` is omitted when there is no printed page number, or when it matches `file_page`.

For `ebook` records there is no fixed file pagination, so `file_page` does not apply. When the EPUB carries EPUB3 pagebreaks (`epub:type="pagebreak"` or `role="doc-pagebreak"`, whose `title` is the print-edition page), the ingester emits `printed_page` alone at each break position:

```markdown
<!-- printed_page: 15 -->
```

The label is taken verbatim from the pagebreak, so front-matter roman numerals (`iii`, `viii`) and index labels appear as-is. A page break can fall mid-paragraph, so the marker records where print page N begins in the reflowed text. EPUBs without pagebreaks carry no page markers and locate content by [chapter boundary](#chapter-boundary) only.

### Speaker change

An inline HTML comment marks when the speaker changes. All content until the next speaker annotation belongs to that speaker.

```markdown
<!-- speaker: David Fravor -->
```

The `speaker` value is the speaker's name, or - when the real name is unknown - a description of them in square brackets.

#### Square brackets mean "this is a description, not a name"

`<!-- speaker: David Fravor -->` names a person. `<!-- speaker: [interviewer 2] -->` describes one. The brackets are part of the value and they carry meaning: they say the person's real name is unknown, and what stands in its place is a description of who they were in this recording.

**A description is scoped to its own record.** The `[interviewer 2]` in one recording is not the `[interviewer 2]` in another, and neither is the `[audience member]`, the `[recovery team member]`, or the `[speaker 3]`. This is the whole reason for the notation, and every consumer must honour it:

- **No cross-record identity.** A bracketed speaker never becomes a person the graph follows between records, is never merged with a same-spelled description elsewhere, and never accumulates a biography. Nothing should end up holding a file on somebody called "interviewer one".
- **No cross-record suggestion.** A name-completion list built from the corpus must not offer bracketed values, or a reviewer is invited to file two strangers under one label.
- **Still a real participant of THIS record.** They appear in the record's `speakers:` list, their turns are theirs, and a quotation drawn from those turns is attributed to them exactly as written - `[interviewer 2] asked ...`. Within one record the description identifies somebody consistently; it just does not travel.
- **Record-scoped, so not curated.** A real name in `speakers:` is kept even when no turn is currently theirs - only a reviewer removes it. A description means nothing apart from the turns it labels, so it goes when its last turn does.

Reserved descriptions, common enough to spell the same way everywhere:

| Token | Meaning |
|-------|---------|
| `[speaker 1]`, `[speaker 2]`, ... | A diarisation cluster nobody has identified yet. What the ingester emits by default. |
| `[narrator]` | A voice-over narrator distinct from any on-camera speaker. |
| `[group]` | Multiple people saying the same thing simultaneously - chants, unison answers from a committee, group responses. |
| `[irrelevant]` | Content that doesn't belong in the record (ads, sponsor reads, off-topic asides). Hidden from rendered output, and stripped before extraction so no claim is drawn from it (see [Irrelevant content](#irrelevant-content)). |
| `[external footage]` | DEPRECATED - use an [external passage](#external-passages) region instead, and name the speaker plainly. Retained only so existing records parse. |

The list is not closed. Any description a reviewer needs is written the same way, lower case, in brackets: `[interviewer 1]`, `[audience member]`, `[recovery team member]`, `[ground control]`, `[hollywood makeup artist]`. A reviewer marks a name as a description in the workbench, which writes the brackets; the ingester writes `[speaker N]` for every diarised cluster it cannot name.

**Older records say `Speaker 1` unbracketed.** It means the same thing, and consumers must accept both - the bracketed form is simply the version that says so out loud. Anything matching `Speaker <n>` with or without brackets is a diarisation id and never a person.

**A description is not a pseudonym or a partial name.** `Mrs. Smith`, `Annika`, `UAP Gerb` are what somebody is called, however incomplete - they stay unbracketed. The test is whether the value would still identify this person if you met them: a name would, a description would not.

**`Name (description)` is a NAME, and the distinction is load-bearing.** `Sally (Budd Hopkins abductee)`, `Dave (SR-71 pilot)`, `Dr. X (French physician)`, `A Friend (anonymous army sergeant)` - a given name or a pseudonym carrying a disambiguating parenthetical. Around twenty real people in the corpus are written this way and they DO match across records, which is the whole point of the parenthetical: it tells two Sallys apart. Only a value that is *entirely* a description is bracketed. Anything treating brackets or parentheses as a signal must survive this form - a guard that reads `Sally (Budd Hopkins abductee)` as anonymous silently removes twenty people from the graph, and one that splits on the comma inside the parenthetical mangles the name outright (`'widow of Louis Emrich) Emrich (Mrs.'` is a real example of the second, from a natural-order migration).

**A sweep for descriptions is written against name SHAPE, not a leading word.** The failure to avoid: a query keyed on a lower-case `unnamed` prefix, which misses `Senior U.S. Intelligence Officer (Anonymous)` and every capitalised description. That is the enumeration mistake again - the leading word is a notation, and the notation varies. Ask instead whether the value names anybody.

### Mathematics

Equations are transcribed as LaTeX, delimited `\[ ... \]` for display and `\( ... \)` inline.

```markdown
\[ r = R \sqrt{\beta} \frac{F_\text{sky}\,\Omega}{F_\text{sun}\,\alpha_\text{moon}} \tag{4} \]
```

**This is faithfulness, not presentation.** Flattening an equation to unicode destroys structure that cannot be recovered: the same source line renders as `r = R · √β · Fsky · Ω/(Fsun · α)`, from which a reader cannot tell whether the radical covers `β` alone or the whole product, and where `F_sky` and `α_moon` have silently lost their subscripts. That is the same class of loss as a paraphrased quote - the record stops representing what the page says. "Transcribe as-is" therefore *requires* LaTeX here; unicode approximation is the departure from it.

**Not `$`, and not `$$`.** A corpus of government programmes is full of dollar figures, and `$` as a math delimiter collides with them. A no-space-hugging guard handles `$22 million` but still misreads a range - `$50-$60` opens at `$5` and closes at the `$` preceded by `-`, swallowing the text between. That is a silent corruption of ordinary prose into math, and this document already settled the identical question once: double curly braces were chosen for inline annotations because "single curly braces appear in source text (mathematics, code, template syntax)... this avoids false matches **without requiring escape mechanisms**". LaTeX's own delimiters are unambiguous in prose; use them.

**Inside a math span the sequence `{{` never appears.** The ingester normalises nested braces to `{ {` - identical in TeX, where the space is grouping whitespace - enforced deterministically after extraction. So annotation parsing needs no special-casing for mathematics, and a consumer parses the body in one pass.

Without it, `x^{{n}}` and `\frac{{a}}{{b}}` match the [inline annotation](#inline-annotations) grammar, and the prose-anchor's marker-skip reduces `x^{{n}}` to `x^` before anything else runs - a silent mis-parse for every consumer reading against this spec, not only a rendering fault. The fix belongs at the producer for the same reason the delimiters do: the alternative is every consumer lifting maths out before parsing, which makes them all math-aware to solve a problem one writer can prevent.

Worth noting the [double-brace rationale](#why-double-curly-braces) considered mathematics and drew the opposite conclusion - that *single* braces are what appears in maths and code, so doubling them avoids collision. That is right about ordinary notation and blind to nested groups, which produce `{{` from two single braces meeting. The reasoning was sound and its example set was incomplete.

**Transcribe, never simplify.** Reproduce the equation as printed - do not solve, rearrange, normalise notation, or drop an equation number. The LaTeX must render to what the page shows, and the same fidelity bar applies as to a quote.

**No schema bump.** This is additive within `record/1`. `record/2` denotes word timestamps because `{{t:}}` markers interleave through the whole body and a consumer ignorant of them renders garbage; math is localised and **degrades gracefully** - a consumer that does not render it shows the LaTeX source, which is still readable and still faithful. Graceful degradation is the test for a body construct, not whether it touches body grammar.

### Document boundary

Marks where each contained work starts inside a **compilation** - a proceedings of separate papers, an anthology, a report bundling annexes by different authors.

```markdown
<!-- document: {n: 3, title: "Apparent Endless Extraction of Energy from the Vacuum by Cyclic Manipulation of Casimir Cavity Dimensions", creators: ["Robert L. Forward"], document_type: report} -->
```

| Key | Meaning |
|-----|---------|
| `n` | Position in the container, first document first. |
| `title` | The contained work's own title. |
| `creators` | Its authors - **not** the container's. |
| `document_type` | The contained work's form, where it differs usefully from the container's. |

One annotation carrying a YAML mapping, for the same reason as [message boundaries](#message-boundary): separate keys desynchronise, and a parser then cannot tell a missing key from a misplaced one.

**Attribution flows to the contained document, and this is the load-bearing part.** A claim drawn from between one `document` annotation and the next is attributed to *that* document's `creators`, never the container's. Without the rule, a claim from Forward's paper is sourced to a NASA workshop proceedings and loses that Forward wrote it - the flattened attribution [0044](../decisions/0044-claim-provenance-chain-is-required.md) exists to prevent, arriving by a different route. The container's own `creators` remain whoever compiled or issued it.

This is the general case of the message boundary; correspondence is the specialisation, carrying `from`, `date`, and `quoted` instead. A consumer treating both as "a contained work starts here" is reading them correctly.

**A compilation is one record, not many.** Identity is source plus selection, so one PDF is one source. Splitting a proceedings into seventeen [scoped excerpts](data-model.md#record-unit-whole-containers-versus-scoped-excerpts) would price review and digestion per paper and multiply the store for nothing the annotation does not already give. And `document_type` is never set on the container - a record-level value asserts the whole record is one work.

**A guard against "this is an annotation, not content" is written against POSITION, not notation.** Three times in one week a construct crossed a component boundary and the receiving side had been written for the notation it used to have: a classification-marker strip that matched one form, a `creators` guard matching `{{...}}` only and so letting `[redacted]` through as an author's name, and a bracket rule that could not tell `[interviewer 2]` from a literal `[sic]` inside a quote. The pattern is the same each time - a defensive test enumerating notations, and the notation moved.

Enumerating is the mistake, because the next notation is missed silently. Test the position instead: a speaker description is the WHOLE VALUE of a `<!-- speaker: ... -->` comment, never inline in body text, which is what tells it apart from the `[sic]` and `[bracketed]` clarifications that real source content contains. A creator that is entirely a bracketed or braced token is not a name, whichever form it takes. Where a positional test genuinely is not available, two fallbacks in order. **Test the least lossy value available at that point** - the name wherever a name exists, a derived form like a slug only where nothing else does. A component far downstream receives derivatives rather than originals, and the lossy one is usually the one nearest to hand: `[interviewer 2]` slugifies to `interviewer-2`, indistinguishable from a legitimate slug, while the display title beside it still carries the brackets exactly as it carries the accent in "Jacques Vallée". Reaching past the derivative to the name it came from is what makes such a guard hold. Then, and only then, **fail towards treating the value as an annotation** rather than as a person's name - a dropped attribution is recoverable, a person node named `{{redacted}}` propagates.

**Never write frontmatter vocabulary into a body.** A 416-page proceedings arrived carrying seventeen `***`-fenced blocks of `schema: anomalica/record/1` / `title:` / `creators:` / `source_type: pdf` - the extraction model reproducing the record template it had been shown, because the format gave it nowhere else to put per-paper metadata. Those keys are ours, not the source's; by the format's own [total rule](#structure) such a block is content, so the extraction model then reads our schema back as something the source says. The model chose `***` over `---`, correctly avoiding the truncation the [Store](#store) section warns about - it failed only where the format was silent.

### Message boundary

Marks each message in an email thread, and each piece of correspondence inside a container. Structurally this is the correspondence equivalent of [Speaker change](#speaker-change): one body divided into segments authored by different people at different times.

```markdown
<!-- message: {n: 2, from: "John Podesta <john.podesta@gmail.com>", date: 2015-03-05T18:38:14-05:00, quoted: true} -->
```

One annotation per message carrying a YAML mapping, rather than several loose keys. Separate `message_n` / `message_from` / `message_date` annotations can desynchronise, and a parser cannot then distinguish a missing key from a misplaced one.

| Key | Meaning |
|-----|---------|
| `n` | Position in the thread, outermost message first. **This is the ordering key** - a consumer orders a thread by `n`, never by `date` (see below). |
| `from` | The sender, `Name <address>` where both are known. |
| `date` | The message's own `Date` header as ISO 8601 with offset **where that header parsed**; otherwise the source's own attribution text verbatim (e.g. `"Mar 5, 2015 6:08 PM"`) - opaque, for display only, and **never parsed as a timestamp**. The verbatim fallback is kept rather than dropped or coerced: an attribution line carries no timezone, so synthesising an ISO value would fabricate an offset, and fabricating a timestamp in an archive is worse than carrying the string the source printed. The two forms also differ in TYPE after YAML parsing - the ISO form resolves to a timezone-aware datetime, the verbatim fallback stays a string - which is where a naive consumer breaks at the point of use, not at parse. A consumer tests the type (or the ISO shape) before treating a value as a timestamp; because the fallback is unsortable, `date` is not an ordering key. |
| `quoted` | `true` where the segment is quoted inside a later message rather than authored at this level. |

**Parse the mapping as YAML; do not pattern-match the annotation text.** The value is well-formed YAML - string values are double-quoted and `\`/`"` escaped, and a `-->` inside a value is emitted as `--\x3e` (a YAML `\x` escape) so an attacker-controlled display name from an email dump cannot close the annotation's HTML comment early. A consumer that scans the raw text instead of parsing it both mis-reads a display name containing `quoted: true` as the flag, and - absent the escape - loses the tail of any annotation whose value contained `-->`. Read `quoted` from the parsed mapping.

**`quoted` is the load-bearing key.** A reply that quotes its predecessor puts two people's words in one body, and without the flag an extractor attributes the quoted text to the replying sender - the correspondence equivalent of a flattened attribution, and just as invisible once it reaches a claim. Every claim drawn from a `quoted: true` segment belongs to that segment's `from`, never to the message containing it.

This annotation applies wherever correspondence appears, including inside a container whose own `document_type` is not `email` - which is the case it exists for.

### Sentence-level timestamps

In `record/1` audio and video transcripts, each sentence starts on its own line prefixed with a `HH:MM:SS.D` timestamp (fixed 10 characters, one decimal place). An empty line indicates a paragraph break. Word-level `record/2` transcripts carry inline per-word markers instead and omit this line-start prefix - see [Word-level timestamps](#word-level-timestamps) below.

```markdown
<!-- speaker: David Fravor -->
00:01:45.2 We had been at sea for roughly two weeks.
00:01:48.7 I was the Commanding Officer of Strike Fighter Squadron Forty-One.
00:01:53.1 We were at the beginning of our workup cycle.

00:01:56.4 When we arrived at the location at 20,000 feet, the controller called merge plot.
```

The timestamp format is always `HH:MM:SS.D` - hours, minutes, seconds, and one decimal place (tenths of a second). This lines up in a fixed-width column for readability.

### Word-level timestamps

Records with `word_timestamps: true` (schema `anomalica/record/2`) carry timing on every word, not every sentence: an inline `{{t:SECONDS}}` marker (seconds from media start, two decimal places) sits immediately before each word.

```markdown
<!-- speaker: David Fravor -->
{{t:105.20}}We {{t:105.38}}had {{t:105.55}}been {{t:105.71}}at {{t:105.83}}sea {{t:106.10}}for {{t:106.34}}roughly {{t:106.78}}two {{t:107.01}}weeks.
```

These records do **not** carry the sentence-level `HH:MM:SS.D` line-start prefix: each line's first `{{t:}}` already gives its start, so the prefix is redundant. The one exception is a transcript segment for which the aligner produced no word-level timing - that line keeps a `HH:MM:SS.D` line-start stamp as its only timing and has no `{{t:}}` markers. Consumers that want plain prose strip the `{{t:}}` markers like any other annotation.

### Image

Marks a figure, chart, or photograph that appears in the source. Two forms.

**Description-only (inline).** A factual description or transcription with no extracted file. The value is a scalar string - this IS the `description` (image content, kept by the pre-digest and extractable), just with no `file`, `alt`, or `caption`:

```markdown
<!-- image: Bar chart showing UAP reports by year from 2019 to 2023, with a sharp increase in 2021. -->
```

**With extracted file.** When the ingester has saved the image bytes alongside the record, the value is a mapping with at minimum a `file` field:

```markdown
<!--
image:
  file: abc123def4567.png
  alt: "Portrait of a man in a dark suit"
  caption: "David Charles Grusch (Copyright (c) D. Grusch. Image may not be reproduced without permission.)"
-->
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | yes | The image's filename - bare, not a path. Format is `{img_hash}.{ext}` where `img_hash` is a 12-character hexadecimal SHA-256 prefix of the image bytes and `ext` is the file extension (`png`, `jpg`, `gif`, `svg`, `webp`). |
| `alt` | string | no | Alt text from the source (`<img alt="">` in EPUB/HTML). Omitted when the source provides no alt text. |
| `description` | string | no | A faithful transcription or factual description of what is IN the image - the text of a tweet or document screenshot, the figures in a chart, the words on a scanned page, or a plain description of a photo. Generated by a vision pass or human review, not by the ingester. Unlike the other image sub-fields this is CONTENT: the pre-digest renders it into the model input as an `[image: ...]` meta-note (see [the bracket meta-notation](#the-bracket-meta-notation)), so a claim can be drawn from what the image shows (a screenshotted tweet's text is a real statement). It must stay faithful to the image - transcription or factual description, never interpretation - so any claim drawn from it is honestly sourced. Omitted when no description has been written. |
| `caption` | string | no | The source's PRINTED caption for the image, verbatim - including any copyright or attribution line the source shows with it (e.g. `David Charles Grusch (Copyright (c) D. Grusch. Image may not be reproduced without permission.)`). Distinct from `alt` (the source's HTML alt attribute) and `description` (a generated factual description): the caption is what the source itself printed beneath the figure. It renders into the pre-digest as a `[caption: ...]` meta-note - context the model sees but the digester never extracts as a claim (attribution and copyright are not facts about the subject). Omitted when the source shows no caption. |
| `irrelevant` | boolean | no | Reviewer's keep/drop DISPLAY flag. Absent (the default) means keep/render; `true` marks an image not worth rendering (an advertisement, a decorative element, a stock photo unrelated to the subject). Mirrors the text mark-irrelevant convention - kept unless explicitly marked. When `true`, the image is excluded from the pre-digest (never extracted) AND skipped by the assembler/site (never rendered) - the mark drops it from both extraction and display. |

The `file` value is a bare filename so the body of the record stays self-contained and content-addressable. The full path on disk is `media/{record_hash}/{file}` relative to the ingests root, where `{record_hash}` is the hash of the record containing the annotation (the same value as the record's filename in `store/`). Embedding the record hash directly in the body would break the record_hash invariant for source types whose `content_hash` is computed from the body (ebook, web).

When the same image appears in multiple records, each record gets its own copy under its own `media/{record_hash}/` subdirectory. This keeps records self-contained for downstream consumers (workbench, assembler, digester) at the cost of duplication, which is small in practice (cover art, publisher logos).

**How images render into the pre-digest.** An image is not stripped to bare prose; it is rendered into the pre-digest as a `[...]` meta-note (see [the bracket meta-notation](#the-bracket-meta-notation)):

- `[image]` alone when the annotation has no description - signalling only that an image is present;
- `[image: DESCRIPTION]` when a description exists (the mapping's `description:` field, or the inline form's scalar value);
- followed by `[caption: CAPTION]` when a caption exists.

An image flagged `irrelevant: true` is excluded from the pre-digest entirely - the mark means dropped-from-extraction, not only dropped-from-display. The `file` and `alt` fields are storage and accessibility metadata and are not rendered. The whole annotation still stays in the record for the assembler to render the actual image; the `[...]` rendering is only how the image reaches the model.

So a tweet screenshot annotated as:

```markdown
<!--
image:
  file: 3a7c1e90b2d4.png
  description: "Tweet by @user, 3 May 2023: The Pentagon confirmed today that the 2004 Nimitz object remains unidentified."
  caption: "Screenshot, via a news report"
-->
```

reaches the model as `[image: Tweet by @user, 3 May 2023: The Pentagon confirmed today that the 2004 Nimitz object remains unidentified.] [caption: Screenshot, via a news report]`. The tweet text (a description) can become a claim; the `[caption: ...]` (attribution) is context the digester never extracts. The meta-versus-content rule is defined in full under [the bracket meta-notation](#the-bracket-meta-notation).

A reviewer's keep/drop choice for an image is the `irrelevant` flag on the same annotation (`irrelevant: true`; absent means keep), mirroring the text [mark-irrelevant convention](review-workbench.md#what-to-mark-irrelevant). A flagged image is excluded from the pre-digest entirely - the model never sees it - and skipped by the assembler/site when rendering: the mark drops the image from both extraction and display. Like other reviewer corrections, the who/when rides on the git commit that sets it, not an inline stamp:

```markdown
<!--
image:
  file: 9f2c1a0b4de8.jpg
  alt: "Advertisement banner"
  irrelevant: true
-->
```

### Chapter boundary

Marks the start of a chapter or top-level structural section in long-form documents (primarily ebooks).

```markdown
<!-- chapter: 1 -->
<!-- chapter_title: "The Secrecy" -->
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chapter` | string | no | The chapter's own number, as a decimal string. It is the number the book prints at the head of the chapter, however the source writes it - `1`, `Chapter One`, `CHAPTER I`, and a bare `ONE` all yield `chapter: 1` - so the value is the label a reader would cite ("chapter 1"), not a position in the file: the book's chapter 1 carries `chapter: 1` even though a dozen front-matter sections precede it in reading order. Omitted for any section the source does not number - front matter (cover, contents, dedication), part dividers ("Part One"), and unnumbered chapters. |
| `chapter_title` | string | no | The chapter's title as given in the source, with any leading enumerator stripped (`"1. The Secrecy"` in the table of contents becomes `"The Secrecy"`, the number moving to `chapter`). Always quoted. Omitted when the source provides no explicit title. |

At least one of the two fields is present on every marked section: a numbered chapter carries both, a titled-but-unnumbered section (front matter, a part divider) carries `chapter_title` alone. The extractor drops the source's own chapter-number heading from the body once it is captured here, so the number is not left as an orphan line (`1`) with no context; a part divider keeps its "Part One" line as prose.

These are structural markers, not rendered prose. Consumers typically use them for navigation (jump-to-chapter, table of contents construction) and suppress them when displaying the body. Where a `chapter_title` is present, the source itself usually also opens the chapter with a heading on the next non-empty line; consumers should not render the annotation as a duplicate of that heading. A claim's location cites the `chapter` value (`ch1:1240-1310`), so it names the chapter a reader can turn to rather than a file offset.

### Footnotes

Footnotes and endnotes are normalised to CommonMark footnote syntax regardless of where the source keeps the note text (foot of the page, end of the chapter, end of the book):

```markdown
The craft was recovered in 1947.[^12]

[^12]: Corso, *The Day After Roswell*, p. 34.
```

A `[^N]` reference marker is placed inline at the exact point the source cites the note, and the note's text is collected as a `[^N]: ...` definition at the end of the chapter that cites it, so a chapter and its notes stay together when the body is chunked by chapter. `N` is a book-wide sequential number, unique across the whole record. The reference and its definition replace the source's own linkage (a superscript linking to a separate notes section), which would otherwise flatten to a bare digit stuck onto the preceding word. Where the note text cannot be resolved, the `[^N]` marker is still emitted without a definition rather than left as a stray digit in the prose.

### Block-level redaction

```markdown
<!--
redacted:
  extent: paragraph
-->
```

`extent` estimates how much was redacted: `words`, `sentence`, `paragraph`, or `page`.

### Inline redaction value

An inline `{{redacted: ...}}` value carries two things, comma-separated, both optional:

- an **extent** - the redaction box's width estimated in characters, `~N chars` (the older `~N words` is still accepted); and
- the **citation** the redactor printed in or beside the box - the FOIA exemption or classification code, verbatim as printed (`(b)(6)`, `1.4a`, `3.5c`), several comma-separated as the source lists them.

Either may appear alone, or both together in either order: `{{redacted: ~12 chars, (b)(6)}}`, `{{redacted: (b)(3), (b)(6)}}`, `{{redacted: ~8 chars}}`, or a bare `{{redacted}}`. A consumer reads the value rather than matching a fixed shape: a comma-separated part that looks like `~N chars` or `~N words` sizes the bar; anything else is the printed citation, drawn inside the bar the way the source prints it in the box.

**Flat and comma-separated, not a mapping** - and this is deliberate, despite [block annotations](#block-annotations) taking a YAML mapping for exactly the desynchronisation reason. Inline annotations cannot nest: a mapping here would close with `}}}` and break the `}}` scan, the same constraint that keeps a [cross-record link](#cross-record-links) payload a flat list. So the value is classified by shape rather than by key, which is safe only because the discriminator is total - `~` begins an extent and never begins a citation, since FOIA exemptions and classification codes are printed `(b)(6)`, `1.4a`, `3.5c`. Read the parts; do not match a fixed shape.

`~N chars` off a rendered page image is a model's estimate with the same epistemic status as `~2 words`, in a unit closer to what the artefact shows - a redaction is a drawn box of measurable width, not a word count. It is judged from the box itself; it is never a word count multiplied into characters, which would read as a measurement while carrying strictly less information than the count it came from. (Deterministic geometry is not an option: even the born-digital records in this corpus are scanned pages under an OCR text layer, so a redaction is pixels inside an image, not a rectangle a layout query can return.)

### Irrelevant content

Content that is physically part of the source but does not belong in the record - a book's title page, table of contents, index, or glossary; a publisher's cross-sell advertisement; an off-topic aside. It is marked, never deleted: the mark is fully reversible and the source text stays intact in the ingest. What counts as irrelevant - the reviewer convention across every record type - is the canonical list in [review-workbench.md](review-workbench.md#what-to-mark-irrelevant); this section specifies the marker syntax.

The mechanism depends on the source shape.

**Prose records (web, ebook, pdf)** have no speakers or segments, so a paired HTML-comment region wraps the irrelevant block(s):

```markdown
Chapter Eleven closes the investigation.

<!-- irrelevant: start -->

## Also by this author

*Order the sequel, out this autumn from the same publisher.*

<!-- irrelevant: end -->

Appendix A lists the case files referenced above.
```

- **Block-aligned.** `start` and `end` each sit on their own annotation line and wrap whole blocks (paragraphs, headings, lists, tables) - never part of a sentence. There is no mid-sentence form; excluding a fragment of a sentence is not an irrelevant-marking case.
- **Non-nesting.** A region never contains another region: a `start` is closed by the next `end`.
- **Multiple regions** per record are allowed.
- **Verbatim and reversible.** The wrapped text is the source text unchanged; the two comment lines are the only addition, so removing them restores the record exactly.

Each marker is an ordinary single-field block annotation: `<!-- irrelevant: start -->` parses as the YAML mapping `{irrelevant: start}`, value `start` or `end`. Note the space after the colon that YAML requires - write `irrelevant: start`, not `irrelevant:start` (the latter parses as a bare string, not a mapping, and is invalid here).

**Audio and video transcripts** have no prose blocks to wrap, so they mark irrelevant spans by segment instead, through the reserved `[irrelevant]` speaker token (`<!-- speaker: [irrelevant] -->`; see [Speaker change](#speaker-change)). The region marker complements that token - it does not replace it: prose gets the region, transcripts get the speaker token.

**The digester strips both before extraction.** Before reading a record, the digester removes all irrelevant-marked content - both prose `irrelevant: start`/`end` regions and transcript `[irrelevant]` speaker segments - so the extraction model never sees it and no claim is drawn from it. This parallels the classification-marking strip ([Classification markings](#classification-markings)): a read-time transform only. The source text stays in the ingest and the reviewer's mark stays reversible; nothing is written back from the digester, so data still flows one direction. The strip is one step of the deterministic model-prep the digester applies before extraction to produce the **pre-digest** - the materialised, inspectable artefact that is the exact text the model reads ([0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)).

This is additive within `anomalica/record/1`: a consumer that does not recognise the region treats the wrapped text as ordinary content - the behaviour before the marker existed - so it needs no `schema` bump.

## Inline annotations

For annotations that fall mid-sentence. The syntax is `{{YAML}}` - double curly braces containing valid YAML.

```markdown
The programme was conducted at {{redacted: ~9 chars, (b)(1)}} Air Force Base.

The date was {{illegible: possibly March 2004}} according to the memo.

{{Fravor: holds up photograph}} and showed us the evidence.

{{audience: laughter}}
```

The content inside `{{ }}` is parsed as YAML, in one of two authored forms:

- **Keyed** - a single key-value pair where the key describes what or who the annotation is about and the value gives the detail (`{{Fravor: holds up photograph}}`). There is no fixed vocabulary of keys; the key is whatever makes sense in context.
- **Keyless** - a bare YAML scalar, for an unkeyed note that needs no subject (`{{laughs}}`, `{{applause}}`). The scalar is the whole note.

A small set of keys is *reserved* for machine-read markers rather than free-form annotation content: `t` (word-level timestamp), `highlight-start` / `highlight-end` / `highlight-context` ([Highlights](#highlights), [Highlight context links](#highlight-context-links)), `note-start` / `note-end` ([Span notes](#span-notes)), `link-start` / `link-end` ([Cross-record links](#cross-record-links)), `external-start` / `external-end` ([External passages](#external-passages)), and `cites-start` / `cites-end` ([Cited works](#cited-works)). A consumer treating the body as prose strips the whole `{{...}}` family so a marker never breaks word matching. The extraction pipeline strips the `t`, `highlight-*`, and `link-*` markers entirely (they carry no content); for `note-*` it strips the markers but preserves the note's text as context, exactly as it keeps the keyed and keyless content notes (see [Span notes](#span-notes) and [The bracket meta-notation](#the-bracket-meta-notation)).

### Why double curly braces

Single curly braces appear in source text (mathematics, code, template syntax). Double curly braces are extremely rare in natural text. This avoids false matches without requiring escape mechanisms.

### Values containing special characters

Since the content is YAML, values containing colons or commas need quoting:

```markdown
{{Fravor: "turned to the camera and said: look at this"}}
```

Standard YAML quoting rules apply.

### Classification markings

Declassified government documents carry security classification markings at two levels. Both are preserved.

**Document level.** The overall classification banner (`(SECRET//REL TO USA, FVEY)`, `(SECRET//NOFORN)`) goes in the frontmatter `classification` field, verbatim with the surrounding parentheses stripped. In-body repetitions of that same banner - the page headers and footers that restate it - are redundant with the frontmatter and stripped from the body.

**A struck overall banner still goes in `classification`.** The field records what the document *was* marked - it is the prior state, not an assertion that the marking is in force. That is what "original" means in its definition, and it has to be: every declassified release in this corpus carries a marking that is no longer in force, so a field asserting current classification would be wrong on essentially every record rather than on this one.

The strike rule that bars a struck banner from being tagged applies to the **inline** `{{classification: ...}}` annotation, which asserts a marking over a span of text at a position. The frontmatter field makes no such assertion, so there is no conflict between the two rules and no need for a separate `declassified_from`. Both halves of the fact are already kept: `classification` holds what it was marked, and [`release`](#release-and-declassification) holds the declassification that removed it. Dropping the repeated struck banner from the body as furniture therefore loses nothing - it is the one place the fact is *not* needed.

**Portion level.** Markings that classify a specific portion and differ from the document banner (`(S//REL)`, `(U)`, `(S/RELIDO)` prefixing a paragraph or section heading) are preserved as an inline annotation at the start of the portion they govern:

```markdown
{{classification: U}} This paragraph was unclassified within an otherwise classified report.

{{classification: "S//REL"}} This paragraph carried its own portion marking.
```

The value is the marking verbatim, parentheses stripped, quoted when it contains special characters (the `//` and commas common in markings). A portion marking applies from its position until the next classification marking; the frontmatter `classification` is the default for any portion with no preceding marking. This lets a consumer attribute the classification of any portion - and therefore of a claim extracted from it - though doing so is optional.

A classification marking that is merely **printed and in force** is never given a strikethrough; strikethrough is only for text genuinely struck through in the source.

A marking that **is** struck through - a declassification stroke ruled through a banner or a level - is strikethrough text in principle: the stroke is an event on the page, not decoration.

**The extraction model will not produce it, and this is a limit rather than a prompt bug worth chasing.** A model that recognises a classification marking tags it as one rather than transcribing what was done to it, and that reflex beats the instruction. Measured on the declassified Misrep corpus: the model strikes an adjacent struck caveat (`NOFORN`) every time, yet never the struck level (`SECRET`) on the identical `label: value` line beside it. This held across two models - the Claude subscription and the Luna vision model - and several prompt shapes, including a dominant "strike first, override every other rule" instruction. **Do not spend re-extraction runs on it.**

The response is text-preservation-first: the marking's wording is kept intact and readable, nothing is lost, and a reviewer applies the stroke by hand with the workbench's strike control.

**A stroke is preserved in two places, and they are not alternatives.** The strikethrough records what the page *shows*. The declassification itself is *release provenance* and belongs in [`release.markings`](#release-and-declassification), verbatim as stamped, because that is where a consumer looks to learn a document was declassified - it must not have to infer it from body formatting. **Striking a marking means REPLACING it with prose, not decorating it.** A reviewer's stroke turns `{{classification: SECRET//REL TO USA, FVEY}}` into `~~(SECRET//REL TO USA, FVEY)~~`; the annotation is gone, not wrapped. This is a property of the format rather than one editor's behaviour, and it is load-bearing for two different consumer designs that fail in unrelated ways without it. Wrapping produces `~~{{classification: X}}~~`, and every annotation stripper then removes the marker and leaves `~~~~` around nothing. A consumer that indexes prose for selection fails earlier and more quietly: such an index must exclude `{{...}}` spans - otherwise a reviewer could not place a note over words a marker already sits in - so the banner text is not in the index at all, the selection cannot be located, and the strike silently declines. Ordinary prose is still wrapped as usual; only a marking is replaced.

**A struck banner is emitted as prose carrying the stroke, never as a `{{classification: ...}}` annotation.** The annotation asserts a marking *in force*; a struck banner is a marking *removed*, so tagging one is asserting the opposite of what the page says - wrong on its own terms, before any question of stripping. The stripping is the second reason: annotations are removed before extraction, so a stroke applied to one is removed with it, and a reviewer striking a tagged banner in the workbench strikes something that does not survive.

Measured 2026-08-21 on a re-extracted Misrep record, the emitter does both: five banners tagged as annotations (`SECRET`, `SECRET//REL TO USA, FVEY`, `S/RELIDO`) and one struck caveat emitted as prose (`~~NOFORN~~`). The prose case is the useful half of the evidence - the model is **inconsistent here, not incapable**, which is what the reflex finding predicts rather than contradicting it.

Like every annotation, classification markings are metadata, not prose - consumers strip or interpret them before treating the body as text. The extraction pipeline in particular removes them before reading prose, so a marking never leaks into an extracted claim.

### Highlights

A highlight marks a span a reviewer judged significant - gold to keep, an example for training or evaluation, or simply something to flag. Highlights are authored in the workbench and stored in the record body, so they survive edits without a drifting sidecar, and they work in every record type.

A highlight is a pair of inline markers sharing a short opaque id:

```markdown
### Cited works

A passage in which the speaker NAMES a work - a book, a report, a film. Records what
was cited, so an acquisition list and a "which claims rest on material we cannot
check" query are both derivable:

```
{{cites-start: [a1, "book", "The Invisible College", "Jacques Vallee"]}}
Vallee's Invisible College describes ...
{{cites-end: a1}}
```

Positions: id, kind, title, optional creator, then zero or more LOCATORS.

`kind` is a closed set: `book` and `web`. Add kinds when one actually appears rather
than inventing them up front.

**A locator is self-identifying by prefix, so it needs no position of its own.**

| Prefix | Means |
|--------|-------|
| `https://`, `http://` | where the work lives on the web |
| `sha256:` | the record for this work in this corpus, once it has been ingested |

```
{{cites-start: [a1, "book", "The Invisible College", "Jacques Vallee"]}}
{{cites-start: [a2, "web", "Glowing Auras and Black Money", "New York Times", "https://www.nytimes.com/2017/12/16/us/politics/pentagon-program-ufo-harry-reid.html"]}}
{{cites-start: [a3, "web", "Glowing Auras and Black Money", "New York Times", "https://www.nytimes.com/...", "sha256:7bf2c20d..."]}}
```

The alternative was a fixed `url` position after the hash, which reads well until a
book needs one: it would carry `""` to reach the position past it. An empty string
standing in for "this kind does not have one" is a placeholder that every consumer
must learn to skip, and each further kind adds another. Locators avoid it because
nothing is positional - a citation carries the identifiers it has, in any order, and
absence is simply absence.

It also extends without a spec change: an `isbn:` or `doi:` is another prefixed
locator, not a seventh position and a new rule about which slots may be blank.

**A URL and a hash are different facts and both may be present.** The hash says the
work IS HERE, and is identity; the URL says where to fetch it. A cited web page is
therefore fetchable in a way a cited book is not - someone can go and ingest it, at
which point the hash joins the URL and nothing already written becomes wrong, which is
the additive property this marker exists to have.

**IT RECORDS THE CITATION, NOT WHETHER WE HOLD IT.** The tempting shape is a marker
meaning "unheld", and it is wrong: whether the corpus holds a work is MUTABLE and the
marker is not. Acquire the book and every such marker in every record is silently
false, with nothing to sweep them - a fact that is true when written and quietly
untrue later, which is the failure mode this format works hardest to avoid. So the
marker states only what the speaker did, which never changes. Held-ness is a QUERY:
does a record exist for this work? Always current, and acquisition adds a hash rather
than invalidating an assertion.

**Distinct from a cross-record link.** A `link` is OUR navigational pointer between
two records and pins a content hash. A `cites` is THEIR act - the speaker named a
work - and may pin nothing. The line is authorship, the same line that separates a
reviewer's span note from the prose it annotates.

**Stripped from the pre-digest**, like highlights and links: the title is in the prose
already and the marker only makes it machine-readable. Where a reviewer wants to add
identification the speaker did not give, that is a span note - domain context about
the material - not this marker, which is infrastructural (see
[data-model.md](data-model.md#domain-versus-infrastructure)).

### External passages

A passage the record QUOTES rather than utters - an inserted clip, an archival
recording, a read-aloud excerpt. The speaker is the person who spoke the words, named
plainly; where those words came from is a property of the PASSAGE, not of the name:

```
<!-- speaker: Buzz Aldrin -->
{{external-start: [a1, "Larry King Live, 1996"]}}
There was this object out there ...
{{external-end: a1}}
```

Elements: an opaque id, a human description of where the passage came from, and
optionally the `sha256:` content hash of the record it came from when that record has
itself been ingested. Description and hash are SEPARATE positions rather than one
slot holding either, so no consumer has to sniff for a `sha256:` prefix to know what
it is holding. Overlap, orphan and nesting behaviour is the highlight rule exactly.

**The speaker is the person, always.** `Buzz Aldrin`, in every record that quotes him,
never `Buzz Aldrin (External Footage)`. Folding provenance into the name conflates WHO
spoke with WHERE it came from, and downstream every spelling becomes a separate
person: the corpus carries `Buzz Aldrin` and `Buzz Aldrin (External Footage)` as two
speakers, Ross Coulthart as four, and one record inverts it entirely to
`External footage (Victor)` - the provenance became the name and the person became the
parenthetical.

**STRIPPED from the pre-digest**, markers and words together, joining highlights and
links. This reverses the original ruling here, which preserved the passage on the
grounds that a clip is often the most load-bearing material in a record. Three
reasons overturned it:

- **The copy is worse than the original.** A podcast replaying NASA's Gemini 7 audio
  transcribes it as one blob attributed to nobody; the same audio is already a record
  in this corpus, segmented across 33 turns with Frank Borman, Jim Lovell and Mission
  Control named. Extracting the copy manufactures unattributed claims from a degraded
  transcript.
- **And then they corroborate the good ones.** One utterance extracted twice is the
  false-independence problem again, and stripping removes it at source rather than
  detecting and collapsing it downstream.
- **Ingesting an original must be purely additive.** Clips are often from material not
  yet released. If a container's extraction includes the clip, ingesting the original
  later puts the same content in the graph from two extractions, and keeping them
  consistent means re-digesting every container whenever that happens. Stripping means
  acquiring an original never makes anything already extracted wrong.

THE COST IS REAL AND IS ACCEPTED: a passage held nowhere else contributes nothing to
the graph. It is not silently lost, though - an external passage with no `sha256:`
hash is precisely a work item, the same acquisition signal a [cited
work](#cited-works) carries, and the discipline it enforces is the right one: if a
clip matters, ingest what it came from, so the corpus only ever extracts from primary
material.

**This does not merge external into `irrelevant`.** They now share a pipeline
behaviour and mean different things. `irrelevant` says "not domain content at all";
external says "somebody else's words, quoted here". Only external keeps the speaker's
name, feeds the acquisition view, and tells a reader the record is SHOWING rather than
asserting.

**What it is FOR is attestation, not tidiness.** Words spoken in a 1996 broadcast were
not uttered in a 2026 podcast, so a claim drawn from the passage belongs to the
original speaker with the quoting record as a relay - `origin` is the person in the
clip, `relay` carries the record that replayed it
([0044](../decisions/0044-claim-provenance-chain-is-required.md)). This needs no new
machinery: 2,507 claims already carry a non-empty relay.

The stake is corroboration. Attribute a quoted clip to the record containing it and
the same clip quoted by three podcasts reads as three independent sources agreeing -
the same inversion that duplicate records produce, where the corpus looks
better-corroborated the more often one statement is repeated. Where the hash is
present and the original is ingested, corroboration counts the original ONCE.

The {{highlight-start: a1}}remote viewers with the NSA{{highlight-end: a1}} were getting this.
```

The id lets highlights **overlap**: two spans that cross are told apart by their ids, so a close matches the right open even when another highlight opened in between.

```markdown
{{highlight-start: a1}}quick brown {{highlight-start: b2}}fox{{highlight-end: a1}} jumps{{highlight-end: b2}}
```

Ids are opaque, unique within a record, minted by the authoring UI (reviewers never type these markers), and **never reused**: a deleted id is never reissued - a new id is always above every id the record has ever *mentioned*, in any overlay construct (a marker, a context edge, or a link payload), including an id that only a retained dangling reference still names. Deletions leave harmless gaps. That makes an id a permanent handle, which every id reference depends on: [context links](#highlight-context-links) between highlights, and the (record-hash + id) address that makes a [cross-record link](#cross-record-links) shareable. A reused id would silently re-point a reference at an unrelated span - and for a cross-record link, from *outside* the record, where no writer could repair it. Non-reuse is what lets the orphan machinery protect a stale reference by leaving it safely dangling rather than silently rebinding.

Non-reuse is enforced across edits by persisting the id high-water in frontmatter, `overlay_next_id`. Without it the guarantee would be a fiction: a counter held only in memory resets on reload, and deriving the high-water from the ids *currently* in the body lowers it when the highest marker is deleted, reissuing that id. Persisting it means neither a reload nor a deletion of the highest marker can lower it. The only property the field carries is that **it only ever increases** - it is the authoring UI's next-id counter, not a decodable index: records may also hold legacy or hand-written ids that are not counter renderings, and the counter simply refuses to collide with them. It is lazily migratable: when absent, derive the high-water from the largest id *mentioned anywhere* in the body - markers and references alike, since a dangling context edge or a link payload can be the only thing still naming an id - then clamp up to the authoring UI's minimum id (a fresh record starts at that minimum, not zero; the exact value is the UI's, kept out of this contract). Overlay ids share **one id space per record** across every overlay construct (highlights, span notes, links, and the references between them), so a single counter keeps every id unambiguous and every reference - in-record and the external `record-hash + id` link address - safe.

**Span extent and orphan handling.** A matched pair is bounded only by its own start and end markers - a highlight may span any range, including across paragraph breaks and speaker turns (a highlight over a multi-speaker back-and-forth is valid). An edit can delete one half of a pair: a `highlight-start` with no matching end auto-closes at the end of the body; a `highlight-end` with no live open is dropped. Parsers on both sides apply this, so a half-deleted marker never corrupts a record.

**Highlights are stripped from the pre-digest and never reach the extraction model.** Unlike the content notes above, a highlight carries no content - it is a reviewer's pointer, an evaluation and curation signal only. Letting the model see it would bias extraction and destroy its value as a blind recall signal ([0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)); the `{{t:}}` timestamp markers are stripped the same way. Authored content notes (`{{...}}`, keyed or keyless) are the exception - they are preserved into the pre-digest as context, exactly as bracket meta-notes are.

This is additive within `anomalica/record/1`: a consumer that does not recognise the markers treats the wrapped text as ordinary content, so it needs no `schema` bump.

### Highlight context links

A highlight can carry a **context link** to one or more *earlier* highlights in the same record that it needs in order to be understood. The case: an early highlight introduces who a person is; a later highlight has them only as "he said..." - the later span depends on the earlier one for its meaning. The link is one-directional and points backwards, and it is untyped - one generic "needs this for context" edge, not a vocabulary of edge kinds (type it later only if real use demands it).

Highlights already carry ids, so a context link is not a new marker pair - it is a small standalone annotation naming ids, reserved key `highlight-context`. Its value is a flow list whose first id is the highlight that needs context and whose remaining ids are the earlier highlights it depends on:

```markdown
{{highlight-start: h7}}he said the craft was recovered intact{{highlight-end: h7}}
{{highlight-context: [h7, h3]}}
```

Here highlight `h7` depends on `h3` - say, the earlier span that named the person `h7` now only calls "he". A highlight may depend on several: `{{highlight-context: [h7, h3, h5]}}`. Because it references ids, not position, the annotation may sit anywhere in the body; the authoring UI places it at the dependent highlight, and reviewers never type it. A referenced highlight can be legitimately deleted, and because ids are never reused ([Highlights](#highlights)) that reference cannot rebind to a different span - it simply becomes unresolvable. A dangling `highlight-context` (its dependent highlight gone, or a target no longer present) is **retained and rendered as unresolved** for the reviewer to decide on, never silently dropped: the intent to link is a signal worth keeping. This differs from a half-deleted highlight *pair*, which auto-closes - that is structural repair of a span, not a semantic reference. These ids are per-record and short; they are NOT usable across records - a cross-record reference uses the [cross-record link](#cross-record-links) form, keyed on `content_hash` + quote, never a bare id.

**Context links strip from the pre-digest with their highlights.** They carry no content and live entirely on the highlights, which are already stripped - so `highlight-context` joins `highlight-*` in the strip-entirely bucket and the model never sees it. No new pre-digest rule.

The point of chains is evaluation. **A chain of context-linked highlights is one gold unit**, not several independent spans: the expected extraction merges the linked spans and *resolves the coreference* - it must name the person the later span only calls "he", using the earlier span. That makes a reviewer's gold a direct measure of cross-passage coreference and attribution on long transcripts - one of the few things that actually separates models on hard content, and exactly what a claim's `speaker` and `refs` have to get right. An extraction must carry the resolved referent across the chain - the person a later span only calls "he" is named from the earlier span, not left as the bare pronoun. How that is scored is the grader's: span recall plus a chain-level attribution check, not an all-or-nothing verdict on the whole chain (a partly-resolved chain must score above a wholly-missed one, or the gold loses the discrimination it exists for). A useful side-effect worth the reviewer knowing: chains remove the pressure to draw one big highlight with an irrelevant interior just to reach the context it needs - reviewers highlight tightly and link, which also keeps the gold clean.

Additive within `anomalica/record/1` - a consumer that does not recognise `highlight-context` ignores it - so no `schema` bump.

### Span notes

A span note attaches free text to a word *range* - "what was on screen here", external context that spans a period the words alone do not carry. It is the ranged counterpart to the keyless point note (`{{laughs}}`, anchored to one spot): a span note has a start and an end the reviewer can drag to re-range.

A span note is a pair of inline markers sharing a short opaque id. `note-start` carries a YAML flow list `[id, text]`; `note-end` carries the id:

```markdown
{{note-start: [a1, "on-screen caption: the witness's own drawing of the craft"]}} ... spanned words ... {{note-end: a1}}
```

The flow list keeps the note flat - no nested braces to confuse the `}}` scan - and the text is quoted per YAML when it contains colons or quotes. Ids are opaque, unique within a record, and minted by the authoring UI; reviewers never type these markers. Overlap, extent, and orphan handling are the same as [Highlights](#highlights): spans are told apart by id and may cross speaker turns and paragraph breaks, an unmatched half auto-closes at the end of the body, and an end with no live open is dropped.

**Unlike a highlight, a span note carries content and is preserved into the pre-digest.** The markers (`note-start` / `note-end` and their ids) are stripped from prose - for search and display, and from the model input - but the note's *text* is re-surfaced into the pre-digest as a context note, exactly like the keyed and keyless content notes, so the model reads it as interpretive context. This is additive within `anomalica/record/1`: a consumer that does not recognise the markers treats the wrapped text as ordinary content, so it needs no `schema` bump.

### Cross-record links

A cross-record link is a reviewer-authored reference from a span in this record to another record - typically to a specific part of it. The use case: an interview mentions a document; that document is ingested as its own record; the reviewer links the mentioning phrase to the document, so a reader (and other content) can follow the reference to the exact passage cited.

It is the third paired-marker `{{ }}` type, alongside [highlights](#highlights) and [span notes](#span-notes), and shares their machinery. `link-start` carries a flat YAML flow list; `link-end` carries the id:

```markdown
{{link-start: [a1, "sha256:7bf2c20d..."]}} the AARO historical record report {{link-end: a1}}
```

with an optional anchor into the target - a verbatim quote from it:

```markdown
{{link-start: [a1, "sha256:7bf2c20d...", "unidentified anomalous phenomena remain unexplained"]}} that passage {{link-end: a1}}
```

The list is flat (no nested braces, so the `}}` scan stays safe), with up to three elements: the opaque **id**, the target's **`content_hash`**, and an optional **target quote**. Ids, overlap, extent, and orphan handling are exactly as [Highlights](#highlights) - spans are told apart by id, may cross paragraph and speaker boundaries, an unmatched half auto-closes at the end of the body, and reviewers never type the markers.

Three rules make a link durable:

- **Target by content hash, never by symlink.** The link pins the target's `content_hash` (`store/{hash}.md`), never its `records/` symlink name - archives move symlinks out from under name lookups. The hash records exactly what was linked.
- **Resolve through supersession at render time.** The pinned hash is stable identity; if the target has since been superseded ([Versioning and supersession](#versioning-and-supersession)), resolution follows the chain to the current record so the link still lands. The pinned hash is what was cited; the chain is how it stays reachable.
- **Anchor by quote, re-derived - the same as a claim.** When an anchor is given it is a verbatim quote from the target, and the precise location within the target (a `HH:MM:SS.d-HH:MM:SS.d` range for a timestamped record, a page or character span for text) is re-derived by aligning that quote against the target - exactly as a claim's `location` is recovered ([digest-format.md](digest-format.md), digester `f4dcab2`), never authored directly. A quote survives the target's re-extraction; a raw offset would not.

**Links are stripped from the pre-digest, like highlights.** A link is a reviewer's navigation pointer, not source content: the `link-start` / `link-end` markers and their payload are removed before extraction, and the spanned prose stays as ordinary text, so the model reads the referring phrase unchanged and extraction is unaffected. Additive within `anomalica/record/1` - a consumer that does not recognise the markers treats the spanned text as prose - so no `schema` bump.

Each link is individually addressable by its id (the source record's hash plus the link id), which is what makes it shareable and referenceable from other content. The shareable URL scheme, and any **backlink** view (a target showing which records link to it, *derived* by scanning forward links, never stored on the target), are the workbench's and site's to render against this contract.

## The bracket meta-notation

A square-bracket note - `[...]` - in the pre-digest is a *description of what is present*, not verbatim source content. It reaches the model as context, and the digester reads it as meta. It appears in two places:

- **Images**, rendered into the pre-digest from the [image annotation](#image): `[image]` alone, `[image: DESCRIPTION]`, and `[caption: CAPTION]`.
- **Transcript event notes** - non-verbal events such as laughter, applause, or an inaudible passage. These are now authored as keyless inline annotations (`{{laughs}}`, `{{applause}}`, `{{inaudible}}`; see [Inline annotations](#inline-annotations)); older records carry the legacy bracket form (`[laughs]`) pending migration. Either records what occurred, not words anyone spoke.

**The load-bearing rule: the meta framing is never a verbatim claim; genuine content described inside it still is.** The digester may use a `[...]` note as context, but must never turn the FRAMING into a spoken or written claim - `[laughs]` never becomes "someone laughed"; `[caption: Credit Getty]` never becomes an attribution claim; a bare `[image]` never becomes a claim. But genuine content that a description transcribes - `[image: the text of a screenshotted tweet]`, `[image: a chart's figures]` - is a real statement the source makes through that image, and stays extractable as a claim, sourced to the image. The brackets frame *where* content came from; the content inside a description is still content.

Because event notes appear only in transcripts (which carry no markdown links) and image notes are generated by the pre-digest with an `image:` or `caption:` prefix, `[...]` meta-notes do not collide with ordinary bracketed prose.

**Relationship to `{{...}}` inline annotations.** Reviewer-authored notes are all `{{...}}` now - keyed when the note has a subject (`{{Fravor: holds up photograph}}`, `{{classification: U}}`) and keyless for a bare event (`{{laughs}}`). The `[...]` bracket form is reserved for two non-authored uses: [speaker descriptions](#square-brackets-mean-this-is-a-description-not-a-name) (`[speaker 3]`, `[interviewer 2]`, `[narrator]`) inside `<!-- speaker: -->` comments, and the image and caption meta the pre-digest renders from image annotations (`[image: ...]`, `[caption: ...]`). A bare `[...]` sitting in a stored record body that is neither of those is therefore *literal source content* (`[sic]`, an editor's `[bracketed]` clarification inside a quote), not an annotation - which is exactly why authored notes moved to `{{...}}`: to stop colliding with the brackets real source text contains. Where they are annotations, both forms are metadata, never prose, and both obey the never-a-verbatim-claim rule above.

## Parser behaviour

1. Extract the first `---` fenced block as frontmatter (standard markdown frontmatter).
2. Find all `<!-- ... -->` HTML comments in the body. Parse the content of each as YAML. All HTML comments are annotations.
3. Text between annotation blocks is content.
4. Within content blocks, scan for `{{...}}` patterns and parse the interior as YAML (inline annotations).

## Output directory structure

```
store/          # hash-named record files (source of truth)
  7bf2c20d...md
  7bf2c20d...verification.json
  e27169e8...md
  _pipeline_versions.yaml   # {media_type: current_version} manifest
  v1/                       # superseded records, retired here
    3211a96e...md
records/        # human-readable symlinks
  2023-07-26-pdf-fravor-written-statement.md -> ../store/7bf2c20d...md
  2020-09-08-video-lex-fridman-122-david-fravor.md -> ../store/e27169e8...md
media/          # extracted images, per-record subdirectories
  11c66b201...
    abc123def4567.png
    f80921a3b56c.jpg
  9a254b6ba...
    abc123def4567.png   # same image, separate copy per record
```

### Store

The `store/` directory contains the actual record files, named by `content_hash`. What `content_hash` hashes per source type, and how it links back to `sources/`, is defined once in the canonical hash chain ([`format-specs.yaml`](../reference/format-specs.yaml), `chain:`) and is not restated here.

**An ingest's own hash does not name its archived original for every type. Resolve
through `source_hash` wherever it is present.** Measured across all 257 live ingests
on disk (2026-08-16), the split is exact and has no exceptions:

| Types | `content_hash` names the original | carries `source_hash` |
|-------|----------------------------------|-----------------------|
| audio, pdf, video (206) | yes, all | none |
| web, ebook (51) | no, none | yes, all |

A resolver consulting `content_hash` alone therefore finds nothing at all for web and
ebook, and gives no sign it looked in the wrong place - it reads as "no original
archived".

**TO ASK WHETHER A FILE IS ALREADY HELD, INDEX BOTH FIELDS.** Hash the file and look
for it under `content_hash` OR `source_hash`; matching on `content_hash` alone answers
"no" for every ebook and every web record, which is exactly the case a
have-we-got-this-already check exists to serve. The invariant is total and can be
relied on: every one of the 17 ebook and 34 web records carries a `source_hash`, and
every one of those 51 originals is present in `records/`. There is no partial-coverage
case to code around.

This shape has now produced four wrong counts in one day, across three sessions. Each
looked like a clean answer; see
[the instrument measured itself](../knowledge/the-instrument-measured-itself.md). If a
count of records touching this seems low, suspect the query before the data.

**The table above is the current state; the rule below is the ratified contract, and
it has not shipped for web and ebook.** Measured 2026-08-16: all 34 web and all 17
ebook records carry `source_hash`, all 206 audio/pdf/video carry none, with no
exceptions - and ebooks extracted on 2026-07-29 and 2026-07-30 body-hash exactly like
the older ones. That is a designed pattern still running, not an unmigrated tail.

So write consumers against the table until the ingester's identity migration lands.
The migration is staged and its move-list is unrun; when it completes, web and ebook
`content_hash` becomes the asset hash and `source_hash` drops out wherever the two
would be identical.

This is the same shape as [0010](../decisions/0010-auditable-assembly.md),
[0040](../decisions/0040-pipeline-versioning-and-supersession.md) and
[0043](../decisions/0043-canonical-provenance-block.md): a decision recorded as
settled while nothing emits it. A ratified rule is not evidence of a running one -
count the field before building on it.

**A record's identity is its source plus its selection, never its extraction output.** `content_hash` hashes the archived source asset's bytes, and - for a [scoped excerpt](data-model.md#record-unit-whole-containers-versus-scoped-excerpts) - the normalised scope string with it. It never hashes the extracted body.

That one rule is what makes re-extraction safe. Improving an extractor, stripping page chrome, fixing chapter numbering, segmenting an email thread: all change the body, none change the source or the selection, so all keep the same `content_hash`. The record is rewritten **in place** at `store/{hash}.md`, and every digest, review sidecar, highlight, and cross-record link bound to that hash survives untouched. Reconciled 2026-07-25; previously web, ebook, and excerpt records hashed their body, so any re-extraction minted a second store entry and silently detached everything keyed to the first.

Two consequences worth stating, because both look wrong at a glance:

- **The record file does not reproduce its own filename.** It never did for audio, video, or PDF - the name comes from the source asset, not from the markdown. This makes the remaining types behave the same way rather than adding an exception.
- **A re-fetch that returns different bytes is a different record**, even when the extracted text is identical. That is correct and it is what [supersession](#versioning-and-supersession) exists for: re-*acquisition* changes identity and is stamped; re-*extraction* does not and is in place. Volatility now sits where the machinery to handle it already is.

Selection is part of identity because one asset can yield several records: two excerpts of one statute must be distinguishable, and they are, by their scope strings. Absent an excerpt directive the scope is empty and identity is the asset alone.

#### Bodies may be edited in place

**Annotation is hash-neutral by construction.** Marking a region irrelevant, adding a span note, correcting a chapter title - the whole reviewer workflow - changes the body and not the identity, because the identity never covered the body. A reviewer edits, the workbench commits back, the file keeps its name, and every digest, sidecar, link, and review span bound to that hash survives.

This is the point of anchoring on the source rather than the extraction. The alternatives all fail: making every edit a supersession prices review at a re-identification per annotation, and hashing "the body with annotations stripped" requires the ingester, workbench, and digester to compute one normalisation identically - a divergence that is silent by nature, which is the failure being fixed rather than a fix for it.

**What in-place editing does put at risk is reproducibility, not identity**, and that has its own mechanism. A digest records the `pre_digest` hash of the exact text the model read ([0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)). Edit a body after digestion and that hash no longer matches - which is how the staleness is *detected* rather than hidden. A digest carrying neither `prompts` nor `pre_digest` cannot detect it, which is one more reason those are re-digested rather than trusted.

Order the work so it does not arise: **edit before digesting.** An annotation applied ahead of a digestion run is simply the text that run reads.

**Records whose stored `content_hash` does not reproduce their body are not a data bug.** They are an artefact of the superseded body-anchored model, and they resolve when identity migrates - the hash stops claiming to describe the body. Do not hand-repair them, and do not compute body digests to reconcile them. Note also that the discrepancy is not attributable to annotation alone: in a 2026-07-30 measurement, 6 of 22 records *without* annotation markers also failed to reproduce their stated hash, so the legacy recipe has a second defect that the migration equally retires.

Idempotency: if `{hash}.md` exists, the ingester skips extraction.

#### Withdrawal: sources we may not hold

The copyright model governs what may be **served**. A separate class governs what may be **held at all**: a rights holder who prohibits reproduction is not satisfied by a gated copy, because the copy is itself the reproduction. Every component would report compliance - the fetch succeeds, the status tags `restricted`, the access gate correctly refuses - while the breach happened at acquisition.

Prospectively this is a **source-registration** decision, not a record field: a source marked no-hold never has an adapter run against it, so no record exists to carry a status. A record that must not exist needs no field. Where a source is mixed - mostly reproducible with a no-hold subset - the marking may be narrowed per document at acquisition, never widened: a document inside a holdable source can be marked no-hold, but a document inside a no-hold source cannot be marked holdable without re-registering the source. Narrowing is safe and reversible; widening is a rights determination and a human one.

Retrospectively - a record already held that later proves no-hold - the requirement is not a status but an **obligation to remove**, and it needs three things the model would otherwise lack:

- **A tombstone at the identity.** Deleting the record alone is self-undoing: the next ingest finds nothing at that hash, re-fetches, and recreates it. The hash must survive as an empty marker carrying the withdrawal reason and date, so idempotency refuses rather than re-acquires. It is also the only place compliance can be evidenced once the content is gone.
- **A third outcome in the [resolution order](#versioning-and-supersession).** A consumer holding the old hash currently resolves live, then retired, then reports a dangling reference. Withdrawal adds *withdrawn* - resolvable, deliberate, and distinct from both a live record and a broken pointer, so a cross-record link renders "removed for rights reasons" rather than failing as though something were lost.
- **Traversal of what the record produced.** Removal is not complete while the claims, digests, pre-digests, briefs, and article text derived from it remain. That the chain is traversable at all is a consequence of the audit binding built for reconstructability ([content-format.md](content-format.md#auditable-assembly)) - the same links that answer "what was this article built from" answer "what did this record contribute to".

One property makes this harder than deletion: **the store is version-controlled.** Removing a file from `ingests` does not remove it from git history, so an obligation to remove is not discharged by a commit that deletes. Whether that requires history rewrite, and how far the obligation extends into derived artefacts already published, is a rights question to settle per instance rather than a rule to fix here - but it must be settled, not assumed handled.

Sidecars live next to the record in `store/`, named `{content_hash}.<kind>.json`:

- `{hash}.verification.json` - cloze proof-of-possession challenges (ingester's
  `shared/verification.py`; consumed by the workbench access gate). Present only
  for records whose copyright status gates access.
- `{hash}.review.json` - review-coverage spans and the reviewer verdict
  (`anomalica/review-coverage/N`, written by the workbench). **There is no
  review gate.** Nothing in the digester enforces the verdict - extraction
  never consults it, and `assess_record` is reached only from the
  `coverage` reporting command. Review is informational, exactly as
  [0021](../decisions/0021-content-review-lifecycle.md) and
  [0031](../decisions/0031-per-record-inspection-pages.md) require of every
  other review signal. Corrected 2026-07-29; this document and the
  workbench both previously described a gate that was never built.
- `{hash}.highlights.json` - relevance-tuning ground truth
  (`anomalica/highlights/1`, written by the workbench tuning mode; read by the
  digester's grader). Span offsets are Unicode code points into the raw stored
  body (the verbatim text after the closing frontmatter fence); `body_sha256`
  pins the exact body the offsets index. See
  [relevance-tuning-mode](../decisions/drafts/relevance-tuning-mode.md).

### Versioning and supersession

Three orthogonal axes describe a record's generation, defined in full in
[0040](../decisions/0040-pipeline-versioning-and-supersession.md):

- `schema` (`anomalica/record/N`) is the on-disk FORMAT. A record/1 is not stale
  merely because record/2 exists as a format.
- `processing.pipeline_version` (an integer, per media type) is the extraction
  GENERATION. A record whose value is PRESENT and below the current version for
  its media type is STALE: a consumer badges it "outdated (vN of M)" and it is a
  backfill target, but it is still shown - it is the best available until
  re-ingested. An ABSENT value means "generation not declared" - no badge, not
  treated as 0 (so introducing the field does not flag the whole corpus). The
  current version per media type is published in `store/_pipeline_versions.yaml`
  (`{media_type: current_version}`), upserted by the ingester on every run.
- `processing.version` (the ingester's git short-hash) is fine-grained
  provenance, unchanged.

**Supersession** retires a prior record when a source is re-ingested, keyed on
LOGICAL source identity (`provenance.identifiers`, then `provenance.source_url` - the only identity
stable across re-downloads; a per-download `content_hash` is not). The new record
carries `supersedes: <old_content_hash>`; the prior record is stamped
`superseded_by: <new_content_hash>`, moved from `store/{hash}.md` to
`store/v1/{hash}.md`, and its `records/` symlink removed. The frontmatter flag is
the source of truth - a consumer HIDES any record carrying `superseded_by` (one
visible record per source); the `store/v1/` location is a derived convenience so
a non-recursive `store/*.md` glob excludes retired records. Supersession is
stamped across schema boundaries (a record/2 supersedes a record/1 of the same
source). It applies only when re-acquisition changes the `content_hash` (a fresh
download, or a web/ebook body change); re-extraction from the SAME asset keeps
the hash and is an in-place update at `store/{hash}.md`, not a second record. So
the browse list is always one-per-source.

**Retire by moving, or mark in place - the discriminator is downstream pointers.**
Move to `store/v1/` where nothing holds the old hash. **Mark in place** - leave the
file at `store/{hash}.md` carrying `superseded_by` - where something does, because
the digester's redigest resolver reads bodies by `content_hash` and a body that is
merely *absent* is a silent drop rather than an error. `superseded_reason` records
which case applied and why, in prose. Two live records are marked in place on exactly
this ground.

**`store/v1/` holds stamped supersessions and nothing else.** A file there without
`superseded_by` is not a retired record, and a consumer following the resolution
order will read it as one. As of 2026-08-16 it holds three different things: 6 stamped
supersessions, 154 retired extractions carrying no `superseded_by`, and **120
frontmatter-only intake-queue stubs** with no `content_hash` and no body - carrying
`intake_date`/`ingested`/`ingested_at` and `source_type` values (`webpage`,
`document`) outside the valid set. Something still writes them; one landed at 02:02
on 2026-08-16.

Two consequences, both live: a consumer resolving a missing record falls through to
`store/v1/` and gets a title with no body and no hash, which reads as a retired
record rather than a queue artefact; and **14 hashes hold a file in both tiers** (11 one-byte stubs plus three others), so `store/{hash}.md` and `store/v1/{hash}.md` name the same address with a
1-byte stub at one end. The stubs do not belong in the retirement tier - that is a
writer to fix, not a rule to relax.

**The `.v2` suffix is 65% of the corpus, not scaffolding.** 167 of 257 live records
carry `.v2.md`, mapping exactly onto `schema: anomalica/record/2` with no overlap. A
consumer building `store/{content_hash}.md` therefore misses two thirds of the corpus
and gets no error - the file simply is not there. The canonical path is
`store/{content_hash}.md` and the schema version belongs in frontmatter, where it
already is; a filename must not encode it. **Until the collapse runs, glob both.**
One check before collapsing: no source may hold a `.md` and a `.v2.md` at the same
hash, or the rename collides. See
[0040](../decisions/0040-pipeline-versioning-and-supersession.md).

### Records

The `records/` directory contains symlinks with human-readable names, pointing into `store/`. The naming convention is:

```
{date}-{source_type}-{slugified-title}.md
```

For example:
- `2023-07-26-pdf-fravor-written-statement.md`
- `2020-09-08-video-lex-fridman-122-david-fravor.md`
- `2024-08-20-ebook-imminent.md`
- `2009-pdf-nimitz-executive-summary.md`

The date, source_type, and title are taken from the record's frontmatter. The symlinks are regenerated from the store contents and can be deleted and rebuilt at any time.

### Media

The `media/` directory holds images extracted from sources (currently EPUB; PDF, web, and video frame extraction will follow). Layout:

```
media/{record_hash}/{img_hash}.{ext}
```

`record_hash` matches the record's filename in `store/`. `img_hash` is a 12-character SHA-256 prefix of the image bytes. `ext` is the source-supplied extension (`png`, `jpg`, `gif`, `svg`, `webp`).

Each record's images live in their own subdirectory. Images shared across records are duplicated rather than shared - see the [Image annotation](#image) section for the rationale.

A record's `media/` directory is omitted entirely when the record has no extracted media. Consumers should not assume every record has one.

Copyright status follows the parent record. If `copyright.status` is `licensed` or `restricted`, the images stay private. The assembler copies images into `content` only for records eligible for public serving (`public_domain`, `open_licence`, `publicly_accessible`).

## Examples

### PDF document

```markdown
---
schema: anomalica/record/1
title: "David Fravor Statement for the House Oversight Committee"
source_type: pdf
provenance:
  publisher: "House Oversight Committee"
  creators:
    - David Fravor
  published_date: 2023-07-26
  source_url: https://oversight.house.gov/...
content_hash: sha256:7bf2c20d...
pages: 3
---

<!-- file_page: 1 -->

David Fravor Statement for the House Oversight Committee.

I first want to thank you for the invitation to speak to this
committee on the UAP topic that has been in the news for the past
6 years and seems to be continuing to gain momentum.

<!-- file_page: 2 -->

As we proceeded to the west and as the air controller counted down
the range, we had nothing on our radars and were unaware of what
we were going to see when we arrived.

<!-- file_page: 3 -->

In closing, I would like to say that the Tic Tac Object that we
engaged in Nov 2004 was far superior to anything that we had at
the time, have today, or are looking to develop in the next 10+
years.
```

### Video transcript

```markdown
---
schema: anomalica/record/1
title: "Lex Fridman Podcast #122 - David Fravor"
source_type: video
provenance:
  publisher: "Lex Fridman"
  published_date: 2020-09-08
  source_url: https://youtube.com/watch?v=aB8zcAttP1E
  identifiers:
    youtube: aB8zcAttP1E
duration: 7200.48
content_hash: sha256:e27169e8...
---

<!-- speaker: [speaker 1] -->
00:01:23.0 So tell me about what happened in 2004.
00:01:25.4 You were a Navy pilot stationed on the Nimitz.

<!-- speaker: Speaker 2 -->
00:01:45.2 We had been at sea for roughly two weeks.
00:01:48.7 I was the Commanding Officer of Strike Fighter Squadron Forty-One.
00:01:53.1 We were at the beginning of our workup cycle.

00:01:56.4 {{action: Fravor gestures to indicate the size of the object}}
00:01:58.1 It was about the size of an F-18, roughly 40 feet long, with no wings, no exhaust plume.
```

### Freedom of Information Act document with redactions

```markdown
---
schema: anomalica/record/1
title: "Incident Report"
source_type: pdf
provenance:
  published_date: 2004-11-14
pages: 5
---

<!-- file_page: 1 -->

# Incident Report

On {{redacted: ~11 chars, (b)(1)}}, personnel at {{redacted: (b)(6)}}
observed an unidentified aerial object in restricted airspace.

<!--
redacted:
  extent: paragraph
-->

The object was tracked on radar for approximately 12 minutes
before {{redacted: ~26 chars, (b)(1)}}.

<!-- file_page: 2 -->

<!-- image: Grainy black and white photograph showing a small oblong object against a featureless sky. No scale reference visible. -->

The following personnel were present during the observation:

| Name | Rank | Role |
|------|------|------|
| {{redacted}} | Commander | Officer of the Watch |
| {{redacted}} | Lt. | Radar Operator |
```
