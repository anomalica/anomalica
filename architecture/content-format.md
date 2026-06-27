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

There is **no cost or billing field** in content frontmatter. Per-artefact AI usage, where surfaced, is provenance only (model, version, token counts); any notional cost shown on the site is derived by the site from published list prices, not stored here.

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
