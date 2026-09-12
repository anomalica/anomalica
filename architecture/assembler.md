# Assembler

The assembler reads from the knowledge graph (a structured database of interconnected facts) and produces articles. It also applies directives - durable instructions extracted from human edits that affect presentation without altering meaning.

## Inputs

- Knowledge graph (SQLite - a lightweight file-based database, built by the assimilator from digests, read-only)
- Directives (from the content hierarchy)
- Existing articles (for incremental updates)

### Input contract: assembling one entity article (`--node` mode)

> **Transitional.** Per [decision 0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md) the assembler becomes a pure writer whose sole input is a brief (the synthesiser selects the facts; the writer no longer reads the graph). The direct-graph-read contract below is the current/interim behaviour, superseded by brief-input once the synthesiser lands.

Grounded against the assembler's code. The assembler reads the assimilator's graph directly via `sqlite3` (raw SQL, no ORM) over `knowledge.db` (`--db`; host path `~/.local/share/assimilator/knowledge.db` - the relocation off `~/.local/share/digester/` is done, and only an empty 0-byte `anomalica.db` remains there). It reads exactly four tables - `nodes`, `claims`, `records`, `claim_node_refs` - via three queries:

1. **Load node** - the entity's `id`, `node_type`, `name`, `metadata`, matched by id or case-insensitive name.
2. **Claims for node** - every claim where the entity is the `speaker_id` OR is referenced via `claim_node_refs`, left-joined to `records` (title, date, reference, content_hash, friendly_name - the citation and deep-link provenance) and to `nodes` (speaker name). Per claim it reads `id`, `content`, `original_excerpt`, `claim_type`, `attestation`, `location_in_record`, `date`, `date_end`. Ordered by record date then `location_in_record`; de-duplicated by claim id.
3. **Related nodes** - nodes co-occurring in the same claims (a `claim_node_refs` self-join), ranked by shared-claim count, top 30 - the "related entities you may link to" prompt block.

Selection and ordering: claims are selected by speaker-of OR referenced-by, with **no score/confidence threshold and no `claim_role` filter**, ordered chronologically by source then document order. The model then writes free-form encyclopaedic prose from those claims plus the related-node list - the assembler imposes no role-based sectioning and consults no `confidence`, `claim_role`, or `corroborations` in selection or ordering (those columns/tables exist but are not read). After the model returns, a deterministic pass re-attaches per-claim provenance (quote, claim_id, record_hash, workbench_url) to the references from the already-fetched claims - no extra query.

(Record-mode assembly, used for the per-record inspection pages of 0031, reads the digest YAML rather than the database - a separate read-contract, to be documented when that work lands.)

## Outputs

Updated articles in content.

## When the assembler runs

- **Knowledge graph updated** - the digester has processed new material, so articles need updating to reflect new claims or changed evidence scores.
- **New directive received** - a human has submitted a presentational correction, so affected articles need reassembly.

The assembler does not modify the knowledge graph. It is a consumer, not a producer.

## Articles

Articles are assembled by artificial intelligence from knowledge graph data. The artificial intelligence arranges existing claims, attributions, and relationships into readable prose. It does not create information (decision 0008).

Each article is assembled per-language from the knowledge graph rather than translated from a canonical English version. The knowledge graph is language-independent; the articles are language-specific.

### References

Every article includes references at the bottom linking each claim to its source. A reference includes:

- The record title and date (e.g. "Lex Fridman Podcast #122, 2020-09-08")
- A link to the original source material (URL, where available)
- The location within the record (timestamp, page number)
- Who made the assertion (the speaker)
- A link to the digest in the digests repository, where readers can see exactly how the claim was extracted and report errors via the repository's issue tracker

This gives readers two paths: follow the link to the original source to verify the claim themselves, or follow the link to the digest to challenge how the claim was interpreted.

## Directives

Directives are how humans influence article presentation without directly editing content that would be overwritten on the next assembly.

### What directives can change

Directives affect presentation, not meaning:

- **Style and grammar** - sentence structure, word choice, readability
- **Disambiguation** - clarifying ambiguous phrasing
- **Formatting** - ordering of sections, use of tables versus prose, timeline direction
- **Naming and transliteration** - how names are romanised, which form of a name to use after first mention
- **Language conventions** - language-specific presentation rules

### What directives cannot change

Directives cannot alter the factual content of an article. Any edit that changes the meaning of a claim - adding information, removing information, reframing what a source said - is rejected. The assembler detects meaning-altering edits during directive extraction and discards them.

If a reader believes the factual content is wrong, there are two paths depending on the nature of the error:

- **Extraction error** (the claim was misinterpreted from the source) - the reader follows the reference link to the digest and opens an issue on the repository. A correction to the digest triggers a database rebuild and article reassembly.
- **New evidence** (the claim is accurately extracted but contradicted by other sources) - the reader submits the contradicting source as a new record through the ingestion pipeline. The new claims enter the knowledge graph and the evidence scoring handles the conflict.

