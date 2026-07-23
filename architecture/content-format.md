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

An article is built from exactly one brief, and [0010](../decisions/0010-auditable-assembly.md) requires it be reconstructable to the precise graph slice it came from - the brief's `brief_hash` (`built_from`). See [brief-format.md](brief-format.md) for `brief_hash`.

The binding is carried in **two machine-owned frontmatter keys**, settled 2026-07-23. Not a sidecar and not a central index: provenance that can be moved, copied, or partially synced away from its article is provenance you cannot trust, and a sidecar's location would depend on the unsettled on-disk layout question below.

```yaml
built_from:                  # INPUTS - extends the shape already published
  source: brief              # brief | graph | record
  brief: {slug, hash}        # brief mode; slug locates, hash verifies
  record_hash: <sha256>      # record mode
  claims: [{id, hash}]       # every mode that has them
built_by:                    # OUTPUTS and generator
  model: <id>
  model_version: <id>
  transport: subscription    # subscription | api
  prompt_sha256: <sha256>    # the USER prompt
  system_prompt_sha256: <sha256>
  directives_sha256: <sha256>  # the RESOLVED directive list
  body_sha256: <sha256>
```

Two keys rather than one because they answer opposite questions: `built_from` is what went in, `built_by` is what came out and what made it. Between them they make three staleness questions independently answerable, and a regeneration pass needs all three:

| Question | Answered by | Meaning |
|----------|-------------|---------|
| Is my input stale? | `built_from` | The slice or a claim changed - reassemble. |
| Has a human edited this? | `built_by.body_sha256` | Do not clobber. Human edits are an *expected* flow: live-site edits return as directives, so this fires routinely. |
| Would this be built differently today? | `built_by.model`, `model_version`, `prompt_sha256` | The generator moved on. Neither hash above detects it, and the corpus quietly ends up in mixed generations. |

Four things about this are easy to get wrong:

- **The brief needs a slug as well as a hash.** `brief_hash` is an integrity check with no locator - briefs are addressed on disk by page slug, so a hash alone cannot find one. Today the locator is implicit in the article's filename matching the brief's, which breaks silently on any slug change.
- **`body_sha256` covers the body only, over the exact bytes written, computed last.** The assembler mutates the body after render and re-dumps the frontmatter, so a hash taken at render time never matches the file on re-read. Body-only also sidesteps the frontmatter re-dump entirely.
- **`model` and `model_version` are reconstructability inputs, not transparency fields.** They currently reach an article only via `ai_usage`, which is being removed (see Open questions). If they leave with it, an article no longer records what produced it and 0010 fails. Cost had to go; the model must not go with it.
- **`prompt_sha256` is a hash of the exact prompt string sent.** Assembler prompts are in-code rather than versioned files, so the digester's `{id, version, sha256, file}` shape does not apply here.
- **`directives_sha256` hashes the RESOLVED directive list, not the files.** Directives are resolved at build time from up to five sources (article frontmatter, a per-article sidecar, then `_directives.{lang}.yaml` and `_directives.yaml` walking up each folder), most-specific-first with dedup. The file set that produced a given article is not recoverable from the article, so only the resolved list is a meaningful audit record.

**The prompt is hashed in components, never as one blob**, and the transport is stamped alongside. A single "full prompt hash" cannot say *which* component differed, which is the whole point of the audit: the digest layer keys on `(model, prompt_sha, prep_version)` as separate components for exactly this reason, and the article equivalent is `(model, prompt_sha, system_prompt_sha, transport)`.

The transport must be stamped because the two paths do not currently send the same prompt: the subscription path passes a system prompt via `--append-system-prompt`, while the API path sends the user prompt with no system prompt at all. Identical inputs therefore produce different output depending on a runtime toggle.

**That divergence is a defect to close, not a difference to enshrine.** The `<COMPONENT>_USE_API` toggle selects a *billing* path; prompt content is supposed to be invariant across it. Articles assembled on the API path are currently generated without the system guidance the subscription path gets, so the corpus varies along an axis that is meant to be purely about money. Close the divergence, and keep `transport` and `system_prompt_sha256` in the block regardless - they make the historical divergence visible and attributable, and they detect any future one.

**Machine ownership needs no new machinery.** The assembler rewrites the whole file on every re-assembly and preserves only an enumerated allow-list (`_PRESERVE_KEYS`, currently just `directives`). Keeping these two keys out of that list makes machine ownership the default: a human edit inside them is discarded on the next assembly. The rule is stated here for humans, not built.

