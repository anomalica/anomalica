# Review Workbench

A private web application for reviewing and structuring Records and Ingests and
applying replayable graph curation. Digest-selection review remains planned with
the unimplemented selector. The Workbench is not a public provenance service or
part of the main site.

## Purpose

**Review and correction.** The pipeline produces ingests (structured text from source material) and digests (extracted claims and nodes). Both need human review to catch errors - misidentified speakers, wrong timestamps, irrelevant content, misclassified claims. The workbench provides a purpose-built interface for this work, rather than asking reviewers to edit raw markdown files.

**Public transparency is a site concern.** Stable public Record pages expose safe
provenance and claim anchors. The Workbench may inspect private source material and
review data, so it runs locally or behind reviewer authentication and is never the
anonymous reader surface.

## Technology

**Frontend:** A plain Svelte 5 single-page application built with Vite. No meta-framework (not SvelteKit) - the workbench has no need for server-side rendering, file-based routing, or a Node.js server. Svelte compiles components to plain JavaScript at build time, so there is no framework runtime in the browser. This keeps the application lightweight and reduces the attack surface.

**Styling:** Tailwind CSS v4 with shared design tokens imported from brand. Panel contents use container queries (`@container`) rather than viewport breakpoints, so components adapt to their panel width as users resize the layout.

**Backend:** A minimal Python service (FastAPI) that reads from and writes to the git repositories. Python because the rest of the pipeline (ingester, digester) is Python, allowing shared libraries for record parsing and validation. The backend is a thin layer between the frontend and git - it has no database of its own. In production, FastAPI serves both the API and the built static frontend files.

**Development:** During development, Vite's dev server proxies `/api` requests to the FastAPI backend running on a separate port. This avoids Cross-Origin Resource Sharing configuration.

**Storage:** Two git repositories hold the pipeline output:

- **ingests** (access-gated) - the structured text output from the ingester. Access
  is resolved independently for every selected Asset, not by one Record-level
  status: public-domain and openly-licensed members are freely accessible to an
  authenticated reviewer, while gated members require exact possession or an
  explicit grant. The repository itself is access-controlled; the Workbench
  backend serves one authorised view at a time.
- **digests** (public) - contains extracted claims and nodes. Reviewers influence
  the replayable selector or graph-curation inputs; ordinary review does not edit
  model digests directly.

The backend has no database of its own. The git repositories are the storage.

**Access model:** Every Workbench user is an authenticated reviewer. Source access
is then checked per Asset through public rights, trusted-local access, exact-Asset
possession proof or an explicit grant. For a multi-Asset Record, access to one
member never unlocks another; showing the complete Ingest or composite original
requires authority for every contributing member.

**Authentication:** OAuth implemented directly in FastAPI using Authlib (a lightweight BSD-3 licensed Python library). No external identity service or self-hosted identity platform. The workbench supports multiple OAuth providers - initially just the git hosting platform (such as GitHub), with others (Google, etc.) addable in about 20 lines of Python each.

The OAuth flow:

1. Reviewer clicks "log in" in the workbench
2. Browser redirects to the FastAPI `/login` endpoint
3. FastAPI redirects to the OAuth provider's authorisation page
4. Reviewer authorises, provider redirects back to FastAPI with a token
5. FastAPI extracts the reviewer's name and email, sets a session cookie
6. The Svelte frontend reads the cookie and includes it in subsequent requests

No authentication library is needed on the frontend. It is just a redirect and a cookie.

For the initial phase with a small number of reviewers, Workbench access is
controlled by an email allow-list on the backend. The digest repository remains
public independently, but browsing it does not create an anonymous Workbench
session or grant source access.

**Supply chain discipline:** The workbench handles sensitive source material, so dependency management matters. Every third-party library added is a trust decision. The framework choice (plain Svelte over heavier alternatives) and the preference for platform APIs over libraries reflect this priority. Key dependencies are limited to:

- **PaneForge** - resizable panel layout (Svelte 5 native)
- **pdfjs-dist** - PDF rendering (Mozilla, framework-agnostic)
- **hash-wasm** - streaming file hashing via WebAssembly (for copyright verification of large files)
- **Authlib** - OAuth protocol handling on the backend (BSD-3 licence, single dependency)

