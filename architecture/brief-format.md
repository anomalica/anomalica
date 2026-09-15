# Brief format

The brief is the interchange between the synthesiser (producer) and the assembler/writer (consumer), schema `anomalica/brief/2`. It holds exactly the graph slice that feeds ONE page - language-neutral, before any prose - and is the writer's sole input (see [decision 0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)). Like the digest format (0027), it is a versioned interchange spec: breaking changes bump the integer.

The canonical machine-readable field list is [`reference/format-specs.yaml`](../reference/format-specs.yaml) (`types.brief`); this document is its narrative companion.

The field set below is live, grounded against the synthesiser's first-cut brief. Two parts of the intended shape are deferred and marked as such ([Intended but deferred](#intended-but-deferred)) - documented now, built when their gate lands.

## Shape

A YAML document (`.yaml`) - the same serialisation as the digest interchange (0027), not markdown with frontmatter. Top-level keys carry the page identity, the selection and payload hashes, the generated stamp, and the related-node candidates; a `claims` list carries the ordered, selected claims with their provenance. Language-neutral throughout - facts, not prose; one brief feeds all N language articles for its page. The fields below are the locked `anomalica/brief/2` contract; YAML is the serialisation.

## Where a brief lives

`<briefs>/<section>/<slug>.yaml`, where `<section>` is `section_for(page.node_type)` from anomalica-common (`people`, `organisations`, `projects`, `places`, `events`, `objects`, `documents`, `topics`, ...) - the same two halves as the page it feeds, `content/pages/<section>/<slug>.<lang>.md`. A page's identity is the pair, not the slug: the slug is disambiguated only within a node type, so an event and a project of one name (`Apollo 14`) share a slug and do not share a URL. A brief keyed on the slug alone gave those two pages one file, and the scheduler re-emitted whichever node did not own it on every pass (2026-09-02).

A brief **reference** - what a scheduler job or `assembler --brief` names - is therefore `<section>/<slug>`, which resolves as a direct path under either briefs directory. A consumer enumerates briefs with `*/*.yaml`; a file directly in the root is the pre-section layout and is pruned by the synthesiser, never read.

That reference, without `.yaml`, is also the brief artefact identity at the
`brief-selection` freshness boundary. A title, bare slug, node id or
`generated.graph_version` is not an interchangeable identity.

The two directories (internal `~/.local/share/assimilator/briefs`, published `content/briefs`) hold the same layout; `data-model.md` records why they are not copies of each other.

## `page.nodes` (the covered nodes)

A page covers one or more graph nodes. `page.nodes` is the ordered list of them, each `{node_id, name, node_type}`. It is always present and always a list; for an ordinary page it holds one entry. There is no `page.node_id` - a page-level primary sitting beside a member list would be two answers to one question, free to drift, and the drift is silent in exactly the checks that exist to catch silent failures.

Most pages cover one node. A composed page covers several deliberately. The first is the pair of topics for unidentified objects: they hold 961 and 1,133 claims but share only 26, while 24 of their 72 source records feed both - so the split is by which word a source happened to use, not by subject. Composing the page unions the claims while the nodes stay separate, which is what preserves the word each source chose. (Mark, 2026-09-03.)

**A consumer that acts on a covered node must act on every member, not on the first.** Four passes look a node up from the brief today: the assembler's retirement sweep and its veto sweep, the publication staleness map, and the assimilator's consistency check. Each asks "which node is this page about?" and takes one answer. Given a page over two nodes, a member that is retired by a merge, or vetoed by a reviewer, must take the page down or hold it back the same as a sole node would; a pass that reads only the first member leaves the page standing and keeps publishing the second member's claims, reporting nothing. That is the failure the list shape exists to prevent, so a consumer iterates.

`page.node_type` and `page.slug` stay page-level. They are the page's own identity - its section under `section_for()` and its URL - not a member's, and for a single-node page they match the member's. `page.title` is likewise the page's own name and is never lifted from a member, so adding or removing a member cannot silently rename a page or move its URL.

### The bump from `anomalica/brief/1`

`page.nodes` replaces `page.node_id`; nothing else changed. Briefs are derived data, rebuilt deterministically by the synthesiser (806 of them, in both the internal and the published directory), so `/1` is not migrated and no consumer reads both: the synthesiser emits `/2`, every brief is regenerated in one pass, and the consumers above move to the list in the same change. A compatibility period would be the wrong shape here - it buys nothing that a regeneration does not, and leaves the singular reading alive to be copied into the next consumer.

