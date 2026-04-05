# Review Workbench

A separate web application for reviewing and correcting ingests and digests. Not part of the main site. The workbench is where the human review step of the pipeline happens.

## Purpose

The digester pipeline produces ingests (structured text from source material) and digests (extracted claims and nodes). Both need human review to catch errors - misidentified speakers, wrong timestamps, irrelevant content, misclassified claims. The review workbench provides a purpose-built interface for this work, rather than asking reviewers to edit raw markdown files.

## Technology

**Frontend:** A plain Svelte 5 single-page application built with Vite. No meta-framework (not SvelteKit) - the workbench has no need for server-side rendering, file-based routing, or a Node.js server. Svelte compiles components to plain JavaScript at build time, so there is no framework runtime in the browser. This keeps the application lightweight and reduces the attack surface.

**Styling:** Tailwind CSS v4 with shared design tokens imported from anomalica-brand. Panel contents use container queries (`@container`) rather than viewport breakpoints, so components adapt to their panel width as users resize the layout.

**Backend:** A minimal Python service (FastAPI) that reads from and writes to the git repositories. Python because the rest of the pipeline (ingester, digester) is Python, allowing shared libraries for record parsing and validation. The backend is a thin layer between the frontend and git - it has no database of its own. In production, FastAPI serves both the API and the built static frontend files.

**Development:** During development, Vite's dev server proxies `/api` requests to the FastAPI backend running on a separate port. This avoids Cross-Origin Resource Sharing configuration.

**Storage:** The git repositories ARE the storage. Ingests are read from the ingester's output. Digests are read from and written to the anomalica-digests repository. The backend commits corrections via the git hosting platform's application programming interface. No separate database.

**Authentication:** Via the git hosting platform's OAuth. If someone can push to the anomalica-digests repository, they can review.

**Supply chain discipline:** The workbench handles sensitive source material, so dependency management matters. Every third-party library added is a trust decision. The framework choice (plain Svelte over heavier alternatives) and the preference for platform APIs over libraries reflect this priority. Key dependencies are limited to:

- **PaneForge** - resizable panel layout (Svelte 5 native)
- **pdfjs-dist** - PDF rendering (Mozilla, framework-agnostic)
- **hash-wasm** - streaming file hashing via WebAssembly (for copyright verification of large files)

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

This is not yet decided. Options include:

- **Updating the ingest and digest files directly** - the workbench writes corrected versions back to the repository. Simple but means the ingest is no longer a pure ingester output.
- **Storing corrections as patches** - the original ingest is preserved and corrections are stored separately, applied at import time. More complex but preserves the distinction between automated output and human corrections.
- **A hybrid approach** - the ingest is updated in place (since it is an internal working file anyway) but the digest corrections are tracked as commits in the anomalica-digests repository, where the git history provides the audit trail.

## Relationship to the main site

The workbench is a separate application with a different audience (reviewers) and different requirements (video playback, interactive editing, file upload). It is not part of the main Anomalica site, which serves assembled articles to readers.

The two applications share the same data: the workbench reads and writes ingests and digests, the main site reads assembled articles produced from those digests. They do not need to be on the same domain or infrastructure.
