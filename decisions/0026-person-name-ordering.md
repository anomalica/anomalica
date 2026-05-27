# 0026. Person name ordering

Date: 2026-05-20
Status: accepted

## Context

[Decision 0023](0023-person-naming-convention.md) established that person nodes use plain legal names only - no titles, ranks, honourifics, or suffixes. The examples in 0023 happen to be written in "First Last" order ("David Fravor", "Marco Rubio") but the decision text itself does not state which ordering is canonical.

This silence caused drift during pipeline implementation. An extraction prompt was written that read the examples as policy and explicitly forbade "Last, First" ordering, then a separate experiment harness was kept in "Last, First" form, then a graph-wide rewrite was nearly executed to "fix" the inconsistency. The actual problem was that 0023 had never specified ordering.

We need an explicit rule.

## Decision

**Person nodes use "Last, First Middle" ordering as the canonical form.**

- "Fravor, David", not "David Fravor"
- "Pais, Salvatore", not "Salvatore Pais"
- "Rubio, Marco", not "Marco Rubio"
- "Elizondo, Luis", not "Luis Elizondo"

The no-titles rule from 0023 stands unchanged - this decision is purely about ordering.

Single-name historical figures and pseudonyms remain as-is ("Madonna", "Whiskey-99"). Names in non-Latin scripts follow the conventions of that script (kanji order in Japanese names, etc.).

The reverse form ("David Fravor") is stored as an alias on the person node, so case-insensitive matching during integration handles either form in source text.

### Why surname-first

- **The surname is the durable identifier.** First names change in informal contexts (Lue/Luis, Dave/David); the surname is what remains stable across speakers, registers, and records.
- **The surname is often the only part initially known.** Formal references introduce people as "Captain Fravor" or "Senator Rubio" before any first name appears. Putting the surname first means the part you have lines up with where the name starts.
- **Surname-first sorts usefully.** The vault, search results, and any alphabetic listing group by surname, which is how humans actually look people up.
- **It matches the project's "most important first" theme.** Dates use YYYY-MM-DD. Place names use largest-unit-first ("USA, Nevada, Area 51"). Japanese addresses go country-prefecture-city-block-number. Surname-first is the same principle applied to people.
- **It is the format on official identification.** Passports, government records, academic citations, and library catalogues all use surname-first. The graph mirrors how the underlying records actually name people.

### Presentation reorders for prose

The assembler is responsible for reordering to "First Last" when generating natural-language prose ("Commander David Fravor, who at the time..."). Storage uses one canonical form; presentation handles the rest.

## Consequences

- The production extraction prompt, the experiment harness, and any future ingestion code all emit "Last, First Middle".
- The existing graph is already in this form, so no migration is required.
- The matcher tolerates either ordering, so historical aliases and source-text variants integrate correctly.
- This decision clarifies but does not supersede 0023. 0023's titles/ranks/honourifics rule continues to govern; 0026 specifies the ordering left open by 0023.