## Top-level fields

The top-level fields - `schema`, `brief_hash`, `payload_hash`, `page` (`kind`, `title`, `slug`, `node_type`, `nodes`), `generated`, `related_nodes` - are listed with their descriptions in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.brief`. This document does not repeat them; the narrative below covers what a field list cannot (slug resolution and the two hashes' distinct audit roles).

`page.slug` and `related_nodes[].slug` are resolved by the synthesiser at emission via the canonical slugifier (`metadata.explicit_slug` if present, else the shared anomalica-common slugifier - first-last for persons, with deterministic disambiguation; see [node slugs](node-types.md#node-slugs)). They are pre-resolved into the brief because the assembler is writer-only and does not read node metadata; an unresolved slug would silently break pattern-slug URLs and their cross-links.

For a person page, optional `page.listing` carries the raw public-list ordering inputs:
`work_count`, `subject_claim_count` and `claim_count`. `work_count` is the
page-gate's historical `source_count` renamed at this boundary because it counts
distinct `COALESCE(records.work_id, record_id)` works, not source URLs or
provenance roots. `subject_claim_count` is the deterministic count of claims
whose text is about the person; `claim_count` is the distinct speaker-or-reference
claim union. The synthesiser copies these measurements from the page proposal.
The site reads the current published brief directly; the assembler does not copy
the block into content. They remain separate raw integers and are never
collapsed into a score. `page.listing` is display-only and excluded from
`brief_hash`; a frequency change reorders the index without claiming the
article's prose input changed.

This is an additive transition within brief/2: readers accept its absence, while
newly generated publishable person briefs include it. All three values are
non-negative integers; a missing, non-integer or negative value makes the whole
listing block unavailable rather than partially ranking it. Brief publication
refreshes this block from the current page-proposal row even when the prose claim
selection is unchanged; because the block is excluded from `brief_hash`, that
refresh does not make the article body stale.

## `size` and `truncated`

`size.tokens_estimated` is how much of the consuming stage's context window the brief's claim material occupies **as a consumer renders it**: each claim's `content` and `original_excerpt` at 2.7 characters per token, plus a flat line of framing per claim (attribution, date, record). It is not the size of the YAML file, which carries roughly four characters of ids, hashes, slugs and provenance for every character of claim text, none of which reaches a model: the largest brief is 3.6 MB on disk and renders to about 286,000 tokens. `size.sized_against` is the smallest context window among the models the consuming stage may use (from `model-policy.yaml`), so the brief fits whichever the scheduler picks. The estimate errs high; the binding check is the consumer's, made on the prompt it actually builds.

`truncated` is **absent** when the brief carries every claim the node holds, so its presence is the signal. When present it gives `kept`, `available`, and `why`, which names the constraint that bound - the token budget, or the per-event source cap - because the two call for different responses: one for a larger model, the other for nothing.

## `entailment` (per claim, and per page)

The digester checks each claim against its own excerpt: does the excerpt (premise) entail the claim text (hypothesis)? A claim that was assessed carries `entailment: {label, score, model, premise}` - `label` is `entails`, `neutral` or `contradicts`, `score` the model's probability of that label, `model` the checker's id, and `premise` says which text produced the label: `quote` (the excerpt alone) or `window` (the record text around it, tried when the quote alone is neutral). An entails-by-window is the weaker verdict: the quote does not carry the claim on its own. The block is **absent** when the claim was not assessed (a digest that predates the check, or a claim with no excerpt); absence never means neutral, and `neutral` means not warranted even by the surrounding record. The page-level `entailment` block summarises the carried claims: `assessed`, `unassessed`, the three label counts, `entailed_by_quote` and `entailed_by_window` with their fractions over assessed (`null` when nothing was assessed). The entailed share is always split by premise, never one number.

Both are surfaced, not applied. The entailed fraction is the first component of the evidence score, whose definition is still open; until it is defined nothing selects, orders, hides or hedges a claim on this field, and a consumer should not either.

## `claims` (the selection)

An ordered list of claims - the selection, and the only facts the writer may use. Nothing outside it can enter the prose; this is what makes 0008 enforceable by construction. Order is the synthesiser's. Each claim's fields - `claim_id`, `claim_hash`, `content`, `original_excerpt`, `claim_type`, `attestation`, `speaker`, `node_refs`, `date`/`date_end`, `location_in_record`, `evidence`, `provenance` - are listed in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.brief` (`body.claims`). Note `provenance.content_hash` and `friendly_name`: they link each claim back to its source ingest.

