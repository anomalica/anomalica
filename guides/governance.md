# Anomalica governance charter

A living statement of what Anomalica is, how it is funded and licensed, what languages it commits to, and what it discloses. This consolidates the founding and governance decisions (formerly ADRs 0002 founding, 0003 name, 0004 transparency, 0005 licensing, 0022 languages) and the disclosure policy (formerly the operational-decision-visibility draft amending 0004). It is edited in place; git is the history. See [decisions/0001](../decisions/0001-record-decisions.md) for how decisions are routed across homes.

Anomalica was founded by a single person. "We" is editorial.

## What Anomalica is

An international, jurisdiction-independent reference platform for anomalous phenomena - unidentified anomalous phenomena (UAP) and non-human intelligence. It curates, analyses, translates, and presents structured information with full source attribution and algorithmic evidence scoring (confidence computed from measurable properties of the sources, not human editorial judgement).

The landscape it answers to: the major platforms (MUFON, NUFORC, Enigma Labs, the All-domain Anomaly Resolution Office) are US-based and US-controlled; no multilingual, jurisdiction-independent, structured reference exists; information is fragmented and largely inaccessible to non-English speakers. Japan, designated by AARO as the top global UAP hotspot, has no structured reporting infrastructure.

### Name

**Anomalica** - a coined word combining "anomaly" with the "-ica" suffix of encyclopaedic reference works (Britannica, Ars Technica, Botanica). It covers anomalous phenomena broadly (including consciousness, non-human intelligence, and reality) without narrowing to aerial phenomena. It is pronounceable across languages and sets the expectation of a reference work, not a blog or news site. The original working title, "Non-Human Intelligence Exchange", was dropped for reading as financial.

### Founding principles

- Not aligned with any national interest.
- Not government-funded from any country.
- Not run for profit; funded by donations.
- The core knowledge - curated claims, articles, and the knowledge graph - is always free, never paywalled or money-gated.
- No advertising, no sponsorship, no outside investment.
- All project code and data are open source.

### Jurisdiction-independent in practice

No country's perspective is centred and no country's institutions are treated as more authoritative by default. US Congressional hearings receive the same treatment as Japanese parliamentary activity, French GEIPAN case files, or Brazilian military archives. This is reflected structurally: the primary domain is Icelandic (.is), the platform is multilingual from the start, English-language content uses British English, and AI verification uses models from different geopolitical jurisdictions. These avoid defaulting to any single national perspective rather than being anti-American.

## Funding

A donation-funded not-for-profit. No advertising, sponsorship, or outside investment. The core knowledge is never paywalled.

## Licensing

**MIT** for all code; **CC0** (public domain) for all data. The platform's purpose is to make information freely available, and its real value is being the living, trusted, evolving source - not a snapshot of code or data, which cannot be duplicated by copying files. Restrictive licensing would contradict the aim, is unenforceable for a project with no enforcement resources, and adds friction for contributors. Contributions are released under these terms.

## Supported languages

Genuinely multilingual from the start - not English-first with translations bolted on. The supported set is chosen by a reproducible greedy set-cover over Unicode Common Locale Data Repository coverage data, ranking each language by the literate population it newly covers. The script and source data live in `brand/analyse-languages.py` and `brand/language-coverage.json` (the full ranked list is there); the methodology is published on the site as part of the transparency commitments.

**Final set: 28 translations producing 30 displayed languages, ~80% of the literate world population.** The 28 are the algorithmic top 30 minus three exclusions, plus one editorial addition:

- **Excluded:** Javanese and Malay (their literate readers use Indonesian, already supported) and Nigerian Pidgin (a spoken pidgin, not a written reference language; covered by English).
- **Added:** Ukrainian - the platform will not support Russian without Ukrainian during an active conflict between the two countries.
- Two displayed languages are mechanical conversions, not separate translations: Traditional Chinese (character conversion from Simplified) and American English (spelling/formatting conversion from British).

The language count is the primary driver of several architectural choices (Hugo for build performance at hundreds of thousands of pages; multi-script and right-to-left support; translation quality flagged per language and corrected via the directive system) - see the architecture docs and the translation-directives record.

### Rollout is staged

The set above is the destination, not the day-one output. Translation rolls out in stages: a **core language set first, then propagation outward by capacity**, rather than all languages at once. This refines the earlier "translate into all languages" intent - the full set remains the goal, the path to it is now incremental.

The core set is drawn from the top of the coverage ranking (the highest-coverage languages, English first); its exact membership is pinned when the rollout begins, and the remainder propagate as translation capacity allows. This shapes the scheduler's translate job, which targets the core set first rather than every language for every page.

## Disclosure: what is published, private, or secret

Transparency is most valuable as a deliberate act on the things that earn trust, not as a blanket setting on everything. The project's credibility rests on a narrow set of things being open; it does not rest on the founder publishing every operational and strategic decision. Three tiers:

- **Published** (public meta-repo + website): the product - all code, data, and the architecture decision records that govern them - plus the things that let a reader trust the platform is not captured or biased: money (where it comes from and goes), editorial independence, neutrality, methodology, governance, and legal structure.
- **Private but tracked** (the private `operations` repository): operational and strategic decisions - provider choices and negotiations, account management, business development, positioning, growth strategy, half-formed ideas, and the operational-security detail of hosting and domains. The founder may graduate a specific item to the published tier when it serves the mission.
- **Secret** (a password manager, never in any repository): credentials and API keys.

Security never relies on obscurity: the submission system, encryption, and conditional release are designed to be secure with full source visibility.

### Principle-level transparency for relocated operational records

Some decisions whose operational detail now lives privately in `operations` keep a thin, principle-level statement public here, so relocating them does not quietly reduce transparency:

- **AI-spend transparency** - AI processing runs on paid Anthropic services and local compute, met from the project's donation funding (see Funding above). Which services each component uses, and the billing detail, are tracked privately in `operations`.
- **Resilience and jurisdictional spread** - the platform is designed to survive adversarial pressure: domains and hosting are spread across resilient jurisdictions, the static site degrades gracefully (see the architecture record for the technical three-layer design), and the backend that holds reviewer-identity data runs in an EU, non-Five-Eyes jurisdiction with its encryption keys never written to disk - a choice made to protect reviewers. The specific registrars, defensive registrations, hosting providers, and backend location are operational-security detail, tracked privately in `operations`.
- **Privacy-respecting analytics** - site analytics are cookieless and aggregate: no personal data, no device fingerprinting, no cross-site tracking, and no consent banner required (compliant with the General Data Protection Regulation and the ePrivacy Directive). The specific analytics tool and its hosting are tracked privately in `operations`.