Facts flow through the knowledge graph, not through directives.

### How directives work

1. A human reads an assembled article on the site
2. The human edits the article (like editing a wiki page)
3. AI compares the original and edited versions
4. AI classifies each change as presentational or meaning-altering
5. Meaning-altering changes are rejected
6. Presentational changes are extracted as one or more directives - durable, language-specific instructions that capture the intent behind the changes
7. Directives are stored in the content hierarchy (see below)
8. The assembler applies collected directives when assembling or reassembling articles

### Directive storage

Directives live alongside the content they apply to. There is no separate directive tree to keep in sync.

**Article-level directives** live in the article's own frontmatter:

```yaml
---
title: David Fravor
directives:
  - "Use Commander as the rank throughout, not Cmdr"
  - "Present the Nimitz timeline in chronological order"
---
```

**Broader directives** live in `_directives.yaml` files in the content folder hierarchy. The content layout is flat with a language *suffix* (`pages/<section>/<slug>.<lang>.md`), not a per-language directory tree, so the hierarchy is the folder chain and language is itself a file suffix (`_directives.<lang>.yaml`):

```
content/
  _directives.yaml                     (global - all languages, all content)
  _directives.en.yaml                  (global, English only)
  pages/
    _directives.yaml                   (all pages, all languages)
    people/
      _directives.yaml                 (all people articles, all languages)
      _directives.en.yaml              (English people articles)
      david-fravor.directives.yaml     (THIS article, ALL languages - the sidecar)
      david-fravor.en.md               (this article, English - frontmatter directives)
      david-fravor.ja.md               (this article, Japanese - frontmatter directives)
    records/
      _directives.yaml                 (all record inspection pages)
```

A `_directives.yaml` (or a per-article `<slug>.directives.yaml` sidecar) is a list of presentational instruction strings (or a mapping carrying a `directives:` list).

The per-article sidecar `<slug>.directives.yaml` is the home for a single-article directive that should shape **every** language render (e.g. "use the full name Luis Elizondo, never the surname alone") - written once, not duplicated into every `<slug>.<lang>.md` frontmatter. A directive that is genuinely language-specific (a phrasing rule that only makes sense in one language) goes in that language's `<slug>.<lang>.md` frontmatter instead.

When assembling an article, the assembler collects directives most-specific-first: (1) the article's own frontmatter (article + this language); (2) the per-article `<slug>.directives.yaml` sidecar (article, all languages); (3) at each folder from the article's directory up to the content root, the `_directives.<lang>.yaml` (this language) then the `_directives.yaml` (all languages). Duplicates collapse to their most-specific position; on conflict the earlier (more specific) directive wins. A directive can only ever affect presentation - one that asks for a factual change is ignored.

These directive files (`_directives*.yaml`, `<slug>.directives.yaml`) are assembler inputs, not content. Hugo does **not** ignore them by default - verified on Hugo 0.152.2 extended, a `.yaml` file under `content/pages/` is copied verbatim into `public/` and served raw at its URL, exposing the directive text. The site excludes them with an `ignoreFiles` rule in `hugo.toml` matching the `directives` stem (`ignoreFiles = ['directives(\.[A-Za-z-]+)?\.ya?ml$']`). Naming contract: keep the stem `directives` with a `.yaml`/`.yml` extension (and an optional `.<lang>` segment) so the site's rule covers every file the assembler reads; if the stem or extension ever changes, tell the site to widen the rule.

If an article is renamed or moved, its frontmatter directives travel with it. If a content folder is restructured, the `_directives.yaml` files move with their folders. Nothing gets orphaned.

### Emergent style

Over time, the accumulated directives form an emergent style guide shaped by community input rather than top-down editorial decisions. Each language version develops its own set of directives through its community's edits.

## Assembly audit trail