Video and audio playback uses native HTML5 media elements with Svelte's built-in element bindings (`bind:currentTime`, `bind:paused`). No media player library.

**State management:** Svelte 5 runes (`$state`, `$derived`, `$effect`) with class-based stores in `.svelte.ts` files. No external state management library.

## Three-panel view

The workbench presents three layers of the same record side by side:

1. **Original source** - the raw material (video player, PDF viewer, audio player, rendered web page). This is uploaded by the reviewer from their own copy.
2. **Ingest** - the structured text the ingester produced, with speaker turns, timestamps, page boundaries, and annotations.
3. **Digest** - the claims and nodes extracted from the ingest, with claim types, attestation levels, speaker attributions, and node references.

A fourth element shows **where the digest's claims ended up** - links to all assembled articles that reference claims from this digest.

The three panels are resizable using PaneForge, which supports nested panel groups and keyboard accessibility. Each panel is a container query boundary, so its contents adapt to whatever width the user drags the dividers to.

## Infrastructure view

Extraction splits every record in two. Domain claims go to `knowledge.db` and become articles; **infrastructure claims** - what a source says about its own sources - go to `infrastructure.db`. That second database had no consumer at all until the workbench's Infrastructure tab: 1,830 claims and 9,605 nodes written on every import and never read.

Followed through its claim-to-node references it is a bibliography. 800 works, 994 people and 356 organisations, linked by who wrote what and who cited whom - "American Cosmic cites Jeremy Sconce's Haunted Media", "Leon Festinger, Henry Riecken and Stanley Schachter wrote When Prophecy Fails". So the view is organised around works rather than claims, with people, organisations and the raw claim list alongside.

Each named work carries a **shelf-check**: whether the corpus holds it. Of the 800 named, it holds 25. The remaining 775 are a reading list the material assembled about itself, and the most likely next use of this data is as an acquisition list.

Two things the view is careful about:

- **`administrative` is not a defect category.** 1,469 of the 1,830 claims are typed `administrative`, which is what a bibliography is made of. The other 361 were typed as observation, testimony or hearsay - types the extraction usually reserves for the domain half. They sort to the top because that is where a mis-filed domain claim would be found, but the claim type does not determine the split (the digester assigns the section, and the type independently), so this is a heuristic and the view says so.
- **20 of the 800 works are the same work listed twice.** `Communion` and `Communion (Whitley Strieber book)` are separate nodes, so the counts report them twice. The assimilator's merge ledger would fold them, but replay is only ever passed the domain connection - it has never reached `infrastructure.db` and a merge recorded today would not either. The view names the duplicates rather than reporting one work as two in silence.

  Two of the ten clusters are not the parenthetical class. `Go Fast video` / `Go-Fast Video` differ only in punctuation and case. `UFO Danger Zone` / `Unidentified Flying Object (UFO) Danger Zone` is the corpus's own acronym convention, unfolded because the assimilator's acronym rule is anchored to the end of the name: a name ending at its acronym folds, one that continues past it does not. Fuzzy matching does not rescue that pair either - `ufo` is a domain stopword, so one side is left with orphan tokens and the other with none, and the matcher requires orphans on both sides to declare disagreement. The workbench's own title matcher is deliberately not anchored, which is why the tab pairs them.

- **The read is read-only.** `infrastructure.db` is derived and rebuilt from the digests on every import, so a correction written there would not survive. Recategorising a claim belongs in the curation ledger the assimilator replays, keyed on `claim_fingerprint` scoped by record content hash - not on `claims.id` (fresh per emission) or `claim_hash` (which includes resolved graph ids and moves when node resolution moves). No correction action is built yet.

## Copyright handling

The Workbench may serve extracted text from copyrighted source material to
authenticated reviewers who demonstrate access to every required Asset. It is not
a distribution channel. What is shown depends on each Asset's authority (see the
[source types and copyright decision](../decisions/drafts/source-types-and-copyright.md)).
The accepted target protection is layered. The deployed legacy endpoints do not
yet satisfy it; the launch blockers below are normative, not an assertion that the
current server is safe for public exposure:

