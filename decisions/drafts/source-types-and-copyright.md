# Source types and copyright handling

Date: 2026-03-21
Status: draft

## Context

The knowledge graph (a structured database of interconnected facts) will be built from a variety of source material with different accessibility and copyright characteristics. The platform needs to extract meaning from all of these without infringing copyright or reproducing content that belongs to others.

## Decision

The platform will ingest the following types of sources:

**Public domain and openly accessible:**
- Government documents, Freedom of Information Act releases, declassified material
- Congressional and parliamentary records and testimony
- Academic papers (open access)
- Podcast and YouTube video transcripts (publicly available audio/video, transcribed for extraction)

**Copyrighted but extractable under fair dealing:**
- Books
- News articles
- Academic papers (paywalled)
- Documentary transcripts

**Original submissions:**
- Documents, testimony, sensor data, and other material deposited directly with Anomalica by submitters. These will be held by the platform and may be published with the submitter's consent (see [source identity model](source-identity-model.md) and [conditional release](conditional-release.md)).

For copyrighted material, the platform will:
- Extract structured claims and meaning, not reproduce the original text
- Attribute every extracted claim to its source (title, author, page/chapter, timestamp as applicable)
- Use only short excerpts where necessary for context, within fair dealing limits
- Direct readers to where they can obtain the original (purchase link, library reference, publisher website)
- Not host or distribute the copyrighted source material itself

For podcasts and YouTube videos, the transcription is a means to extract structured claims. The transcript itself is an intermediate step in the pipeline, not published content.

For original submissions, the submitter controls whether the material is published. Submitted material will be stored by the platform and processed through the knowledge graph engine. How and where original files are stored is an open question (see below).

## Consequences

The platform can draw on a broad range of sources including books and copyrighted journalism without infringing copyright. Readers are directed to the original sources, which may increase sales or readership for those sources rather than competing with them.

Every claim in the knowledge graph is traceable to a specific source. For copyrighted sources, the reader sees the attribution and a pointer to where to find the original, not the original content itself.

**Open question:** storage of original submitted files (PDFs, sensor data, scanned documents) is not yet decided. Options include object storage alongside the knowledge graph, distributed storage, or a separate archive. This will be addressed in a future decision.

## Per-record copyright metadata

Each ingested record carries a `copyright` block in its YAML frontmatter that describes the legal status of the original work and what permissions the platform has. This metadata determines what the workbench and site can display to users:

- `public_domain` or `open_licence`: full record content can be served directly
- `licensed`: full content served to authenticated reviewers, subject to licence terms
- `restricted` (default): only extracted factual claims are served, not the record text itself. Users can unlock the full view by providing their own copy of the source file (verified by SHA-256 hash match)

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

Only `status` is always required. The other fields are conditional:

| Status | Required fields | Optional fields |
|--------|----------------|-----------------|
| `restricted` | (none beyond status) | `holder` |
| `public_domain` | `reason` | `holder`, `notes` |
| `open_licence` | `reason` | `holder`, `licence_url`, `notes` |
| `licensed` | `holder`, `granted_by`, `granted_at`, `reference` | `expires`, `licence_url`, `notes` |

### Reason values

| Value | Meaning |
|-------|---------|
| `us_government_work` | Created by the US federal government (17 USC 105) |
| `cc0` | Dedicated to the public domain via Creative Commons Zero |
| `expired` | Copyright term has expired |
| `cc_by_4` | Creative Commons Attribution 4.0 International |
| `cc_by_sa_4` | Creative Commons Attribution-ShareAlike 4.0 International |
| `cc_by_nc_4` | Creative Commons Attribution-NonCommercial 4.0 International |
| `explicit_permission` | Rights holder has granted permission directly |

This list will grow as new licence types are encountered.

### Defaults and safety

The ingester always sets `status: restricted` for new records. This is the safe default - no content is served beyond extracted claims until someone actively determines the copyright status and provides justification.

Changing the status away from `restricted` requires filling in the appropriate justification fields. The workbench enforces this by presenting a structured form that requires the conditional fields based on the selected status. A reviewer cannot simply mark something as `public_domain` without providing a reason.

All changes to the copyright field are tracked in git history, providing a full audit trail of who changed the status, when, and what justification they provided.

### References

For `licensed` status, the `reference` field points to evidence of the permission: a file path within the repository (e.g. `correspondence/cbs-2026-04-11.pdf`), a URL to an archived email, or similar. The point is that the claim of permission is verifiable.
