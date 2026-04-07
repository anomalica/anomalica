# 0023. Person naming convention

Date: 2026-04-01
Status: accepted

## Context

Person nodes in the knowledge graph (a structured database of interconnected facts) need a canonical name. People in the unidentified anomalous phenomena domain often carry military ranks (Commander, Lieutenant), government titles (Senator, Secretary), professional titles (Dr, Professor), and honourifics that vary by culture and change over time. David Fravor was Commander Fravor during the Nimitz incident but is now retired. Marco Rubio has been Senator Rubio since 2011 but may not always be.

The question is whether titles and ranks should be part of the canonical name or handled separately.

## Decision

**Person nodes use plain legal names only. No titles, ranks, honourifics, or suffixes.**

- David Fravor, not Commander David Fravor
- Marco Rubio, not Senator Marco Rubio
- Luis Elizondo, not Luis "Lue" Elizondo
- Leslie Kean, not Dr Leslie Kean (if applicable)

Titles and ranks are properties of a person at a point in time, not part of their identity. They are captured as claims in the knowledge graph:

- "David Fravor held the rank of Commander in the US Navy"
- "David Fravor commanded Strike Fighter Squadron 41 (VFA-41)"
- "Marco Rubio served as chair of the Senate Intelligence Committee"

Each such claim carries a date range and source attribution, building a natural history of positions held as more records are ingested.

This convention applies across the entire pipeline:

- **Ingester**: speaker rosters in audio/video records use plain names
- **Digester**: Person nodes are created and matched using plain names; titles are extracted as separate claims
- **Assembler**: may reintroduce titles contextually when presenting articles, drawing from claims in the knowledge graph (e.g. "David Fravor, who at the time held the rank of Commander")

### Aliases

Informal names, shortened forms, and transliterations are stored as aliases on the Person node, not as the canonical name:

- Canonical: Luis Elizondo. Aliases: Lue Elizondo, Lue.
- Canonical: David Grusch. Aliases: Dave Grusch.

The digester's alias matching handles these during integration (see digester architecture).

### Multilingual presentation

The canonical name in the knowledge graph is language-neutral (typically the name as used in the person's own culture). The assembler handles language-specific conventions during article generation:

- **English**: "Fravor, who held the rank of Commander" (title as contextual information)
- **Japanese**: "フレーバー司令官" or "フレーバー氏" (honourific/rank as required by Japanese convention)
- **French**: "le commandant Fravor" (title integrated as French convention requires)

These are presentation decisions made by the assembler using claims from the graph and language-specific directives. The underlying Person node is always just the plain name.

### Non-Latin names

For people whose primary name is in a non-Latin script, the canonical name uses that script. Romanisations are stored as aliases:

- Canonical: 岸田文雄. Aliases: Kishida Fumio, Fumio Kishida.

The assembler selects the appropriate form for each language.

## Consequences

- Person matching in the digester is simpler (no title variations to normalise)
- Names are stable over time (no updates needed when someone retires or changes role)
- Cultural conventions are handled at presentation, not storage
- The knowledge graph naturally accumulates a career/role history as more records are ingested
- Requires the assembler to be culturally aware when generating articles in different languages