1. **Authenticated, allow-listed session** - only the Workbench backend service account has direct repository access; every human request has an authenticated reviewer identity.
2. **Per-Asset gate** - public rights, trusted-local access, a successful nonce-bound byte-range proof or an explicit grant is checked independently for every member required by the requested output.
3. **Manual access grants** - where exact-byte verification is impractical, a grant binds one authenticated user to an explicit set of Asset hashes and uses; a per-Record grant is insufficient unless it enumerates every member.
4. **Rate limiting (pre-public requirement, not yet implemented)** - challenge issue and submission endpoints throttle attempts and use short-lived, single-use challenges; not live today (see [Pre-public hardening](#pre-public-hardening)).
5. **Public hashes are identifiers, not credentials** - digests and graph anchors carry full Asset hashes so evidence sites are verifiable. Knowing a hash identifies the challenge target but never satisfies it or grants source access.

### Record and Asset identifiers

The public identifier is the first 56 hex characters of the domain-separated
Record `content_hash`. It is safe to publish and cannot equal a raw Asset hash
under the specified codec. Full Asset hashes are also public evidence identities,
not possession keys. Possession is established by a short-lived
`anomalica/asset-possession-challenge/1` byte-range challenge. The authenticated
server selects unpredictable ranges from the archived Asset; the browser hashes
the nonce, encoded ranges and exact local bytes. Neither public hashes nor quoted
text reveal that proof.

A Record may require several possession checks. The backend evaluates every Asset
member needed for the requested body or original and returns nothing unless all
are authorised. One successful challenge cannot unlock another member, another
Record's private derivative, or an entire bundle. Public rights are evaluated by
the same per-Asset rule, independently of possession.

### Pre-public hardening

Three server-side protections this design assumes are NOT implemented today and
are pre-public launch requirements:

- **Replace hash and cloze submission.** Implement `POST
  /api/assets/{asset_hash}/possession-challenges` and `POST
  /api/assets/{asset_hash}/possession-challenges/{challenge_id}/verify` with the
  exact schemas and codec below. A submitted Asset hash or legacy cloze answer
  never creates authorisation.

- **Rate-limiting** on challenge issue and challenge-verification endpoints as
  ordinary defence in depth. Public Asset identity does not weaken this control:
  byte-range proofs, not hashes, grant access.
- **Gate-enforced fetch.** `GET /api/ingests/{hash}` and `GET /api/sources/{hash}` are not gate-enforced server-side today (dev-mode ungated); until they are, the hash gate and copyright gating are advisory, not enforced.

All three must land before any public exposure.

### Flow

An authenticated reviewer identifies each required Asset and selects their local
copy; source bytes are never uploaded. The server creates a single-use challenge
bound to session, Asset hash, requested use and an expiry no more than five minutes
away. It returns a 256-bit nonce and 16 cryptographically random, non-overlapping
byte ranges totalling 64 KiB, or all bytes in one range for a smaller Asset. The
browser computes the exact proof defined in
`anomalica/asset-possession-challenge/1`; the server independently computes and
constant-time compares the expected proof from its archive. Success creates only
the challenge-bound session authorisation until its expiry; the client then retries
the intended endpoint. A composite fetch requires every member's independent gate
to pass before returning the Ingest.

### Operational requirements

Because public hashes identify evidence rather than authorise access, two rules are
non-negotiable:

- Asset challenge lookup accepts only a complete canonical hash; prefix search is
  never exposed.
- A challenge is bound to authenticated session, Asset, use and expiry, is
  single-use, and reveals only nonce, offsets and lengths, never expected proof or
  gated source bytes.

The existing edge and backend implementations that accept a submitted SHA-256 as
immediate proof do not satisfy this contract. Legacy cloze sidecars also do not
satisfy it because public evidence quotations may disclose answers. Both paths are
pre-launch-only and must be replaced before any public digest or graph containing
Asset hashes is published or any Workbench endpoint is exposed.

The deployed whole-Markdown update routes are also not `record/3` writers: they
protect only legacy top-level rights and do not recompute Selection identity. A
conforming writer parses the current envelope server-side, rejects reviewer edits
to `content_hash`, `assets`, `selection`, `page_map` and authoritative
`assets[].copyright`, and uses separate administrator or structural operations for
those fields. No public deployment may accept client-supplied full Markdown that
can alter identity-bearing or rights-authoritative fields.

Rate limiting is a load-bearing security control, not just an anti-abuse measure, and should be tested as such.

### Scope

This approach works for any source material the reviewer can obtain independently: videos downloadable from YouTube, publicly available PDFs, books they own, podcast episodes. It does not work for material the reviewer cannot access, but in those cases only people with existing access would be reviewing anyway.

## Review tasks for video and audio

Video and audio records are the most labour-intensive to review because automatic speaker diarisation (identifying who is speaking when) is imperfect. The workbench supports:

- **Speaker merging** - the diarisation may split one person into multiple speaker identities. The reviewer merges them.
- **Speaker identification** - assigning names to unidentified speakers, confirming or correcting automatic identifications.
- **Marking irrelevant sections** - flagging content that doesn't belong in the record (via the `[irrelevant]` speaker token) so the digester skips it. The audio/video cases - ads, sponsor reads, intro/outro filler, "next time on..." previews, off-topic tangents - are one category of the canonical [What to mark irrelevant](#what-to-mark-irrelevant) list, which covers every record type.
- **Timestamp correction** - adjusting speaker turn boundaries where the diarisation placed them incorrectly.
- **Playback alongside transcript** - the video or audio plays in sync with the transcript, making it easy to verify what was said against what was transcribed.

Video and audio playback uses the browser's built-in HTML5 media elements. Syncing playback position with the transcript uses Svelte's reactive bindings on the media element's `currentTime` property. Clicking a transcript line seeks the media to that timestamp; as media plays, the active transcript line is highlighted and scrolled into view.

## Review tasks for all record types

### Split and compose Records

The accepted structural target can split one temporary parent into several child
Records or compose one Record from several Assets; the deployed Workbench does not
yet implement these routes. The first implementation will accept only complete
physical PDF pages and whole standalone images. The client submits ordered
selections and editable metadata, never generated body text, hashes, page maps or
archive paths. The server derives preview and commit from one compare-and-swap
bound Git ref, validates every Asset/page/source map, expands ranges to atomic
selectors and derives the sequential Record `page_map`.

Each parent must be live and explicitly carry `structure_status: temporary`.
Commit creates every child or composite as final and retires all parents atomically. A
failed validation or stale ref writes nothing. Structural one-to-many lineage is
separate from scalar `superseded_by`. Parent review, housekeeping, gold,
verification, digest and graph sidecars do not inherit mechanically. A missing
exact source map blocks the operation. Any separately authorised re-extraction
must complete first; preview and commit invoke no provider and never fall back to
a rough model location. Composition uses
already extracted Asset/page blocks and never synthesizes a PDF.

- **Claim review** - verifying that extracted claims accurately represent what the source says. Correcting misinterpretations, wrong speakers, incorrect claim types or attestation levels.
- **Node review** - verifying that people, organisations, projects, places, events, objects, documents, and topics were correctly identified and linked. Correcting misidentifications or creating new nodes.
- **Flagging missing claims** - noting claims that the digester missed and should have extracted.
- **Removing irrelevant claims** - marking claims that were extracted but add no value (pleasantries, filler, off-topic asides).
- **Marking irrelevant content** - flagging whole source sections that are not domain content (front matter, marketing, bibliographies, and the rest) so the digester skips them before extraction. See [What to mark irrelevant](#what-to-mark-irrelevant).

The review interface uses structured forms rather than raw text editing. Reviewers correct speaker names via dropdowns, adjust timestamps with controls, and change claim types and attestation levels through purpose-built inputs. This is more usable than editing YAML directly and reduces the chance of formatting errors.

The intake queue is not a record or review stage. Workbench presents only valid,
scheduler-owned transient `queue/*.md` stubs as pending intake, using the field
and lifecycle contract in [ingest-format.md](ingest-format.md#intake-queue-lifecycle).
It excludes every Git-tracked legacy queue file, every completion-stamped stub
and every candidate whose canonical source identity already resolves
unambiguously to a live record. It never derives review state from queue fields.
Duplicate transient candidates or ambiguous live-source matches are shown as
blocked data errors, not silently deduplicated or selected. Workbench does not
edit, stamp, commit or delete queue files; verified-result cleanup belongs to
the scheduler.

Before entering or saving ingest editing, the UI reads
`GET /api/ingests/<64-lowercase-hex-content-hash>/housekeeping`. The backend
resolves one current ingests Git ref and reads the record, sidecar and root
`housekeeping-algorithm.json` manifest from that same tree. Its
`anomalica/housekeeping-view/2` envelope is a strict tagged union on `access`.
A caller allowed to read the record receives `access: full` with exactly
`schema`, `access`, `viewed_sidecar_sha` (the committed backing blob id, null
only when absent), `viewed_ref`, `viewed_content_hash`, the valid sidecar's
immutable `viewed_input_sha256` and `viewed_result_sha256` (both null when the
sidecar is absent or invalid), the
manifest's `viewed_algorithm_version`, `review_state`, `due_reason`,
`outstanding_count`, sorted `scopes`, `deep_link`, raw committed `sidecar` (null
when absent or unreadable), and derived `previews` keyed by item id. `deep_link`
is `/housekeeping?record=<64-lowercase-hex-content-hash>`. Preview data is never
inserted into or written back with the sidecar.

A possession-gated caller who has not passed every required Asset challenge receives only
`schema`, `access: summary`, `review_state`, `due_reason`, `outstanding_count`, sorted
`scopes`, `deep_link` and `sidecar: null`. These are permitted processing
metadata. The summary exposes no `viewed_*` identity, item, old/new token, byte
span, evidence or preview. After successful Asset proof submissions for the
`review` use, retrying the GET returns the full view while those session-bound
authorisations remain unexpired. No durable unlock state is created.

Versions 1 and 2, and missing, malformed, result-mismatched or
algorithm-mismatched sidecars are due and have no current outstanding
proposals. The exact review-state vocabulary is `due`,
`pending-deterministic`, `failed-deterministic`, `pending-research`,
`failed-research`, `needs-decisions` and `ready`. A missing pass key is pending,
not running; a failed pass remains blocked and retryable. A processing-complete sidecar's
`status: proposed` items are outstanding. When due, `outstanding_count` is zero
and `scopes` is empty.
`due_reason` is one of `missing-sidecar`, `invalid-sidecar`,
`unsupported-schema`, `result-mismatch` or `algorithm-mismatch`.
A missing, malformed or non-canonical algorithm manifest is not a record state:
the endpoint fails closed with service unavailable rather than claiming current or due.
Scheduler dispatch separately fails closed when the worker's reported version
differs from that manifest.

The UI shows the outstanding count and affected scopes with that direct link, or
shows deterministic/research progress and the authenticated waiver action. For
an unreviewed record it blocks entry into content review until `review_state` is
`ready`: deterministic is complete, metadata research is complete or waived and
every item is decided. Records whose human review already started or completed
are excluded before housekeeping state is evaluated; their existing review may
continue and automatic housekeeping does not run. Changed bytes outside the
final housekeeping decision make the prior sidecar stale; reconciliation
discovers the new tuple. See [decision
0048](../decisions/0048-post-ingest-housekeeping-is-content-versioned.md).

`POST /api/ingests/<64-lowercase-hex-content-hash>/housekeeping/decide` requires
an authenticated reviewer and sends only `schema:
anomalica/housekeeping-decision/2`, `viewed_sidecar_sha`, `viewed_ref`,
`viewed_content_hash`, `viewed_input_sha256`, `viewed_result_sha256`,
`viewed_algorithm_version` and a complete `decisions` list of `{item_id,
status}` covering every proposed item exactly once. The server requires every
viewed identity to remain current and reloads the manifest, sidecar, record and
each named proposed item from that ref; it never accepts operation fields from
the client. It also requires deterministic completion and metadata-research
completion or waiver. Versions 1 and 2, unknown, duplicate, omitted, changed or already-decided
items are refused without a partial decision. Every stale, validation, guard or
ref failure leaves the record, sidecar and statuses unchanged. Successful
decisions atomically commit every approved record edit, final item statuses,
`result_sha256` and ordered `decisions` audit under the authenticated reviewer
identity.
The decision endpoint accepts only identities from an `access: full` view.

`POST /api/ingests/<64-lowercase-hex-content-hash>/housekeeping/waive-research`
is a separate authenticated action bound to a pending- or failed-research view.
The client sends only the viewed identities and a non-empty reason. The server supplies
reviewer identity and time, records `{by, at, reason}` in the metadata-research
pass, and applies no proposal or record edit.

## What to mark irrelevant

The single canonical list of what a reviewer marks irrelevant, for every record type - books, PDFs, web pages, audio, video. The marker syntax is in [ingest-format.md](ingest-format.md#irrelevant-content) (a prose region marker for text records, the `[irrelevant]` speaker token for transcripts). Marking is non-destructive: the text stays in the record and is only excluded from extraction ([decision 0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)), so err toward marking anything that is not content.

**Principle.** Mark irrelevant anything that is NOT domain-knowledge content about the subject - anything that is not a substantive claim or fact about the anomalous-phenomena topic. Keep the actual content; exclude the apparatus around it.

- **Self-promotional / marketing** - about-the-author blurbs, jacket and cover copy, "praise for this book", author bios. These make factual-sounding claims with the weakest possible provenance - the book vouching for itself - so extracting them launders marketing into the graph. If an author's standing ever matters for weighting, it comes from INDEPENDENT sources, never from the jacket.
- **Copyright / legal / publication apparatus** - copyright pages, disclaimers, permissions, ISBN and publication data, "all rights reserved".
- **Navigation / structural apparatus** - tables of contents, indices, page-number lists, running headers and footers.
- **Source apparatus** - bibliographies, endnotes, and footnote CITATION lists. The citations are sources, not claims; per-chapter numbering and Ibid chains make them low-value and hard to resolve (see the parked endnote-mining work). Exception: a discursive note that adds genuine content is pulled inline, case by case.
- **Front- and back-matter filler** - dedication, half-title, colophon, and usually acknowledgements.
- **Audio / video filler** - ads, sponsor reads, intro/outro filler, "next time on..." previews, off-topic tangents.

This is the human counterpart to the digester's model-prep: what a reviewer marks here is exactly what the pre-digest strips before extraction, so the model never reads it.

## How corrections are saved

When a reviewer submits corrections, the workbench backend commits the changes to the appropriate git repository using a service account. The commit records the reviewer's identity using git's author/committer separation:

Every ordinary ingest-edit read returns `base_record_sha`, the Git blob id of
the displayed record, and `base_ref`, the commit whose tree supplied it. The
frontend echoes both on `PUT
/api/ingests/<64-lowercase-hex-content-hash>`. The backend rejects a changed ref
or blob with conflict before writing; it never applies stale whole-record
browser content over a newer edit.

- **Author** - the reviewer (name and email from their OAuth profile). This is the person who made the correction.
- **Committer** - the workbench service account. This is the system that applied the change.

This is the same convention used by git hosting platforms when merging pull requests - the author did the work, the committer applied it. Any git client displays both fields.

**Ingest corrections** (speaker merges, timestamp adjustments, marking irrelevant
sections) are committed to the access-controlled ingests repository. Reviewers
interact only through the Workbench, which applies authentication and independent
Asset rights, challenge or grant checks before serving a view.

**Digest findings** cause re-digestion or a graph-curation operation. When the
planned selector lands they may also create a replayable selector preference.
Ordinary review does not edit model digest output in place.

The git history provides the full audit trail: who changed what, when, and why. The workbench shows reviewers the diff of their changes before they submit, and displays the history of corrections to each record.

## Review identity across re-ingestion

The authoritative review is `store/{content_hash}.review.json`. Stable Record
identity locates the sidecar; `reviewed_body_sha256` binds the verdict to the exact
parsed Ingest body. A metadata-only commit preserves currentness when that body is
unchanged. A changed body makes the verdict stale, and unresolved
`review_carryover` independently requires verification.

URL, Asset hash and historical `Reviewed-Record:` trailers are migration evidence,
not current review authority. They never transfer a verdict to a different
Selection. Structural children and composites begin without review state even when
all their parent pages were reviewed, because ordering and body boundaries changed.

Public-page eligibility requires a valid version-1 sidecar with coverage exactly
1.0, `digestible: true`, positive `total_units`, a current body binding and no
unresolved carryover. Partial current review remains visible in the private
Workbench but does not expose generated claims publicly.

## Relationship to the main site

The workbench is a separate application with a different audience (reviewers) and different requirements (video playback, interactive editing, file upload). It is not part of the main Anomalica site, which serves assembled articles to readers.

The two applications share the same data: the workbench reads and writes ingests and digests, the main site reads assembled articles produced from those digests. They do not need to be on the same domain or infrastructure.
