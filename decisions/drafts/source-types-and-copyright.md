# Source types and copyright handling

Date: 2026-03-21
Status: draft
Updated: 2026-04-11

## Context

The knowledge graph (a structured database of interconnected facts) will be built from a variety of source material with different accessibility and copyright characteristics. The platform needs to extract meaning from all of these without infringing copyright or reproducing content that belongs to others.

The processing pipeline (ingestion, digestion, and extraction of facts) runs in Japan, where Article 30-4 of the Copyright Act (著作権法 (ちょさくけんほう), amended 2018) permits reproduction of copyrighted works for information analysis (情報解析 (じょうほうかいせき)) without permission, provided the reproduction is not for the purpose of enjoying the works themselves. This provision was introduced specifically to support artificial intelligence and data mining activities, and applies equally to domestic and foreign works under the Berne Convention. Article 30-4 covers the extraction step, not the distribution of results. Distribution is addressed separately below - the public site serves only non-copyrightable facts, and copyrighted source material is never distributed publicly regardless of hosting location.

Additionally, facts are not copyrightable in any jurisdiction. Only the specific expression (the words chosen to describe a fact) is protected. Anomalica extracts facts and states them in its own words - the original expression remains in the original source.

## Decision

### Source types

The platform will ingest the following types of sources:

**Public domain and openly accessible:**
- Government documents, Freedom of Information Act releases, declassified material
- Congressional and parliamentary records and testimony
- Academic papers (open access)
- Podcast and YouTube video transcripts (publicly available audio/video, transcribed for extraction)

**Copyrighted but extractable under Article 30-4 and fair use / fair dealing:**
- Books
- News articles
- Academic papers (paywalled)
- Documentary transcripts

**Original submissions:**
- Documents, testimony, sensor data, and other material deposited directly with Anomalica by submitters. These will be held by the platform and may be published with the submitter's consent (see [source identity model](source-identity-model.md) and [conditional release](conditional-release.md)).

### What the platform publishes

From the digestion stage onwards, the platform publishes only extracted facts, claims, entity references, and provenance information. These are not copyrightable. Every extracted claim is attributed to its source (title, author, page/chapter, timestamp as applicable) and readers are directed to where they can obtain the original.

The platform does not publish copyrighted source material or ingested reproductions of copyrighted source material.

### Quotation policy

Short attributed quotations are published in full - as long as they need to be to convey their point - and are NOT capped, truncated to a length limit, or gated. This is best-effort, not enforced: the digester uses Haiku, which already produces small, targeted quotes, and the platform builds no quote-length enforcement. If a rightsholder raises a specific concern, the platform complies on request (takedown or adjustment); it does not pre-restrict.

The legal basis is Japan's Copyright Act Article 32, which makes quotation (引用 (いんよう)) of a published work a lawful affirmative right where the use is fair and the quotation subordinate to the quoting work, with mandatory source attribution (出所明示 (しゅっしょめいじ)) under Article 48. This is the distinct right covering the PUBLISHED quotes; Article 30-4 (above) covers the extraction step, not publication. Japanese courts apply a two-part test (Supreme Court, 28 March 1980, the Parody Montage case, モンタージュ写真): a clear distinction between the quoted material and the quoting work (明瞭区別性 (めいりょうくべつせい)) and a main-subordinate relationship (主従関係 (しゅじゅうかんけい)); later practice (Intellectual Property High Court, 2010, the Art Appraisal Document case, 絵画鑑定証書 (かいがかんていしょうしょ)) weighs these as a totality. Short attributed quotes that substantiate a claim pass under either approach - the position is strongly defensible, not certain. Short attributed quotation is also standard practice across journalism, scholarship, and reference works (Wikipedia treats short attributed text quotes as its most permissive category). Anomalica is educational: quotes substantiate claims and link back to the source record.

The line is SUBSTANTIALITY, not length. No jurisdiction sets a bright-line safe word count - the United States Copyright Office and the United Kingdom Intellectual Property Office both say so explicitly - so "no length cap" is consistent with the law, not in tension with it. A supporting quote is evidence and is published; a full body or transcript is redistribution and stays behind the proof-of-possession gate (see below). The control is substitution: quoted material must not be presentable as an independent substitute for the original (Tokyo District Court, 12 February 2020), which bites on images and long passages, not one- or two-sentence text quotes. Quote is not body - this policy does not un-gate full bodies or transcripts.

