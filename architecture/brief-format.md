# Brief format

The brief is the interchange between the synthesiser (producer) and the assembler/writer (consumer), schema `anomalica/brief/2`. It holds exactly the graph slice that feeds ONE page - language-neutral, before any prose - and is the writer's sole input (see [decision 0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)). Like the digest format (0027), it is a versioned interchange spec: breaking changes bump the integer.

The canonical machine-readable field list is [`reference/format-specs.yaml`](../reference/format-specs.yaml) (`types.brief`); this document is its narrative companion.

The field set below is live, grounded against the synthesiser's first-cut brief. Two parts of the intended shape are deferred and marked as such ([Intended but deferred](#intended-but-deferred)) - documented now, built when their gate lands.

## Shape

A YAML document (`.yaml`) - the same serialisation as the digest interchange (0027), not markdown with frontmatter. Top-level keys carry the page identity, the brief hash, the generated stamp, and the related-node candidates; a `claims` list carries the ordered, selected claims with their provenance. Language-neutral throughout - facts, not prose; one brief feeds all N language articles for its page. The fields below are the locked `anomalica/brief/2` contract; YAML is the serialisation.

## Where a brief lives

`<briefs>/<section>/<slug>.yaml`, where `<section>` is `section_for(page.node_type)` from anomalica-common (`people`, `organisations`, `projects`, `places`, `events`, `objects`, `documents`, `topics`, ...) - the same two halves as the page it feeds, `content/pages/<section>/<slug>.<lang>.md`. A page's identity is the pair, not the slug: the slug is disambiguated only within a node type, so an event and a project of one name (`Apollo 14`) share a slug and do not share a URL. A brief keyed on the slug alone gave those two pages one file, and the scheduler re-emitted whichever node did not own it on every pass (2026-09-02).

A brief **reference** - what a scheduler job or `assembler --brief` names - is therefore `<section>/<slug>`, which resolves as a direct path under either briefs directory. A consumer enumerates briefs with `*/*.yaml`; a file directly in the root is the pre-section layout and is pruned by the synthesiser, never read.

The two directories (internal `~/.local/share/assimilator/briefs`, published `content/briefs`) hold the same layout; `data-model.md` records why they are not copies of each other.

## `page.nodes` (the covered nodes)

A page covers one or more graph nodes. `page.nodes` is the ordered list of them, each `{node_id, name, node_type}`. It is always present and always a list; for an ordinary page it holds one entry. There is no `page.node_id` - a page-level primary sitting beside a member list would be two answers to one question, free to drift, and the drift is silent in exactly the checks that exist to catch silent failures.

Most pages cover one node. A composed page covers several deliberately. The first is the pair of topics for unidentified objects: they hold 961 and 1,133 claims but share only 26, while 24 of their 72 source records feed both - so the split is by which word a source happened to use, not by subject. Composing the page unions the claims while the nodes stay separate, which is what preserves the word each source chose. (Mark, 2026-09-03.)

**A consumer that acts on a covered node must act on every member, not on the first.** Four passes look a node up from the brief today: the assembler's retirement sweep and its veto sweep, the publication staleness map, and the assimilator's consistency check. Each asks "which node is this page about?" and takes one answer. Given a page over two nodes, a member that is retired by a merge, or vetoed by a reviewer, must take the page down or hold it back the same as a sole node would; a pass that reads only the first member leaves the page standing and keeps publishing the second member's claims, reporting nothing. That is the failure the list shape exists to prevent, so a consumer iterates.

`page.node_type` and `page.slug` stay page-level. They are the page's own identity - its section under `section_for()` and its URL - not a member's, and for a single-node page they match the member's. `page.title` is likewise the page's own name and is never lifted from a member, so adding or removing a member cannot silently rename a page or move its URL.

### The bump from `anomalica/brief/1`

`page.nodes` replaces `page.node_id`; nothing else changed. Briefs are derived data, rebuilt deterministically by the synthesiser (806 of them, in both the internal and the published directory), so `/1` is not migrated and no consumer reads both: the synthesiser emits `/2`, every brief is regenerated in one pass, and the consumers above move to the list in the same change. A compatibility period would be the wrong shape here - it buys nothing that a regeneration does not, and leaves the singular reading alive to be copied into the next consumer.

## Top-level fields

