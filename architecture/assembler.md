# Assembler

The assembler reads from the knowledge graph (a structured database of interconnected facts) and produces articles. It also applies directives - durable instructions extracted from human edits that affect presentation without altering meaning.

## Inputs

- Knowledge graph (SQLite - a lightweight file-based database, rebuilt from digests, read-only)
- Directives (from the content hierarchy)
- Existing articles (for incremental updates)

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

**Broader directives** live in `_directives.yaml` files in the content folder hierarchy:

```
content/
  _directives.yaml              (global - all languages, all content)
  en/
    _directives.yaml            (all English content)
    people/
      _directives.yaml          (all English people articles)
      david-fravor.md           (article with its own directives in frontmatter)
  ja/
    _directives.yaml            (all Japanese content)
    events/
      _directives.yaml          (all Japanese events articles)
```

When assembling an article, the assembler collects directives from the bottom up: article frontmatter, then the nearest `_directives.yaml`, then parent folders up to the root. More specific directives take precedence over more general ones.

If an article is renamed or moved, its frontmatter directives travel with it. If a content folder is restructured, the `_directives.yaml` files move with their folders. Nothing gets orphaned.

### Emergent style

Over time, the accumulated directives form an emergent style guide shaped by community input rather than top-down editorial decisions. Each language version develops its own set of directives through its community's edits.

## Assembly audit trail

Every article assembly is auditable. A reader can verify that the article was produced from the inputs claimed and nothing else (decision 0010).

### What is recorded per assembly

- **Article hash** - SHA-256 (a cryptographic hash that uniquely fingerprints content) of the assembled article content
- **Prompt hash** - SHA-256 of the full prompt sent to the artificial intelligence (knowledge graph data + directives + system template + previous article version)
- **Directives active** - the specific directives that were collected and applied
- **Knowledge graph version** - which state of the knowledge graph was used

### Prompt reconstruction

The full prompt is not stored directly (it would be large and redundant). Instead, all its components are versioned independently:

- The knowledge graph is versioned (SQLite file)
- The directives are versioned (in git with the content)
- The system prompt template is versioned (in the assembler repo)
- The previous article version is versioned (in git with the content)

A reader can reconstruct the exact prompt by combining these components at their recorded versions. The hash of the reconstructed prompt must match the stored prompt hash. If it does, the article was produced from exactly these inputs. If it doesn't, something was altered.

### Prompt inspector

The site provides a prompt inspector page for each article. This is a client-side JavaScript tool that:

1. Fetches the component versions (knowledge graph data, directives, system template, previous article)
2. Assembles them into the full prompt
3. Hashes the result
4. Compares against the stored prompt hash
5. Displays the reconstructed prompt and the match/mismatch status

## Independent verification

After assembly, a different AI model from a different provider verifies that every assertion in the article traces to the knowledge graph (decision 0009). The verification report is stored alongside the article.

### Verification report

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

The platform targets 30 languages (decision 0022). English-language content uses British English throughout.
