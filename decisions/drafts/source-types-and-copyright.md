# Source types and copyright handling

Date: 2026-03-21
Status: draft

## Context

The knowledge graph will be built from a variety of source material with different accessibility and copyright characteristics. The platform needs to extract meaning from all of these without infringing copyright or reproducing content that belongs to others.

## Decision

The platform will ingest the following types of sources:

**Public domain and openly accessible:**
- Government documents, FOIA releases, declassified material
- Congressional and parliamentary records and testimony
- Academic papers (open access)
- Podcast and YouTube video transcripts (publicly available audio/video, transcribed for extraction)

**Copyrighted but extractable under fair dealing:**
- Books
- News articles
- Academic papers (paywalled)
- Documentary transcripts

**Original submissions:**
- Documents, testimony, sensor data, and other material deposited directly with Anomalica by submitters. These will be held by the platform and may be published with the submitter's consent (see ADR 0016 for source identity and ADR 0017 for conditional release).

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
