# Source types and copyright handling

Date: 2026-03-21
Status: draft
Updated: 2026-09-22

> **Layer clarification:** Decision
> [0051](../0051-asset-record-selection-and-evidence-identity.md) makes each
> `assets[].copyright` block authoritative. References below to Record-level
> copyright or grants are legacy wording where not yet rewritten; no such value may
> widen an Asset decision.

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

The platform does not publish source material outside the explicit body,
original, media and embed allow-lists fixed by the
[0031 amendment](../0031-per-record-inspection-pages.md#public-record-content).

### Quotation policy

Short attributed quotations are published in full - as long as they need to be to convey their point - and are NOT capped, truncated to a length limit, or gated. This is best-effort, not enforced: the digester uses Haiku, which already produces small, targeted quotes, and the platform builds no quote-length enforcement. If a rightsholder raises a specific concern, the platform complies on request (takedown or adjustment); it does not pre-restrict.

The legal basis is Japan's Copyright Act Article 32, which makes quotation (引用 (いんよう)) of a published work a lawful affirmative right where the use is fair and the quotation subordinate to the quoting work, with mandatory source attribution (出所明示 (しゅっしょめいじ)) under Article 48. This is the distinct right covering the PUBLISHED quotes; Article 30-4 (above) covers the extraction step, not publication. Japanese courts apply a two-part test (Supreme Court, 28 March 1980, the Parody Montage case, モンタージュ写真): a clear distinction between the quoted material and the quoting work (明瞭区別性 (めいりょうくべつせい)) and a main-subordinate relationship (主従関係 (しゅじゅうかんけい)); later practice (Intellectual Property High Court, 2010, the Art Appraisal Document case, 絵画鑑定証書 (かいがかんていしょうしょ)) weighs these as a totality. Short attributed quotes that substantiate a claim pass under either approach - the position is strongly defensible, not certain. Short attributed quotation is also standard practice across journalism, scholarship, and reference works (Wikipedia treats short attributed text quotes as its most permissive category). Anomalica is educational: quotes substantiate claims and link back to the source record.

The line is SUBSTANTIALITY, not length. No jurisdiction sets a bright-line safe word count - the United States Copyright Office and the United Kingdom Intellectual Property Office both say so explicitly - so "no length cap" is consistent with the law, not in tension with it. A supporting quote is evidence and is published; a full body or transcript is redistribution and follows the separate status allow-list below, with `licensed`, `restricted`, absent and unknown state behind the proof-of-possession gate. The control is substitution: quoted material must not be presentable as an independent substitute for the original (Tokyo District Court, 12 February 2020), which bites on images and long passages, not one- or two-sentence text quotes. Quote is not body - this policy does not itself un-gate full bodies or transcripts.

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

The Workbench is private. Public provenance is exposed through stable safe Record
pages; private source review and possession-gated access remain in the authenticated
Workbench.

What the workbench can show depends on the copyright status of the source and whether the viewer can demonstrate they have a legitimate copy:

| Copyright status | Digested claims | Supporting quotes | Original source | Ingested markdown |
|---|---|---|---|---|
| `public_domain` / `open_licence` | Shown | Shown | Served directly from storage | Shown |
| `publicly_accessible` (web articles, YouTube, podcasts) | Shown | Shown | Embedded or linked from original source URL | Shown |
| `licensed` (explicit permission from rights holder) | Shown | **Shown** | Gated: nonce-bound byte-range proof or manual access grant | Gated: nonce-bound byte-range proof or manual access grant |
| `restricted` (books, paywalled papers, documentaries) | Shown | **Shown** | Gated: nonce-bound byte-range proof or manual access grant | Gated: nonce-bound byte-range proof or manual access grant |


**A SUPPORTING QUOTE IS NEVER GATED, WHATEVER THE STATUS.** The `Supporting quotes`
column above is `Shown` on every row, including `restricted`, and that is not an
oversight to be tidied up. It is the Quotation policy earlier in this document,
restated in the table because the table is what people actually read when deciding.
If you are about to remove short attributed quotes because their source is a
copyrighted book, STOP - you are about to delete lawful quotation the platform
depends on, and it has happened before.

**Over-gating is NOT free, and the allow-list sentence below is about SOURCES, not
quotes.** "An allow-list merely over-gates, which is a correction rather than a
disclosure" is true of serving a full body: withholding one costs a reader one
document. Removing supporting quotes costs something different and worse - a claim
with no quote beside it looks unevidenced, so stripping quotes makes the platform
look like it cannot support its own assertions. That is a false statement about our
evidence, published at scale. Deleting 5,400 quotes and deleting nothing are BOTH
errors; neither is the safe default.

**The artefacts this table governs are the source body and the ingested markdown.**
If you are deciding about something not listed here, it is not covered by these rows
and you must not reason by analogy from them. Ask.

**Public serving is an allow-list, not a deny-list.** Only `public_domain`,
`open_licence` and `publicly_accessible` are served publicly on status alone. Every
other value - including `licensed`, including an unrecognised or missing one - is
gated. This matches the implementation (`SNAPSHOT_PUBLIC` in the workbench's
`prerender.py`), and the direction matters: a deny-list leaks whenever a new status
is added or a field is absent, an allow-list merely over-gates, which is a
correction rather than a disclosure.

**`licensed` does not serve freely on the strength of the word or its evidence.** Permission is
specific - it may cover quotation and not redistribution, it may have expired, it
may have come from someone without the standing to grant it. What makes the status
real is the evidence beside it: `holder`, `granted_by`, `granted_at`, `licence_url`,
`expires`. A `licensed` record carrying none of those is indistinguishable from a
mislabelled `restricted` one, so it is treated as restricted. Those fields justify
classification but do not encode audience or permitted use; they therefore never
widen either public or Workbench access. Any access without a possession proof
requires the separate explicit per-user, per-Asset manual grant.

That is not hypothetical. On 2026-08-20 all seventeen `licensed` records in the
store - *Communion*, *Thinking, Fast and Slow*, *Imminent*, *Dark Mission* and
others - carried `status: licensed` and nothing else. No permission had been sought
from any of those rights holders. They were commercial books, which this table's own
`restricted` row describes exactly, and they have since been reclassified. Had the
serving code followed this document instead of its own allow-list, all seventeen
would have been published in full.

For gated Assets, there are two independent paths inside an authenticated,
allow-listed Workbench session:

1. **Nonce-bound byte-range proof.** The reviewer selects each exact local copy.
   The browser hashes unpredictable server-selected byte ranges with a short-lived
   nonce, without uploading bytes. The Asset hash identifies the target but is
   public and grants nothing by itself. Success authorises only that Asset, session
   and use; a composite view requires every gated member.

2. **Manual access grant.** A grant binds the authenticated reviewer, explicit
   Asset hashes and allowed uses. It covers cases where exact-byte verification is
   impractical; a Record id alone grants nothing.

### Access grants storage

Access grants are stored in a YAML file in the workbench repository, separate from
the records themselves. User identity is an HMAC-SHA-256 pseudonym over the
authenticated issuer and subject using a Workbench secret that is never committed:

```yaml
grants:
  - user: hmac-sha256:a1b2c3d4e5...
    assets:
      - sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      - sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    uses: [review]
    granted_by: anomalica-admin
    granted_at: 2026-04-11
```

The Workbench computes
`HMAC-SHA256(secret, UTF8(issuer) || 0x00 || UTF8(subject))` from the authenticated
session and checks for the full lowercase digest. Email addresses and a public
fixed salt are forbidden. Rotating the secret requires an authenticated atomic
rewrite of all grants; a missing key fails closed.

## Per-Asset copyright metadata

Each `record/3` Asset descriptor carries a `copyright` block describing the legal
status of those exact bytes. The Workbench applies it independently to every
selected member. Legacy `/1` and `/2` Records retain their top-level block only as
migration input. Rights metadata contains no user or access information.

### Schema

```yaml
copyright:
  status: public_domain | open_licence | publicly_accessible | licensed | restricted
  detail: US federal government work (17 USC 105)
  holder: CBS Broadcasting Inc.
  licence_url: https://creativecommons.org/licenses/by/4.0/
  granted_by: Jane Smith, Head of Licensing
  granted_at: 2026-04-11
  reference: correspondence/cbs-2026-04-11.pdf
```

The `status` field tells the workbench what display rules to apply. The `detail` field is freetext for humans - the justification for the status, readable in the audit trail.

### Defaults and safety

The ingester applies the same ordered acquisition defaults as the canonical Ingest
contract:

- an explicit operator status wins;
- a `.gov` or `.mil` hostname defaults to `public_domain`;
- every other anonymously retrieved HTTP(S) URL defaults to
  `publicly_accessible`, regardless of file format;
- a local file defaults to `restricted`.

These are defaults, not licence determinations. Hostname matching is exact; a URL
path containing `.gov` does not qualify.

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

The Workbench needs access to original source files to display them alongside an
Ingest. Every original is an immutable Asset stored by `assets[].asset_hash`,
independent of source type and Record identity. For a multi-Asset Record, access is
checked per member and one successful possession proof never unlocks the rest.

Two storage zones are used:

- **Public zone** (CDN-backed) - public domain and open-licence originals. Served directly to anyone. URL pattern: `https://cdn.anomalica.is/sources/{asset_hash}.{ext}` (the source-asset hash, per type as above)
- **Private zone** (no public access) - copyrighted originals. Only accessible via
  the Workbench API, which checks a nonce-bound byte-range proof or explicit grant
  before proxying the file. No direct public URL exists.

For publicly available sources (YouTube, podcasts, news articles), the original is not stored - the workbench embeds or links to it at its source URL.

The ingester uploads each original to the appropriate storage zone during
ingestion, based on that Asset's authoritative copyright status. If a member's
status is later changed (for example from `restricted` to `public_domain` after
determining copyright has expired), only that Asset is moved between zones; one
member's status never widens another's.

For local development, the workbench backend serves originals from a local directory. The ingester already retains source files on disk during processing.

## Consequences

The platform can draw on a broad range of sources including books and copyrighted journalism without infringing copyright. The legal basis is fourfold: facts are not copyrightable (universal), Japan's Article 30-4 permits the information analysis that produces those facts, Article 32 makes short attributed quotation a lawful right (covering the published evidential quotes; see [Quotation policy](#quotation-policy)), and the platform never distributes copyrighted source material to the public.

The workbench provides full transparency into the extraction pipeline while
respecting copyright. Anyone can audit the digested claims and their provenance.
For copyrighted sources, viewing the ingested reproduction requires demonstrating
access through the nonce-bound byte-range proof or holding an explicit manual
grant. A public Asset hash never grants access.

Every claim in the knowledge graph is traceable to a specific source. For copyrighted sources, the reader sees the attribution and a pointer to where to find the original, not the original content itself.
