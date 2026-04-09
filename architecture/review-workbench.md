# Review Workbench

A separate web application for reviewing and correcting ingests and digests. Not part of the main site. The workbench is where the human review step of the pipeline happens.

## Purpose

The digester pipeline produces ingests (structured text from source material) and digests (extracted claims and nodes). Both need human review to catch errors - misidentified speakers, wrong timestamps, irrelevant content, misclassified claims. The review workbench provides a purpose-built interface for this work, rather than asking reviewers to edit raw markdown files.

## Technology

**Frontend:** A plain Svelte 5 single-page application built with Vite. No meta-framework (not SvelteKit) - the workbench has no need for server-side rendering, file-based routing, or a Node.js server. Svelte compiles components to plain JavaScript at build time, so there is no framework runtime in the browser. This keeps the application lightweight and reduces the attack surface.

**Styling:** Tailwind CSS v4 with shared design tokens imported from anomalica-brand. Panel contents use container queries (`@container`) rather than viewport breakpoints, so components adapt to their panel width as users resize the layout.

**Backend:** A minimal Python service (FastAPI) that reads from and writes to the git repositories. Python because the rest of the pipeline (ingester, digester) is Python, allowing shared libraries for record parsing and validation. The backend is a thin layer between the frontend and git - it has no database of its own. In production, FastAPI serves both the API and the built static frontend files.

**Development:** During development, Vite's dev server proxies `/api` requests to the FastAPI backend running on a separate port. This avoids Cross-Origin Resource Sharing configuration.

**Storage:** Two git repositories hold the pipeline output:

- **anomalica-ingests** (private) - contains the structured text output from the ingester. These files contain copyrighted source material and are never publicly accessible. The workbench backend has a service account with access to this repository and serves individual ingests to authenticated reviewers one at a time, gated by the hash verification described below.
- **anomalica-digests** (public) - contains the extracted claims and nodes. No copyrighted content. The backend commits digest corrections here on behalf of reviewers.

The backend has no database of its own. The git repositories are the storage.

**Access model:** The workbench has two tiers:

- **Public (no login)** - anyone can browse digests, see extracted claims and nodes, and view the correction history. This data is already public (it comes from the anomalica-digests repository).
- **Authenticated (login required)** - viewing ingests (which also requires hash verification of the original source) and submitting corrections to either ingests or digests. Any edit requires a logged-in identity so it can be attributed in the git history.

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

The workbench never distributes copyrighted source material. The reviewer provides their own copy of the original file via the browser's File System Access API (no upload to the server). The browser reads the file locally and computes a SHA-256 hash using hash-wasm in a Web Worker (streaming, so multi-gigabyte video files are handled without loading them fully into memory). The hash is sent to the server. If it matches the content hash stored in the ingest's metadata, the server confirms the match and shows the reviewer the ingest and digest alongside their own copy of the original.

The platform stores ingests (which contain the full text of source material) but does not serve them to anyone who cannot prove they already have the original. The original file is never uploaded to the server, only the hash.

This approach works for any source material the reviewer can obtain independently: videos downloadable from YouTube, publicly available PDFs, books they own, podcast episodes. It does not work for material the reviewer cannot access, but in those cases only people with existing access would be reviewing.

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

## Relationship to the main site

The workbench is a separate application with a different audience (reviewers) and different requirements (video playback, interactive editing, file upload). It is not part of the main Anomalica site, which serves assembled articles to readers.

The two applications share the same data: the workbench reads and writes ingests and digests, the main site reads assembled articles produced from those digests. They do not need to be on the same domain or infrastructure.