Every article assembly is auditable. The machine-owned `built_from` and
`built_by` frontmatter contracts are defined in
[content-format.md](content-format.md#auditable-assembly); this section explains
their purpose rather than defining a second field shape.

### What is recorded per assembly

- **Input identity** - the brief or record binding and claim hashes in
  `built_from`.
- **Output identity** - SHA-256 of the exact article body bytes in
  `built_by.body_sha256`.
- **Logical prompt identity** - separate SHA-256 values for the authored user
  prompt, authored system prompt and resolved directives.
- **Execution identity** - route-qualified model, transport, exact submitted
  user/input payload hash, role mapping, runner version and configuration hash,
  and whether an added execution scaffold is absent or opaque.

### Prompt reconstruction

The authored logical prompts and resolved directives are independently
reconstructable and hash-checkable. A route may deliver them in different
protocol roles. In particular, OpenCode receives the logical system prompt as a
prefix in its user message and adds a hidden system scaffold that its CLI does
not expose. The article therefore records the exact submitted user payload and
marks that scaffold `opaque`; it does not claim that the complete provider
context or native system-role delivery can be reconstructed. The previous
article version is not a prompt component: assembly remains a function of the
current brief and directives rather than its own output history.

### Prompt inspector

The site prompt inspector reconstructs the logical prompt components, verifies
their separate hashes, displays the submitted-payload role mapping and transport
identity, and states when an execution scaffold is opaque. It must not fabricate
or display hidden scaffold bytes as reconstructed content.

## Independent verification

After assembly, a different AI model from a different provider verifies that every assertion in the article traces to the knowledge graph (decision 0010). The verification report is stored alongside the article.

### Verification report

> The file layout below is out of date - it is not what the assembler emits today (the assembler writes no YAML). The current review/verification model (`verification.yaml` for the AI check, `review.yaml` for human review, in document-first directories) is in [content-lifecycle.md](content-lifecycle.md) and decision 0021, which is unratified pending the flat-versus-document-first layout decision. This section will be rewritten when that lands.

Each article has an accompanying review file:

```
content/en/people/david-fravor.md              (the article)
content/en/people/david-fravor.review.yaml     (the verification report)
```

The review file contains:

```yaml
article_hash: sha256:abc123...
verified_by: deepseek-v3
verified_at: 2026-03-26T14:30:00Z
result: pass
claims_checked: 47
claims_matched: 47
claims_flagged: 0
---
Full verification report text from the reviewing model.
Each claim was checked against the knowledge graph.
No unmatched assertions were found.
```

The frontmatter contains structured results. The body contains the full text of the review.

### Verification status on the site

At build time, Hugo checks whether a review file exists for each article and whether its `article_hash` matches the current article hash:

- **Hash matches** - the article has been verified since its last assembly. Green indicator.
- **Hash doesn't match** - the article has been reassembled since the last verification. Pending indicator.
- **No review file** - the article has never been verified. No indicator.

Articles can be published before verification. The verification status is informational, not a gate.

## Languages

The platform targets 30 languages (the governance charter). English-language content uses British English throughout.

## Page quality: what holds and what does not

Assessed 2026-09-08 by reading live pages as a stranger would and tracing each
sentence back to the source line behind it. Kept here so the same ground is not
re-walked. Structural gates pass on every failure below; none is visible without
reading the prose against its sources.

### What holds

**Separating several accounts drawn from one long narrative source.**
`/organisations/royal-australian-air-force` takes 94% of its 32 claims from one
book containing many distinct incidents, and keeps six of them whole and in
chronological order — reordering against the source's own order to do it
(citations run ch5, ch6, ch9, ch11, ch10, ch12). Nothing in the pipeline records
which account a claim came from; the writer reconstructs it from the claims,
because claims carry dates, names and places and are therefore self-describing.

**Synthesising many sources on one topic.**
`/places/ohio-wright-patterson-air-force-base-usa` draws 45 claims from 13
sources and changes source between consecutive citations 73% of the time — the
highest rate in the corpus — and is coherent. High source-switching is the mark
of topical synthesis, not of jumbling. **A low switch rate is the warning sign**:
it means one source dominates and the page is a paraphrase of one book.

**Deep attribution chains.** Four-relay claims are rendered with the chain
intact and with the non-confirmation stated ("Buchanan has never directly
confirmed Jorjani's account").

### What does not

**A single unreliable source is stated in our own voice.** The largest problem.
See `knowledge/one-source-stated-bare.md`. 20,605 claims are marked `bare_ok`
on one source; the whole corpus holds 138 claims with two or more independent
sources.

**A claim that MENTIONS an entity is treated as a claim ABOUT it.** Across 319
pages with 12+ references, on average half the claims on a page never name the
page's subject. The graph cannot distinguish the two cases: `claim_node_refs`
is `(claim_id, node_id)` with no role column. The symptom is an organisation
page accreting biography of whoever was named alongside it, and paragraphs that
begin "Separately, ..." because the writer knows the material does not belong
and has nowhere to put it.

**A page whose subject we hold no source about.** `/events/world-war-ii` has 36
claims from exactly two sources — a book on the Fatima apparitions and a podcast
on postwar technology evacuation — because no source in the corpus is about the
war. The two stories are each rendered coherently; the title promises an article
neither of them is.

**A name built for an index reaches the sentence.** See
`knowledge/an-index-entry-in-a-sentence.md`.

### Method note

Structural measurement did not find any of these and twice pointed the wrong
way: the source-switch rate means the opposite of what it looks like, and a
count of remaining bad links made with the same regex that could not see them
reported zero. Read the page, then read its source lines beside it.
