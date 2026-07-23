# Content format

The content format is the assembler's output: one rendered article per language, consumed by the Hugo static site. It is the last interchange in the pipeline (brief -> assembler -> content -> site).

The canonical machine-readable field list is [`reference/format-specs.yaml`](../reference/format-specs.yaml) (`types.content`); this document is its narrative companion. Both are marked **provisional** - see [Open questions](#open-questions).

> **Status: provisional.** Unlike the record, digest, and brief formats, content has no ratified schema. Its on-disk layout is an open decision and its audit-field binding is unsettled. The fields below are the ones the current docs agree on; treat nothing here as final until the layout decision lands and the assembler workspace confirms what it emits.

## Shape

Each language version is a markdown file with YAML frontmatter:

```yaml
---
title: Privacy Policy
description: "How Anomalica handles visitor data."
directives:
  - "Use formal tone throughout"
  - "Reference GDPR and ePrivacy Directive by full name"
---

[body - assembler-written for generated articles, hand-written for static pages]
```

The frontmatter is **human-controlled**; the assembler reads it but never modifies it, overwriting only the markdown body. The body is assembler-controlled for generated articles and human-controlled for static pages (legal/policy).

## Frontmatter fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Article or page title. |
| `description` | string | no | Short description. |
| `directives` | list | no | Article-level presentational instructions to the assembler (see [Directives](#directives)). Style/formatting/naming only - never factual. |
| `metadata` | object | no | Optional metadata the assembler reads but does not modify. Sub-shape not yet specified. |

There is **no cost or billing field** in content frontmatter. Per-artefact AI usage is provenance only (model, version, token counts). As of 2026-06-29 it is NOT surfaced on the public site (the per-artefact usage/cost panels are pulled - Mark's reversal); the provenance data is kept in frontmatter and the AI-operation ledger for possible later surfacing (likely the internal workbench, TBD). Any notional cost is a pure derivation from published list prices, never stored here.

## Directives

Directives instruct the assembler on presentation (style, formatting, naming, language conventions); they never alter factual content. They are collected most-specific-first and merged, with the more specific winning on conflict:

1. The article's own frontmatter `directives` (this article, this language).
2. A per-article `<slug>.directives.yaml` sidecar (this article, all languages) - the home for a single-article rule that should shape every language render, written once rather than duplicated into each `<slug>.<lang>.md`.
3. At each folder from the article's directory up to the content root: `_directives.<lang>.yaml` (this language) then `_directives.yaml` (all languages).

Directive files (`_directives*.yaml`, `<slug>.directives.yaml`) are assembler inputs, not content. Hugo serves stray `.yaml` files raw, so the site excludes them with an `ignoreFiles` rule in `hugo.toml` matching the `directives` stem. Naming contract: keep the stem `directives` with a `.yaml`/`.yml` extension and an optional `.<lang>` segment; if it ever changes, tell the site to widen the rule.

## Review and verification sidecars

Both sit alongside the article files and are written by other processes (not the assembler), and both are informational - never publication gates ([0021](../decisions/0021-content-review-lifecycle.md)).

- `review.yaml` - append-only human-review log. Each entry: `date`, `language`, `reviewer`, `body_hash` (SHA-256 of the markdown body at review time), `comment`. Current status is computed at build time by comparing the current body hash to the most recent matching-language entry.
- `verification.yaml` - automated AI verification report ([0010](../decisions/0010-auditable-assembly.md)): a different model checks every assertion traces to the knowledge graph.

## Auditable assembly

An article is built from exactly one brief, and [0010](../decisions/0010-auditable-assembly.md) requires it be reconstructable to the precise graph slice it came from - the brief's `brief_hash` (`built_from`). See [brief-format.md](brief-format.md) for `brief_hash`. **Where this binding is carried on the content side is unsettled** (the frontmatter is assembler-preserved, so it is not a natural home) - see Open questions.

## Open questions

These block ratification of this format:

1. **On-disk layout.** Flat with a language suffix (`pages/<section>/<slug>.<lang>.md`, per [assembler.md](assembler.md)) versus document-first directories (`<slug>/index.{lang}.md`, per [content-lifecycle.md](content-lifecycle.md)). The two current docs disagree; assembler.md flags its own layout section as out of date. Unratified.
2. **Audit binding location.** Where `built_from`/`brief_hash` and the article/body hash are carried for a content article, given the frontmatter is human-controlled and assembler-preserved.
3. **`metadata` sub-shape** and whether any provenance (`ai_usage`, node identity/slug) belongs in content frontmatter - to be confirmed with the assembler workspace against what it actually emits.

   Partly answered 2026-07-23: the assembler *does* emit `ai_usage` into article frontmatter - measured across 53 articles. Whether it belongs there is still open, but one constraint binds it either way: **no cost, price, or currency field**, per the canonical rule in [format-specs.yaml](../reference/format-specs.yaml) and [digest-format.md](digest-format.md#ai_usage). Those articles carried `notional_cost_usd` and `price_basis`; both are dropped at the producer and clear as articles re-assemble. This instance is the sharpest one, because `content/` feeds the public site - a cost-shaped field here is readable by anyone, not just the dev layer. See [0037](../decisions/0037-ai-operation-ledger.md), amended.

   **`ai_usage` in article frontmatter has no live consumer**, which makes the remaining question cheap to settle. `site/layouts/partials/` holds `ai-usage.html`, `ai-usage-grouped.html`, and `ai-usage-aggregate.html`, and nothing in `layouts/` includes any of them - dead since the 2026-06-29 display-off reversal (usage data kept, not publicly surfaced). So dropping `ai_usage` from content frontmatter would break no rendering today; the case for keeping it is provenance-on-the-artefact, not display. Decide it on that basis rather than on consumer impact, and note that the assembler can always re-derive from the digest.

   Those dead partials also settle the shape question independently: they read `.tokens.input` / `.tokens.output` and derive cost themselves from a prices dict. The consumer-derived cost model this project just mandated already existed in the site layer, and it was written against **nested** tokens.

   **Decided 2026-07-23: `ai_usage` comes out of article frontmatter.** Four reasons, in order of weight:

   - It is the *propagation path*, not just a location. Carry-forward of `ai_usage` into content frontmatter is precisely how a forbidden cost field reached 53 public articles. Dropping the two fields fixes this instance; dropping the carry-forward removes the class, so the next field that should not be public has no route to get there.
   - No provenance is lost. The digest carries `ai_usage` and the AI-operation ledger ([0037](../decisions/0037-ai-operation-ledger.md)) is its durable home once built. Both are dev-layer. Removing the copy in the most-exposed layer removes a duplicate, not a record.
   - No consumer breaks, as established above.
   - It matches the 2026-06-29 position: usage data kept, not publicly surfaced, with any future surfacing expected in the internal workbench rather than the public site.

   **Sequenced behind open question 2, not independent of it.** Re-deriving an article's usage later requires the article to bind back to the brief and graph slice it came from, and where that binding lives is exactly what question 2 leaves unsettled. Removing `ai_usage` before the binding lands would leave an article with neither its usage nor a route to recover it. That binding is required by [0010](../decisions/0010-auditable-assembly.md) regardless, so this is a sequencing constraint rather than a dependency that might not arrive: settle question 2, then the assembler stops emitting `ai_usage`, and it clears from existing articles as they re-assemble.

   The `metadata` sub-shape and node identity/slug halves of this question remain open.