Coverage is partial and the gap is uneven. Brief mode already emits `built_from`; record mode binds by `record_hash`; **node mode, the majority of the corpus, carries no binding at all**. Node mode can carry claim hashes as soon as the assembler's query selects the `claim_hash` column that already exists in `knowledge.db`. Record mode cannot yet - digest claims carry no hash of any kind (`id`, `type`, `location`, `date`, `refs`, `quote`, `text`), so it binds by `record_hash` plus bare claim ids until a per-claim fingerprint lands in the digest.

## Open questions

These block ratification of this format:

1. **On-disk layout.** Flat with a language suffix (`pages/<section>/<slug>.<lang>.md`, per [assembler.md](assembler.md)) versus document-first directories (`<slug>/index.{lang}.md`, per [content-lifecycle.md](content-lifecycle.md)). The two current docs disagree; assembler.md flags its own layout section as out of date. Unratified.
2. ~~**Audit binding location.**~~ **Settled 2026-07-23** - two machine-owned frontmatter keys, `built_from` and `built_by`. See [Auditable assembly](#auditable-assembly) above. What remains is implementation, and it is larger than a field-siting job: none of 0010's audit trail is computed today (`hashlib` is not imported in the assembler). Node-mode graph-slice identity is a genuine unknown - the database slice has no snapshot mechanism of any kind, and node mode is the majority of the corpus.
3. **`metadata` sub-shape** and whether any provenance (`ai_usage`, node identity/slug) belongs in content frontmatter - to be confirmed with the assembler workspace against what it actually emits.

   Partly answered 2026-07-23: the assembler *does* emit `ai_usage` into article frontmatter - measured across 53 articles. Whether it belongs there is still open, but one constraint binds it either way: **no cost, price, or currency field**, per the canonical rule in [format-specs.yaml](../reference/format-specs.yaml) and [digest-format.md](digest-format.md#ai_usage). Those articles carried `notional_cost_usd` and `price_basis`; both are dropped at the producer and clear as articles re-assemble. This instance is the sharpest one, because `content/` feeds the public site - a cost-shaped field here is readable by anyone, not just the dev layer. See [0037](../decisions/0037-ai-operation-ledger.md), amended.

   **`ai_usage` in article frontmatter has no live consumer**, which makes the remaining question cheap to settle. `site/layouts/partials/` holds `ai-usage.html`, `ai-usage-grouped.html`, and `ai-usage-aggregate.html`, and nothing in `layouts/` includes any of them - dead since the 2026-06-29 display-off reversal (usage data kept, not publicly surfaced). So dropping `ai_usage` from content frontmatter would break no rendering today; the case for keeping it is provenance-on-the-artefact, not display. Decide it on that basis rather than on consumer impact, and note that the assembler can always re-derive from the digest.

   Those dead partials also settle the shape question independently: they read `.tokens.input` / `.tokens.output` and derive cost themselves from a prices dict. The consumer-derived cost model this project just mandated already existed in the site layer, and it was written against **nested** tokens.

   **Decided 2026-07-23: `ai_usage` comes out of article frontmatter.** Four reasons, in order of weight:

   - It is the *propagation path*, not just a location. Carry-forward of `ai_usage` into content frontmatter is precisely how a forbidden cost field reached 53 public articles. Dropping the two fields fixes this instance; dropping the carry-forward removes the class, so the next field that should not be public has no route to get there.
   - No provenance is lost. The digest carries `ai_usage` and the AI-operation ledger ([0037](../decisions/0037-ai-operation-ledger.md)) is its durable home once built. Both are dev-layer. Removing the copy in the most-exposed layer removes a duplicate, not a record.
   - No consumer breaks, as established above.
   - It matches the 2026-06-29 position: usage data kept, not publicly surfaced, with any future surfacing expected in the internal workbench rather than the public site.

   **Sequenced behind the generator stamp specifically - not behind the whole audit binding.** Corrected 2026-07-23, having measured rather than reasoned:

   - *Re-derivation is one hop, not a walk.* An earlier version of this note claimed recovering an article's usage meant traversing `built_from` to the brief, then the graph slice, then the claims, then their digests. It does not: `built_from` already carries claim ids **and hashes inline**, so the walk is article -> claims -> `digest.ai_usage`, and the assembler performs exactly that walk today to build the chain in the first place. The brief is not involved. What enables re-derivation is therefore the **claims list**, which brief mode already emits.
   - *The real blocker is the model record.* `model` and `model_version` reach an article **only** through `ai_usage`. Removing it before `built_by` exists would destroy the record of what produced every article - a direct [0010](../decisions/0010-auditable-assembly.md) reconstructability failure. Cost had to go; the model identity must not go with it.

   So the order is: **`built_by` lands, then `ai_usage` is removed.** It is *not* gated on node-mode graph-slice identity, which is a larger and separate problem - blocking the removal on it would hold a leak path open for the sake of an unrelated design question.

   The `metadata` sub-shape and node identity/slug halves of this question remain open.