**Sources.**

Japan (the operative basis):

- Copyright Act Article 32(1) (quotation) and Article 48 (source indication) - Ministry of Justice official English translation: https://www.japaneselawtranslation.go.jp/en/laws/view/1980/en
- Copyright Research and Information Center (CRIC), English overview: https://www.cric.or.jp/english/clj/cl2.html
- Supreme Court, 28 March 1980 (Parody Montage, モンタージュ写真) - origin of the two-part test.
- Intellectual Property High Court, 2010 (Art Appraisal Document, 絵画鑑定証書 (かいがかんていしょうしょ)) - the totality approach.
- Tokyo District Court, 12 February 2020 - the independent-substitute watch-item.
- Agency for Cultural Affairs (文化庁 (ぶんかちょう)) copyright overview: https://www.bunka.go.jp/english/policy/copyright/system/
- Monolith Law, English practitioner commentary: https://monolith.law/en/general-corporate/quote-text-and-images-without-infringing-copyright

Other jurisdictions concur:

- United States: 17 USC 107 (fair use); US Copyright Office fair-use FAQ (https://www.copyright.gov/help/faq/faq-fairuse.html); Feist Publications v. Rural Telephone, 499 U.S. 340 (1991) (facts are not copyrightable); Harper & Row v. Nation Enterprises, 471 U.S. 539 (1985) (the "heart of the work" and unpublished-source caution).
- United Kingdom: Copyright, Designs and Patents Act 1988, s.30(1ZA) (quotation exception): https://www.legislation.gov.uk/ukpga/1988/48/section/30
- Practice: Wikipedia (Non-free content criteria, Quotations guideline); Center for Media and Social Impact fair-use codes for journalism and scholarship.

### What the workbench displays

The workbench is publicly accessible. Anyone can use it to audit the full provenance chain of any claim - from the original source, through ingestion, to digestion. This transparency is fundamental to the platform's credibility.

What the workbench can show depends on the copyright status of the source and whether the viewer can demonstrate they have a legitimate copy:

| Copyright status | Digested claims | Original source | Ingested markdown |
|---|---|---|---|
| `public_domain` / `open_licence` | Shown | Served directly from storage | Shown |
| `publicly_accessible` (web articles, YouTube, podcasts) | Shown | Embedded or linked from original source URL | Shown |
| `licensed` (explicit permission from rights holder) | Shown | Served directly from storage | Shown |
| `restricted` (books, paywalled papers, documentaries) | Shown | Gated: hash verification or manual access grant | Gated: hash verification or manual access grant |

Only `restricted` gates any content. All other statuses show everything freely.

For copyrighted sources, there are two independent paths to unlock the ingested markdown view:

1. **Hash verification (no login required).** The viewer drags their copy of the source file into the browser. The workbench computes the file's SHA-256 hash client-side (using hash-wasm in a Web Worker, streaming so large files are handled without loading them fully into memory). The full 64-character hash is sent to the workbench API, which returns the ingest if the hash matches. The original file never leaves the viewer's browser and is never uploaded. This works without authentication - possession of the source file is the proof. See the [review workbench architecture](../../architecture/review-workbench.md) for the truncated-hash system that makes provenance references publicly visible without exposing the full hash needed to fetch ingests.

2. **Manual access grant (login required).** A viewer with an account can request access. An Anomalica member approves it. The grant is per user per record, stored in the workbench's grants file (see below). This covers cases where hash verification is impractical (physical book owners, different digital editions with different hashes).

### Access grants storage

Access grants are stored in a YAML file in the workbench repository, separate from the records themselves. User identity is stored as a salted SHA-256 hash of their email address to avoid storing personally identifiable information:

```yaml
salt: anomalica-grants
grants:
  - user: a1b2c3d4e5...  # SHA-256 of salt + email
    records:
      - pentagon-uap-report-2021
      - kean-ufos-generals-2010
    granted_by: anomalica-admin
    granted_at: 2026-04-11
```

The workbench computes `SHA256("anomalica-grants" + user_email)` from the authenticated session and checks for a matching entry. The salt prevents pre-computed rainbow table lookups against the hashes.

## Per-record copyright metadata

Each ingested record carries a `copyright` block in its YAML frontmatter that describes the legal status of the original work. This metadata tells the workbench what display rules to apply. It does not contain any user or access information.

### Schema

```yaml
copyright:
  status: public_domain | open_licence | publicly_accessible | licensed | restricted
  detail: US federal government work (17 USC 105)
  holder: CBS Broadcasting Inc.
  licence_url: https://creativecommons.org/licenses/by/4.0/
  granted_by: Jane Smith, Head of Licensing
  granted_at: 2026-04-11
  expires: null
  reference: correspondence/cbs-2026-04-11.pdf
```

The `status` field tells the workbench what display rules to apply. The `detail` field is freetext for humans - the justification for the status, readable in the audit trail.

### Defaults and safety

The ingester sets the copyright status automatically based on the source type:

- **Web pages, YouTube, podcasts** (anything with a public URL): `publicly_accessible`. The original is freely available on the internet - gating the ingested reproduction of something anyone can read by clicking a link serves no purpose.
- **Everything else** (PDFs, local files, books, documentaries): `restricted`. This is the safe default - no content is served beyond extracted claims until someone actively determines the copyright status and provides justification.

The `publicly_accessible` status can be downgraded to `restricted` if a source is taken offline or paywalled after ingestion. The `restricted` status can be upgraded to `public_domain`, `open_licence`, or `licensed` once someone determines the actual copyright status and provides justification.

Only `status` is always required. The other fields are conditional:

| Status | Required fields | Optional fields |
|--------|----------------|-----------------|
| `restricted` | (none beyond status) | `holder`, `detail` |
| `public_domain` | `detail` | `holder` |
| `open_licence` | `detail` | `holder`, `licence_url` |
| `publicly_accessible` | (none beyond status) | `detail`, `holder` |
| `licensed` | `holder`, `granted_by`, `granted_at`, `reference` | `detail`, `expires`, `licence_url` |

Changing the status away from `restricted` requires filling in the appropriate justification fields. The workbench enforces this by presenting a structured form that requires the conditional fields based on the selected status.

All changes to the copyright field are tracked in git history, providing a full audit trail of who changed the status, when, and what justification they provided.

### References

For `licensed` status, the `reference` field points to evidence of the permission: a file path within the repository (e.g. `correspondence/cbs-2026-04-11.pdf`), a URL to an archived email, or similar. The point is that the claim of permission is verifiable.

## Original file storage

The workbench needs access to original source files to display them alongside ingested markdown during review. Originals are stored in object storage (Bunny Storage), keyed by the raw source asset's SHA-256 - the hash that names the file in `sources/`. Which field carries that hash is per-type: `source_hash` (frontmatter) for `web`; `content_hash` (frontmatter, which hashes the source bytes) for `audio`/`video`/`pdf`; and for `ebook` only the verification sidecar's `sha256` (no frontmatter field). See record-format.md's `source_hash` row.

Two storage zones are used:

- **Public zone** (CDN-backed) - public domain and open-licence originals. Served directly to anyone. URL pattern: `https://cdn.anomalica.is/sources/{asset_hash}.{ext}` (the source-asset hash, per type as above)
- **Private zone** (no public access) - copyrighted originals. Only accessible via the workbench API, which checks hash verification or manual grant before proxying the file. No direct public URL exists.

For publicly available sources (YouTube, podcasts, news articles), the original is not stored - the workbench embeds or links to it at its source URL.

The ingester uploads originals to the appropriate storage zone during ingestion, based on the record's copyright status. If the status is later changed (e.g. from `restricted` to `public_domain` after determining copyright has expired), the file is moved between zones.

For local development, the workbench backend serves originals from a local directory. The ingester already retains source files on disk during processing.

## Consequences

The platform can draw on a broad range of sources including books and copyrighted journalism without infringing copyright. The legal basis is fourfold: facts are not copyrightable (universal), Japan's Article 30-4 permits the information analysis that produces those facts, Article 32 makes short attributed quotation a lawful right (covering the published evidential quotes; see [Quotation policy](#quotation-policy)), and the platform never distributes copyrighted source material to the public.

The workbench provides full transparency into the extraction pipeline while respecting copyright. Anyone can audit the digested claims and their provenance. For copyrighted sources, viewing the ingested reproduction requires demonstrating access to the original (via hash match or manual grant).

Every claim in the knowledge graph is traceable to a specific source. For copyrighted sources, the reader sees the attribution and a pointer to where to find the original, not the original content itself.
