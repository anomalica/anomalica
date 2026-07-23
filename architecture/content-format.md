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
  tokens: {input, output}    # this assembly's own usage
```

`tokens` is here because **the article is the only artefact of the assemble stage**. Every other stage's usage has a second home - a record's or a digest's own `ai_usage` - so removing the carried-forward copy from an article loses nothing. The assemble entry has no such original: the AI-operation ledger is meant to be it, and the ledger is not written (0037 is scaffolded, and its own text names the gap: "assembler discards usage today"). Dropping `ai_usage` without this line would destroy each article's assembly token counts at the moment of writing, which is the opposite of the 2026-06-29 position that usage data is *kept* and merely not surfaced.

This does not reopen what the `ai_usage` removal closed. That removal targets **carry-forward** - upstream entries republished into a public artefact, which is how a forbidden cost field reached 53 articles. The assemble stage's own tokens are first-party data about this artefact, not a copy of someone else's. Cost, price, and currency fields remain forbidden here as everywhere: tokens are a measurement, and any figure is derived by the consumer at display.

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

The transport must be stamped because the two paths do not currently send the same prompt: the subscription path passes a system prompt via `--append-system-prompt`, while the API path sends the user prompt with no system prompt at all.

**The invariant: both transports send the byte-identical system prompt.** `<COMPONENT>_USE_API` selects a *billing* path, so nothing about how an article is written may vary across it.

Identical rather than merely equivalent, and the distinction is the point. A clause that is a no-op on one path - tool suppression, which compensates for the agentic wrapper on the subscription path and does nothing where no tools are passed - is sent on both anyway rather than trimmed. Trimming it would make `system_prompt_sha256` differ, splitting the corpus into two generator identities over a clause that changes no output, which is precisely the confound the component hashes exist to eliminate. One string, one hash, one identity.

Today's instance is benign, and saying so precisely matters more than making the case sound worse than it is: the subscription system prompt carries no editorial or content guidance, only an output-format corrective the user prompt already duplicates in its own words, plus that tool clause. The reason to close it anyway is that **an unstated difference between transports is a latent defect even when today's instance is harmless** - nothing asserts the equivalence, so a later edit could introduce real content guidance on one path alone and nothing would catch it. `transport` and `system_prompt_sha256` are what make that detectable rather than silent.

**Machine ownership needs no new machinery.** The assembler rewrites the whole file on every re-assembly and preserves only an enumerated allow-list (`_PRESERVE_KEYS`, currently just `directives`). Keeping these two keys out of that list makes machine ownership the default: a human edit inside them is discarded on the next assembly. The rule is stated here for humans, not built.

Coverage is partial and the gap is uneven. Brief mode already emits `built_from`; record mode binds by `record_hash`; **node mode, the majority of the corpus, carries no binding at all**.

Node mode needs no binding designed for it, and building one would be a mistake. It is the interim direct-graph-read path that [0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md) supersedes: the assembler is to be "given the brief and nothing else - it does not read the graph", and the brief's input hash *is* 0010's knowledge-graph-data audit hash, "not a parallel scheme". A database-direct binding for node mode would be exactly that parallel scheme, built on a path already scheduled for removal. The unbound articles close by re-assembly from briefs - gaining `brief_hash` like those that already carry it - or by the synthesiser judging the page should not exist. Nothing to design, and nothing for the assimilator to expose.

**Compare claims on the hash, never on the id.** Claim ids are minted fresh (`uuid.uuid4()`) on every digest emission - two digests of the same unchanged record share no claim ids at all. So an id comparison is broken in both directions: it detects nothing when a claim's text changes, and it reports a change on every re-digest when nothing changed. The `id` in `built_from.claims` is a locator for humans; the `hash` is the identity.

Record mode's per-claim hash is **computed, not stored**. Digest claims carry no hash field, and none should be added: `anomalica_common.digest.fingerprint_of_claim(claim)` derives one from fields the emitted claim already has, taking the claim dict exactly as the digest YAML serves it. That shared function single-sources the field *mapping* as well as the hash - a digest names these fields `text`/`type`/`quote`/`location` while the graph names them `content`/`claim_type`/`original_excerpt`/`location_in_record` - so assembler, workbench, and digester hold one definition of "the same claim" rather than three hand-rolled ones.

Storing it instead would recreate the failure this format spent 2026-07-23 removing. A fingerprint is a *derived* value exactly as a notional cost is: if the definition ever changes, every stored copy is silently wrong. A stale hash is worse than a stale price, because it surfaces as a mismatch nobody can explain rather than a number that looks odd. If a non-Python consumer ever needs the fingerprint, revisit it then with the staleness question answered, rather than pre-emptively.

## Open questions

These block ratification of this format:

1. **On-disk layout.** Flat with a language suffix (`pages/<section>/<slug>.<lang>.md`, per [assembler.md](assembler.md)) versus document-first directories (`<slug>/index.{lang}.md`, per [content-lifecycle.md](content-lifecycle.md)). The two current docs disagree; assembler.md flags its own layout section as out of date. Unratified.
2. ~~**Audit binding location.**~~ **Settled 2026-07-23** - two machine-owned frontmatter keys, `built_from` and `built_by`. See [Auditable assembly](#auditable-assembly) above. What remains is implementation: none of 0010's audit trail was computed before this date (`hashlib` was not imported in the assembler). The unbound node-mode articles are not a design problem - see the note above on why 0036 retires that path rather than requiring a binding for it.
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

   **Strip `ai_usage` only from an article that is gaining `built_from` *or* `record_hash` in the same write.** The two stamps preserve different halves of what the carried-forward list held. `built_by` preserves the *assembly* model; the binding preserves the route to the *upstream* models, since an article's usage entries are recovered by walking back to the digests behind it. Either binding provides that route: `built_from.claims` by a claims walk, and `record_hash` more directly still, because a record page has exactly one source record. Record pages carry `record_hash` and deliberately never carry `built_from`, so a condition naming only the latter would strand them holding `ai_usage` for ever.

   Node mode has neither, and keeps `ai_usage`. Such an article would otherwise retain its assembly model but lose any way to reach the models that produced its claims - and that is the majority of the corpus today. Those pages keep the block until they re-assemble from a brief, at which point they gain both stamps and lose it in the same write.

   The `metadata` sub-shape and node identity/slug halves of this question remain open.
