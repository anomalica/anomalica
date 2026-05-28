# Review Workbench

A separate web application that serves two purposes: reviewing and correcting ingests and digests, and providing public transparency into the full extraction pipeline. Not part of the main site.

## Purpose

**Review and correction.** The pipeline produces ingests (structured text from source material) and digests (extracted claims and nodes). Both need human review to catch errors - misidentified speakers, wrong timestamps, irrelevant content, misclassified claims. The workbench provides a purpose-built interface for this work, rather than asking reviewers to edit raw markdown files.

**Public transparency.** Anyone reading the main site can follow any claim back through the workbench to see exactly how it was extracted: which source it came from, what the ingestion produced, and how the digester interpreted it. This auditability is fundamental to the platform's credibility. The workbench is not an internal tool - it is part of how Anomalica earns public trust.

## Technology

**Frontend:** A plain Svelte 5 single-page application built with Vite. No meta-framework (not SvelteKit) - the workbench has no need for server-side rendering, file-based routing, or a Node.js server. Svelte compiles components to plain JavaScript at build time, so there is no framework runtime in the browser. This keeps the application lightweight and reduces the attack surface.

**Styling:** Tailwind CSS v4 with shared design tokens imported from anomalica-brand. Panel contents use container queries (`@container`) rather than viewport breakpoints, so components adapt to their panel width as users resize the layout.

**Backend:** A minimal Python service (FastAPI) that reads from and writes to the git repositories. Python because the rest of the pipeline (ingester, digester) is Python, allowing shared libraries for record parsing and validation. The backend is a thin layer between the frontend and git - it has no database of its own. In production, FastAPI serves both the API and the built static frontend files.

**Development:** During development, Vite's dev server proxies `/api` requests to the FastAPI backend running on a separate port. This avoids Cross-Origin Resource Sharing configuration.

**Storage:** Two git repositories hold the pipeline output:

- **anomalica-ingests** (private) - contains the structured text output from the ingester. These files contain copyrighted source material and are never publicly accessible. The workbench backend has a service account with access to this repository and serves individual ingests to authenticated reviewers one at a time, gated by the hash verification described below.
- **anomalica-digests** (public) - contains the extracted claims and nodes. No copyrighted content. The backend commits digest corrections here on behalf of reviewers.

The backend has no database of its own. The git repositories are the storage.

**Access model:** The workbench has three tiers:

- **Anonymous (no login)** - anyone can browse digests, see extracted claims and nodes, view the correction history, and follow the provenance chain of any claim. For copyrighted sources, anonymous viewers can also unlock the ingested markdown by providing their own copy of the source file (hash verification, described in the copyright handling section below). This data is already public (it comes from the anomalica-digests repository) or gated by proof of possession, not by identity.
- **Authenticated (login required)** - same as anonymous, plus the ability to submit corrections to either ingests or digests. Any edit requires a logged-in identity so it can be attributed in the git history. Authenticated users can also request manual access grants for copyrighted sources where hash verification is impractical.
- **Granted access (per record)** - authenticated users who have been manually granted access to specific copyrighted records by an Anomalica member. Grants are stored separately from the records (see the [source types and copyright decision](../decisions/drafts/source-types-and-copyright.md) for the grants storage model).

**Authentication:** OAuth implemented directly in FastAPI using Authlib (a lightweight BSD-3 licensed Python library). No external identity service or self-hosted identity platform. The workbench supports multiple OAuth providers - initially just the git hosting platform (such as GitHub), with others (Google, etc.) addable in about 20 lines of Python each.

The OAuth flow:

1. Reviewer clicks "log in" in the workbench
2. Browser redirects to the FastAPI `/login` endpoint
3. FastAPI redirects to the OAuth provider's authorisation page
4. Reviewer authorises, provider redirects back to FastAPI with a token
5. FastAPI extracts the reviewer's name and email, sets a session cookie
6. The Svelte frontend reads the cookie and includes it in subsequent requests

No authentication library is needed on the frontend. It is just a redirect and a cookie.

For the initial phase with a small number of reviewers, edit access is controlled by an allowlist of email addresses on the backend. Adding a reviewer means adding their email to the list. Browse access to digests requires no allowlist - it is open to everyone.

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

## Copyright handling

The workbench may serve extracted text from copyrighted source material to users who demonstrate they have a legitimate copy. It is not a distribution channel. What is shown depends on the copyright status of each record (see the [source types and copyright decision](../decisions/drafts/source-types-and-copyright.md) for the full display rules and metadata schema). Protection is layered:

1. **Private ingests repository** - only the workbench backend service account has read access
2. **Hash-gated API** - ingest retrieval requires the full 64-character SHA-256 hash of the original source file, which can only be obtained by hashing the file itself (no login required - possession of the file is the proof)
3. **Manual access grants** - for cases where hash verification is impractical (physical book owners, different editions), an Anomalica member can grant per-user per-record access to authenticated users
4. **Rate limiting** - prevents brute-force attempts to guess the missing hash characters
5. **Partial hashes in public references** - the public digests repository references ingests using a truncated hash; the full hash required to fetch an ingest can only be obtained by hashing the original source file

