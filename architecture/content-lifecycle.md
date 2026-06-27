# Content Lifecycle

How content flows from generation through review, and how the directory structure supports it.

## Directory structure

Content is organised document-first. Each document is a directory containing all its language versions and associated metadata.

```
content/
  _directives.yaml                    # global directives (all languages)
  pages/
    _directives.yaml                  # directives for all pages
    privacy/
      index.en.md                     # English version
      index.ja.md                     # Japanese version
      index.zh.md                     # Mandarin version
      ...                             # (up to 30 language files)
      review.yaml                     # human review log
      verification.yaml              # AI verification report
  people/
    _directives.yaml                  # directives for all people articles
    david-fravor/
      index.en.md
      index.ja.md
      ...
      review.yaml
      verification.yaml
  events/
    2004-uss-nimitz-encounter/
      index.en.md
      ...
      review.yaml
      verification.yaml
```

### What the assembler writes

The assembler writes only the `index.{lang}.md` files. It overwrites the markdown body but preserves the YAML frontmatter. Everything else in the directory (review.yaml, verification.yaml) is written by other processes and left untouched.

### What the assembler reads

When assembling a document, the assembler reads:

1. The knowledge graph (SQLite, read-only)
2. The document's frontmatter, including any article-level directives
3. The `_directives.yaml` hierarchy from the document's folder up to the root
4. The existing body content (for incremental updates)

The assembler does not read review.yaml or verification.yaml.

## Content files

Each language version is a markdown file with YAML frontmatter:

```yaml
---
title: Privacy Policy
description: "How Anomalica handles visitor data."
directives:
  - "Use formal tone throughout"
  - "Must mention GoatCounter analytics by name"
  - "Reference GDPR and ePrivacy Directive by full name"
---

[body content - written by the assembler or by hand for static pages]
```

The frontmatter is human-controlled. The assembler reads it for directives and metadata but never modifies it. The body is assembler-controlled for generated articles, or human-controlled for static pages like legal documents.

## Directives

Directives are instructions to the assembler about how to present content. They affect style, formatting, naming, and language conventions. They do not alter factual content (see assembler architecture for the full directive model).

Directives live in two places:

**Article-level**: in the document's own frontmatter under the `directives` key. These are specific to one document and travel with it.

**Folder-level**: in `_directives.yaml` files in the content hierarchy. These apply to all documents in that folder and below. The assembler collects directives from the document outward, with more specific directives taking precedence.

## Human review

Human reviews are an audit trail recorded in `review.yaml` within each document directory. The file is an append-only list of review events:

```yaml
- date: 2026-04-02
  language: en
  reviewer: Dana Okafor
  body_hash: "sha256:a1b2c3d4e5f6..."
  comment: "Verified GoatCounter section is accurate"

- date: 2026-04-03
  language: de
  reviewer: Hans Mueller
  body_hash: "sha256:f6e5d4c3b2a1..."
  comment: "Datumsformat sollte europaeische Konvention verwenden"
```

### Fields

- **date**: ISO 8601 date of the review
- **language**: language code of the version reviewed (matches the filename suffix)
- **reviewer**: name of the reviewer
- **body_hash**: SHA-256 hash of the markdown body (everything after the frontmatter closing `---`) at the time of review
- **comment**: free-text feedback in any language

### Computing current status

At build time, for a given language:

1. Hash the current body of `index.{lang}.md`
2. Find the most recent entry in review.yaml where `language` matches
3. Compare body_hash values
4. If equal: reviewed (show reviewer name, date, comment)
5. If not equal: content has changed since last review
6. If no matching entry: never reviewed

### Review-to-directive bridge

Reviews do not instruct the assembler. When a reviewer identifies an issue that requires a content change:

1. A human reads the review comment
2. If it is a presentational issue, the human adds or updates a directive in the document's frontmatter
3. If it is a factual issue, the human submits correcting evidence through the ingestion pipeline
4. The assembler regenerates the affected content
5. The body hash changes, and the review status resets to "unreviewed" for the affected languages

## AI verification

AI verification is a separate, automated process (see decision 0010 and the assembler architecture). After assembly, a different AI model checks that every assertion traces to the knowledge graph. The verification report is stored in `verification.yaml` within the document directory.

Human review and AI verification are independent. An article can have one, both, or neither. Both are informational indicators, not publication gates.

## Static pages

Legal documents, policy pages, and other static content follow the same structure but are not assembled from the knowledge graph. Their body content is written by hand (or generated and then manually maintained). Directives in their frontmatter serve as notes about style and content requirements rather than assembler instructions.

Static pages still participate in the review system. A reviewer can review any page regardless of how it was created.