The top-level fields - `schema`, `brief_hash`, `page` (`kind`, `title`, `slug`, `node_type`, `nodes`), `generated`, `related_nodes` - are listed with their descriptions in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.brief`. This document does not repeat them; the narrative below covers what a field list cannot (slug resolution, the `brief_hash` audit role).

`page.slug` and `related_nodes[].slug` are resolved by the synthesiser at emission via the canonical slugifier (`metadata.explicit_slug` if present, else the shared anomalica-common slugifier - first-last for persons, with deterministic disambiguation; see [node slugs](node-types.md#node-slugs)). They are pre-resolved into the brief because the assembler is writer-only and does not read node metadata; an unresolved slug would silently break pattern-slug URLs and their cross-links.

## `size` and `truncated`

`size.tokens_estimated` is how much of the consuming stage's context window the brief's claim material occupies **as a consumer renders it**: each claim's `content` and `original_excerpt` at 2.7 characters per token, plus a flat line of framing per claim (attribution, date, record). It is not the size of the YAML file, which carries roughly four characters of ids, hashes, slugs and provenance for every character of claim text, none of which reaches a model: the largest brief is 3.6 MB on disk and renders to about 286,000 tokens. `size.sized_against` is the smallest context window among the models the consuming stage may use (from `model-policy.yaml`), so the brief fits whichever the scheduler picks. The estimate errs high; the binding check is the consumer's, made on the prompt it actually builds.

`truncated` is **absent** when the brief carries every claim the node holds, so its presence is the signal. When present it gives `kept`, `available`, and `why`, which names the constraint that bound - the token budget, or the per-event source cap - because the two call for different responses: one for a larger model, the other for nothing.

## `entailment` (per claim, and per page)

The digester checks each claim against its own excerpt: does the excerpt (premise) entail the claim text (hypothesis)? A claim that was assessed carries `entailment: {label, score, model, premise}` - `label` is `entails`, `neutral` or `contradicts`, `score` the model's probability of that label, `model` the checker's id, and `premise` says which text produced the label: `quote` (the excerpt alone) or `window` (the record text around it, tried when the quote alone is neutral). An entails-by-window is the weaker verdict: the quote does not carry the claim on its own. The block is **absent** when the claim was not assessed (a digest that predates the check, or a claim with no excerpt); absence never means neutral, and `neutral` means not warranted even by the surrounding record. The page-level `entailment` block summarises the carried claims: `assessed`, `unassessed`, the three label counts, `entailed_by_quote` and `entailed_by_window` with their fractions over assessed (`null` when nothing was assessed). The entailed share is always split by premise, never one number.

Both are surfaced, not applied. The entailed fraction is the first component of the evidence score, whose definition is still open; until it is defined nothing selects, orders, hides or hedges a claim on this field, and a consumer should not either.

## `claims` (the selection)

An ordered list of claims - the selection, and the only facts the writer may use. Nothing outside it can enter the prose; this is what makes 0008 enforceable by construction. Order is the synthesiser's. Each claim's fields - `claim_id`, `claim_hash`, `content`, `original_excerpt`, `claim_type`, `attestation`, `speaker`, `node_refs`, `date`/`date_end`, `location_in_record`, `evidence`, `provenance` - are listed in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.brief` (`body.claims`). Note `provenance.content_hash` and `friendly_name`: they link each claim back to its source ingest.

## Identity and audit

`brief_hash` = SHA-256 over the ordered `[(claim_id, claim_hash)]` plus the page identity, the covered node list included. The member list is part of the identity: adding or removing a member changes what the page should say, and a hash blind to it would leave every built page looking fresh. One fingerprint, three uses:

- the scheduler's staleness diff unit (the "Something changed?" step - reassemble a page only when its `brief_hash` changes);
- the assembler's freeze (`built_from`) - exactly what an article was built from;
- 0010's "knowledge-graph data" prompt-component audit hash - precise and reconstructable.

This is distinct from `generated.graph_version`, the coarse "knowledge-graph version used" stamp 0010 also records. Both are present in v1 and play distinct roles: `brief_hash` is the precise, per-page, reconstructable hash; `graph_version` is the coarse graph-version stamp. Together they satisfy 0010's audit requirement.

## Intended but deferred

Documented now so the full intended shape is on record; built when its gate lands.

- **Page-level evidence block** - `page.evidence { score, tier, independent_sources }`. The per-claim `evidence{}` is neutral in v1. When the [algorithmic-evidence-scoring draft](../decisions/drafts/algorithmic-evidence-scoring.md) is pinned, a page-level evidence block is added: the synthesiser's page-existence threshold reads it, and it is where the public score surfaces - until then, the provisional "scoring methodology in development" of [0035](../decisions/0035-first-public-artefact-proof-of-method.md) Phase 1. Shape documented here; built when scoring pins.