### Full hashes and public hashes

Every ingest is identified by the SHA-256 of its source file, a 64-character hex string. Two forms are used:

- **Full hash** (64 hex chars) - the actual SHA-256. Appears in the ingest file's `content_hash` frontmatter field. Required by the workbench API to fetch an ingest.
- **Public hash** (56 hex chars) - the first 56 characters of the full hash. Used as the identifier in the public digests repository and in any public-facing workbench UI. Not sufficient on its own to fetch an ingest.

The 32 bits dropped from the public hash mean that an attacker who has harvested every public hash from the digests repository still cannot fetch the corresponding ingests. Their options are:

- **Hash the original source file** - the intended path. Takes milliseconds for a reviewer who legitimately has the file
- **Brute-force via the API** - 2^32 (4.3 billion) requests per ingest, defeated by rate limiting
- **Find a SHA-256 pre-image with a matching 224-bit prefix** - computationally infeasible

This means the protection is not a social convention ("please only fetch ingests you already have"): it is a technical requirement that you possess the source file, or find another path to its hash.

### Flow

The viewer provides their own copy of the original file via the browser's File System Access API (no upload to the server). No login is required for this step - possession of the source file is sufficient proof. The browser reads the file locally and computes a SHA-256 hash using hash-wasm in a Web Worker (streaming, so multi-gigabyte video files are handled without loading them fully into memory). The full hash is sent to the workbench API. If an ingest exists for that hash, the server returns the ingest. The original file is never uploaded.

### Operational requirements

Because the partial-hash protection relies on the API never accepting prefix lookups, two rules are non-negotiable:

- The ingest-fetch endpoint rejects any hash that is not exactly 64 hex characters. Prefix search is never exposed.
- The endpoint returns identical responses for "hash not found" and "hash malformed" (both 404 with no distinguishing body). Otherwise an attacker could use the error distinction to verify partial guesses.

Rate limiting is a load-bearing security control, not just an anti-abuse measure, and should be tested as such.

### Scope

This approach works for any source material the reviewer can obtain independently: videos downloadable from YouTube, publicly available PDFs, books they own, podcast episodes. It does not work for material the reviewer cannot access, but in those cases only people with existing access would be reviewing anyway.

## Review tasks for video and audio

Video and audio records are the most labour-intensive to review because automatic speaker diarisation (identifying who is speaking when) is imperfect. The workbench supports:

- **Speaker merging** - the diarisation may split one person into multiple speaker identities. The reviewer merges them.
- **Speaker identification** - assigning names to unidentified speakers, confirming or correcting automatic identifications.
- **Marking irrelevant sections** - ads, sponsor reads, intro/outro filler, "next time on..." previews, off-topic tangents. These sections are flagged so the digester can skip them.
- **Timestamp correction** - adjusting speaker turn boundaries where the diarisation placed them incorrectly.
- **Playback alongside transcript** - the video or audio plays in sync with the transcript, making it easy to verify what was said against what was transcribed.

Video and audio playback uses the browser's built-in HTML5 media elements. Syncing playback position with the transcript uses Svelte's reactive bindings on the media element's `currentTime` property. Clicking a transcript line seeks the media to that timestamp; as media plays, the active transcript line is highlighted and scrolled into view.

## Review tasks for all record types

- **Claim review** - verifying that extracted claims accurately represent what the source says. Correcting misinterpretations, wrong speakers, incorrect claim types or attestation levels.
- **Node review** - verifying that people, organisations, places, events, matters, and objects were correctly identified and linked. Correcting misidentifications or creating new nodes.
- **Flagging missing claims** - noting claims that the digester missed and should have extracted.
- **Removing irrelevant claims** - marking claims that were extracted but add no value (pleasantries, filler, off-topic asides).

The review interface uses structured forms rather than raw text editing. Reviewers correct speaker names via dropdowns, adjust timestamps with controls, and change claim types and attestation levels through purpose-built inputs. This is more usable than editing YAML directly and reduces the chance of formatting errors.

## How corrections are saved

When a reviewer submits corrections, the workbench backend commits the changes to the appropriate git repository using a service account. The commit records the reviewer's identity using git's author/committer separation:

- **Author** - the reviewer (name and email from their OAuth profile). This is the person who made the correction.
- **Committer** - the workbench service account. This is the system that applied the change.

This is the same convention used by git hosting platforms when merging pull requests - the author did the work, the committer applied it. Any git client displays both fields.

**Ingest corrections** (speaker merges, timestamp adjustments, marking irrelevant sections) are committed to the private anomalica-ingests repository. Reviewers cannot access this repository directly - they interact with ingests only through the workbench, which serves one file at a time after hash verification. The project maintainer has full access to the repository and can review, revert, or approve changes.

