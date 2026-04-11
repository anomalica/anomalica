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

### What the workbench displays

The workbench is publicly accessible. Anyone can use it to audit the full provenance chain of any claim - from the original source, through ingestion, to digestion. This transparency is fundamental to the platform's credibility.

What the workbench can show depends on the copyright status of the source and whether the viewer can demonstrate they have a legitimate copy:

| Copyright status | Digested claims | Original source | Ingested markdown |
|---|---|---|---|
| Public domain / open licence | Shown | Served directly | Shown |
| Publicly available (YouTube, news article) | Shown | Embedded from original source | Shown only if viewer provides file (hash match) or has been granted access |
| Copyrighted, not publicly available (books, paywalled) | Shown | Not served | Shown only if viewer provides file (hash match) or has been granted access |

For copyrighted sources, there are two independent paths to unlock the ingested markdown view:

1. **Hash verification (no login required).** The viewer drags their copy of the source file into the browser. The workbench computes the file's SHA-256 hash client-side (using hash-wasm in a Web Worker, streaming so large files are handled without loading them fully into memory). The full 64-character hash is sent to the workbench API, which returns the ingest if the hash matches. The original file never leaves the viewer's browser and is never uploaded. This works without authentication - possession of the source file is the proof. See the [review workbench architecture](../architecture/review-workbench.md) for the truncated-hash system that makes provenance references publicly visible without exposing the full hash needed to fetch ingests.

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
    granted_by: mark-anomalica
    granted_at: 2026-04-11
```

The workbench computes `SHA256("anomalica-grants" + user_email)` from the authenticated session and checks for a matching entry. The salt prevents pre-computed rainbow table lookups against the hashes.

## Per-record copyright metadata

Each ingested record carries a `copyright` block in its YAML frontmatter that describes the legal status of the original work. This metadata tells the workbench what display rules to apply. It does not contain any user or access information.

### Schema

```yaml
copyright:
  status: public_domain | open_licence | licensed | restricted
  reason: us_government_work | cc0 | expired | cc_by_4 | cc_by_sa_4 | cc_by_nc_4 | explicit_permission
  holder: CBS Broadcasting Inc.
  licence_url: https://creativecommons.org/licenses/by/4.0/
  granted_by: Jane Smith, Head of Licensing
  granted_at: 2026-04-11
  expires: null
  reference: correspondence/cbs-2026-04-11.pdf
  notes: Permission covers transcript display only, not audio playback
```

### Defaults and safety

The ingester always sets `status: restricted` for new records. This is the safe default - no content is served beyond extracted claims until someone actively determines the copyright status and provides justification.

Only `status` is always required. The other fields are conditional:

| Status | Required fields | Optional fields |
|--------|----------------|-----------------|
| `restricted` | (none beyond status) | `holder` |
| `public_domain` | `reason` | `holder`, `notes` |
| `open_licence` | `reason` | `holder`, `licence_url`, `notes` |
| `licensed` | `holder`, `granted_by`, `granted_at`, `reference` | `expires`, `licence_url`, `notes` |

Changing the status away from `restricted` requires filling in the appropriate justification fields. The workbench enforces this by presenting a structured form that requires the conditional fields based on the selected status.

All changes to the copyright field are tracked in git history, providing a full audit trail of who changed the status, when, and what justification they provided.

### Reason values

| Value | Meaning |
|-------|---------|
| `us_government_work` | Created by the US federal government (17 USC 105) |
| `government_work` | Created by a government where Crown Copyright or equivalent has expired or does not apply |
| `cc0` | Dedicated to the public domain via Creative Commons Zero |
| `expired` | Copyright term has expired |
| `cc_by_4` | Creative Commons Attribution 4.0 International |
| `cc_by_sa_4` | Creative Commons Attribution-ShareAlike 4.0 International |
| `cc_by_nc_4` | Creative Commons Attribution-NonCommercial 4.0 International |
| `explicit_permission` | Rights holder has granted permission directly |
| `submitter_grant` | Original submission where the submitter has authorised use |

This list will grow as new licence types are encountered.

### References

For `licensed` status, the `reference` field points to evidence of the permission: a file path within the repository (e.g. `correspondence/cbs-2026-04-11.pdf`), a URL to an archived email, or similar. The point is that the claim of permission is verifiable.

## Consequences

The platform can draw on a broad range of sources including books and copyrighted journalism without infringing copyright. The legal basis is threefold: facts are not copyrightable (universal), Japan's Article 30-4 permits the information analysis that produces those facts, and the platform never distributes copyrighted source material to the public.

The workbench provides full transparency into the extraction pipeline while respecting copyright. Anyone can audit the digested claims and their provenance. For copyrighted sources, viewing the ingested reproduction requires demonstrating access to the original (via hash match or manual grant).

Every claim in the knowledge graph is traceable to a specific source. For copyrighted sources, the reader sees the attribution and a pointer to where to find the original, not the original content itself.
