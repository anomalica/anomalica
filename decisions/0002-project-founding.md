# 0002. Build an international reference platform for anomalous phenomena

Date: 2026-03-20
Status: accepted

## Context

The existing landscape for UAP/NHI (Unidentified Aerial Phenomena / Non-Human Intelligence) information has several structural problems:

- Major platforms (MUFON, NUFORC, Enigma Labs, AARO) are US-based and US-controlled.
- No multilingual, jurisdiction-independent, structured reference exists.
- Information is fragmented across incompatible databases, locked in podcast audio, and largely inaccessible to non-English speakers.
- No platform implements tamper-evident storage or cryptographic chain of custody for evidence.
- AARO (the US Department of Defence's All-domain Anomaly Resolution Office) is actively seeking to centralise civilian data under US government control.

A landscape analysis was conducted covering existing platforms (WikiDisc, UAPedia.ai, The Black Vault, Enigma Labs, MUFON, NUFORC, GEIPAN), data federation efforts (OpenADS, Project Galileo, Sky360, UFODAP), and the state of multilingual resources. Japan, designated by AARO as the top global UAP hotspot, has no structured reporting infrastructure.

## Decision

Build an international, jurisdiction-independent reference platform. The platform curates, analyses, translates, and presents structured information with full source attribution and algorithmic evidence scoring.

Note: Anomalica was founded by a single person. "We" is used throughout these records for consistency as the project grows. At the time of writing, there is one contributor.

Principles:
- Not aligned with any national interest
- Not government-funded from any country
- No advertising, no sponsorship, no data monetisation
- All project code and data are open source
- Self-funded initially

### Jurisdiction-independent in practice, not just in principle

Much of the existing UAP discourse is centred on the United States - US legislation, US military testimony, US media. This is understandable given recent Congressional activity, but the phenomenon is global and the platform must reflect that.

Anomalica treats all jurisdictions, languages, and sources equally. American Congressional hearings receive the same treatment as Japanese parliamentary activity, French GEIPAN case files, or Brazilian military archives. No country's perspective is centred. No country's institutions are treated as more authoritative by default.

This is reflected in structural choices: the primary domain is Icelandic (.is), the platform is multilingual from the start, English-language content uses British English throughout, and AI verification uses models from different geopolitical jurisdictions. These are not anti-American choices - they are choices that avoid defaulting to any single national perspective.

## Consequences

The project requires a technology stack, hosting strategy, and legal structure designed for independence and resilience. The scope is large and the project may not succeed, but the architecture is designed so that accumulated data survives even if the platform itself does not.