## Identity and audit

`brief_hash` is SHA-256 of the UTF-8 bytes of this exact compact JSON object,
with keys in the shown order, no insignificant whitespace, JSON strings emitted
without ASCII escaping, and no trailing newline:

```json
{"kind":"entity","node_id":"n1,n2","claims":[["c1","h1"],["c2","h2"]]}
```

`kind` is `page.kind`. Despite its singular legacy name, `node_id` is the ordered
`page.nodes[].node_id` values joined by one comma; node ids cannot contain commas.
`claims` is the brief's ordered `[[claim_id, claim_hash], ...]` selection and is
not sorted. For the fixture above the hash is
`2657da2d00513b0d085f8d3a804078271047fd5e23dbce4c32719569d72c198f`.
The field names and serialisation are part of the hash contract: changing them
changes every brief even if its YAML shape does not change.

The member list is part of page identity: adding or removing a member changes
what the page should say, and a hash blind to it would leave every built page
looking fresh. This hash deliberately remains the stable identity of the
semantic claim selection and covered page members. It does not change merely
because writer context attached to those claims changes.

`payload_hash` binds the complete writer-relevant brief payload. It is SHA-256
of UTF-8 compact JSON with object keys sorted recursively, no insignificant
whitespace, non-ASCII unescaped and no trailing newline. The exact object is:

```json
{"claims":[],"page":{"kind":"entity","node_type":"event","nodes":[],"slug":"example","title":"Example"},"related_nodes":[]}
```

For that fixture the hash is
`12958f9bad6cc16d0a49bbf25fe628a2594ac0d0e1d189276ccb43a239f0f559`.

The values are copied from the brief without normalisation. `page` contains
exactly `kind`, `title`, `slug`, `node_type` and `nodes`; the other two values are
the complete ordered `claims` and `related_nodes` lists. List order remains
significant. Generated stamps, sizing, publication data and display-only
`page.listing` are excluded because they do not enter the writer payload and
have separate comparisons.

Both hashes are required. A current producer regenerates a legacy brief missing
`payload_hash`; a writer refuses to assemble from one. Their roles are distinct:

- `brief_hash` identifies and diagnoses the ordered semantic selection and page
  membership;
- `payload_hash` changes when any writer-visible page identity, claim context or
  related-node value changes, including provenance, attribution, entailment,
  attachment and node salience that intentionally do not alter `claim_hash`;
- the scheduler compares both, the assembler copies both into `built_from`, and
  together they provide 0010's precise, reconstructable knowledge-graph input
  identity.

A mismatch of the rebuilt payload is `payload_hash_mismatch` at
`brief-selection`. It does not describe digest input or graph import state; those
boundaries retain their own reason codes.

These are distinct from `generated.graph_version`, the coarse "knowledge-graph version used" stamp 0010 also records. `brief_hash` identifies the stable selection, `payload_hash` identifies the exact writer-visible values, and `graph_version` is the coarse graph-version stamp.

Freshness is proved by rerunning deterministic selection and comparing both
hashes. `generated.graph_version` may cheaply trigger that reconciliation, but a
matching timestamp cannot prove the selected slice or payload current and a
changed timestamp does not prove either changed. See
[end-to-end freshness](freshness.md#boundary-checks).

## Intended but deferred

Documented now so the full intended shape is on record; built when its gate lands.

- **Page-level evidence block** - `page.evidence { score, tier, independent_sources }`. The per-claim `evidence{}` is neutral in v1. When the [algorithmic-evidence-scoring draft](../decisions/drafts/algorithmic-evidence-scoring.md) is pinned, a page-level evidence block is added: the synthesiser's page-existence threshold reads it, and it is where the public score surfaces - until then, the provisional "scoring methodology in development" of [0035](../decisions/0035-first-public-artefact-proof-of-method.md) Phase 1. Shape documented here; built when scoring pins.