**Digest corrections** (claim type changes, speaker reattribution, node corrections) are committed to the public anomalica-digests repository. These corrections are visible to anyone and tracked in the public commit history.

The git history provides the full audit trail: who changed what, when, and why. The workbench shows reviewers the diff of their changes before they submit, and displays the history of corrections to each record.

## Review identity across re-ingestion

The ingester improves continually: capture pipelines get better, parsers find bugs, post-processing rules tighten. When the ingester re-ingests a record, the record's body changes - which changes its `content_hash`, which is the SHA-256 of the body in the canonical store layout.

Naive binding of reviews to `content_hash` orphans every prior review when the ingester re-runs. A reviewer who approved a record yesterday would find the same record back in the unreviewed queue today, with no signal that they had already approved its previous form. The friction compounds: a single ingester improvement that touches one file format can invalidate the entire review backlog for that format.

This is the expected operational shape - ingester improvements should not gate on review preservation - so the spec binds reviews to a hierarchy of identities, accepting the strongest available match.

### Identity hierarchy

A record can carry up to three identities at any given time:

| Kind | Source | Stable across | Available for |
|------|--------|---------------|----------------|
| `url` | The `source_url` frontmatter field. The URL the ingester fetched. | Re-ingestion. Publisher byte-level changes. Re-extraction. | Web records, YouTube videos, anything fetched by URL. |
| `sha256` | The `source_hash` frontmatter field. SHA-256 of the original source-file bytes. | Re-extraction. Parser improvements. Post-processing changes. | PDFs, ebooks, audio files, video files, any record sourced from a file. |
| `content` | The `content_hash` (record body SHA-256). | Nothing - any body change rotates it. | All records (always present). |

`url` is preferred over `sha256` is preferred over `content`. A given record may have any subset of the three. Web records have `url` and `content`. File-sourced records have `sha256` and `content`. Web records that the ingester also archives by file (a SingleFile snapshot for offline reading) carry all three.

### Trailer form

A review commit records the identities of the record it reviewed using one or more `Reviewed-Record:` trailers:

```
Reviewed-Record: url:https://thedebrief.org/some-article-slug
Reviewed-Record: sha256:abc123def456...
Reviewed-Record: content:9f2a8c5e...
```

Each trailer is `Reviewed-Record: <kind>:<value>` where kind is one of `url`, `sha256`, `content`. The workbench backend emits whichever identities the record carried at the time of review. Multiple trailers in one commit are alternative identities for the same review - all of them are equivalent claims of identity, the strongest available one will match.

### Match scan

To find prior reviews for a given record, the workbench scans review commits in the appropriate repository and matches their trailers against the record's identities. A match is established when any kind in the trailer matches the same kind on the record:

- The record has `source_url = U` and a prior review's commit carries `Reviewed-Record: url:U` - match.
- The record has `source_hash = H` and a prior review's commit carries `Reviewed-Record: sha256:H` - match.
- No url or sha256 match, but the record's `content_hash = C` matches a prior `Reviewed-Record: content:C` - match (weakest).

When multiple prior reviews match (the same `source_url` appears in two old commits because the same article was ingested twice and reviewed each time), the workbench surfaces all of them rather than picking one. The reviewer disambiguates.

When the new record matches no prior reviews on any kind, it enters the queue as unreviewed.

### Back-compatibility with historical trailers

Review commits emitted before this spec carried a single trailer of the form `Reviewed-Record: sha256:<hash>`, where the value was the record's content_hash (the only identity the workbench was emitting at the time). The match scan retries any `sha256:<hash>` trailer as a `content:<hash>` match when the kind-matched scan finds nothing. The collision space between an arbitrary content_hash and an unrelated source_hash is astronomical (2^256), so this retry is safe in practice. New review commits emit fully labelled trailers; the retry exists only to preserve continuity of pre-spec reviews.

### Future use: URL rotation and aliasing

A record's `source_url` is not guaranteed stable over time. Wayback Machine URLs rotate, publishers issue 301 redirects, articles move between sites. The multiple-trailer form already supports this case: when the workbench (or any other tool) discovers that a record's prior `source_url` is now reachable only via a new URL, it can emit a new review commit (or a maintenance commit) that lists both URLs as `Reviewed-Record:` trailers. Future scans will match either.

The spec does not prescribe how aliasing gets detected or who emits the maintenance commit. The trailer format simply admits the case; implementation is deferred until the problem actually bites.

## Relationship to the main site

The workbench is a separate application with a different audience (reviewers) and different requirements (video playback, interactive editing, file upload). It is not part of the main Anomalica site, which serves assembled articles to readers.

The two applications share the same data: the workbench reads and writes ingests and digests, the main site reads assembled articles produced from those digests. They do not need to be on the same domain or infrastructure.
