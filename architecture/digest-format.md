# Digest interchange format

The output of the digester for each record is a single YAML file at
`digests/{friendly-name}.yaml`. This file is the canonical
intermediate between the artificial-intelligence extraction step and every
downstream consumer (the SQLite database, the workbench, the assembler).
Today the relationship is 1:1 (one model, one digest). A planned direction
makes it 1:N - several models per ingest, reconciled into this single
canonical digest - see [Planned: multi-model digestion](#planned-multi-model-digestion-and-canonical-reconciliation)
and [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md).

The companion document on the ingester side is
[`ingest-format.md`](ingest-format.md). This document covers the digester
side.

The canonical machine-readable field list is [`reference/format-specs.yaml`](../reference/format-specs.yaml) (`types.digest`); this document is its narrative companion.

## Schema identifier

Every digest carries `schema: anomalica/digest/1` at the top. A future
breaking change to the format bumps the integer (`anomalica/digest/2`).
Consumers should check the schema and refuse anything they do not
understand.

## File layout in the repository

```
digests/
  2020-04-27-web-statement-by-the-department-of-defense-on-the-release-of.yaml
  2024-08-19-ebook-imminent-inside-the-pentagon-s-hunt-for-ufos.yaml
  ...
  variants/
```

One YAML file per record. Filenames mirror the friendly filenames in
`ingests/by-name/` (same `{date}-{format}-{slug}` form), with
`.md` swapped for `.yaml`. This pairing is how the workbench joins the
two sides for any given record.

## Document structure

The order of top-level keys is fixed: `schema`, `extracted_at`, `model`,
`ai_usage`, `prompts`, `pre_digest`, `curation`, `record`, `terminology`,
`nodes`, `domain_claims`, `infrastructure_claims`. Null and empty values are
omitted - if a record has no infrastructure claims, the key is absent rather
than present with `[]`. `ai_usage`, `prompts`, `pre_digest`, `curation`, and
`terminology` are optional blocks (see below).

```yaml
schema: anomalica/digest/1
extracted_at: '2026-05-19T11:38:07.350885+00:00'
model: sonnet
record:
  id: 15a0aeac-f65e-4408-8356-18eb8fd2b6fe
  title: 'Imminent: Inside the Pentagon''s Hunt for UFOs'
  producer: Elizondo, Luis
  date: '2024'
  reference: null
  copyright_status: licensed

### `copyright_status`

Flattened from the ingest record's nested `copyright.status`. The digest carries
the STATUS ONLY, never the whole copyright block, so nothing else in it is
republished. Values are those of the ingest record: `public_domain`,
`open_licence`, `publicly_accessible`, `licensed`, `restricted`.

**Absent means UNKNOWN, and a consumer must treat unknown as NOT DISTRIBUTABLE.**
Every digest produced before 2026-08-28 lacks the field, so absence is common and
says nothing about the source's licence. A consumer that reads absent as
permitted would treat the entire pre-existing corpus as freely publishable.

It is carried because a field that must be JOINED is a field that gets forgotten.
The status was previously held only in the ingest record, on the reasoning that
access-control state should have exactly one authoritative home - which is correct
in principle and produced a near-miss in practice: with the graph unable to see
copyright, verbatim excerpts from 13 copyrighted books reached 85% of proposed
pages before anyone noticed.

**It is a snapshot, not an authority.** Copyright status lives in record
frontmatter, and frontmatter changes are invisible to `pre_digest.sha256`, which
covers the body. A licence that changes after digestion leaves every digest
asserting the old status with no staleness check able to detect it. A consumer
FILTERING or PROPOSING may use the carried value; a consumer making a PUBLISH
decision should resolve the record by `content_hash` and read the store.

nodes:
  - id: dea95da2-a779-4012-88d5-d443d7f8f4b3
    type: person
    name: Elizondo, Luis

  - id: 5bf24c7d-5a04-4749-a52c-444de447d97c
    type: organisation
    name: Department of Defense

domain_claims:
  - id: 3978ae84-28e8-4bcb-a7b5-59cae50d0041
    type: administrative
    attestation: first_hand
    speaker:
      id: dea95da2-a779-4012-88d5-d443d7f8f4b3
      name: Elizondo, Luis
    provenance_chain:
      origin_kind: speaker
      origin: Elizondo, Luis
      relay: []
    location: 00:04:12.0-00:04:25.5
    date: '2017'
    refs:
      - id: dea95da2-a779-4012-88d5-d443d7f8f4b3
        name: Elizondo, Luis
      - id: 5bf24c7d-5a04-4749-a52c-444de447d97c
        name: Department of Defense
    quote: |-
      Verbatim text from the source goes here
    text: |-
      The canonical claim text as extracted.

infrastructure_claims: []
```

### `provenance_chain`

Required on every claim ([0044](../decisions/0044-claim-provenance-chain-is-required.md)). It records who
originally asserted the claim and how it reached the speaker, and it is what the
corroboration model keys on when deciding whether two claims are genuinely
independent - repetitions of one anonymous email share a root and must not
present as independent attestations. `origin_kind` is one of `speaker`, `named`,
`anonymous`, `document`, `unattributed`; `relay` is the ordered path from origin
to speaker, empty when the speaker is the origin. `attestation` is derived from
its depth. An `anonymous` origin can never be a node, so this field is the only
place it survives. See [data-model.md](data-model.md#provenance-chains).

Distinct from the record's `provenance` block
([0043](../decisions/0043-canonical-provenance-block.md)), which is source-origin
metadata about the document rather than the assertion chain inside it.

### `location`

The span of the source the claim was drawn from. **Always derived by realigning
the claim's verbatim `quote` against the record, never taken from the model.**
This was already the rule for timestamped records; it applies to every type.

The reason is **axis consistency and frame definiteness**, not model imprecision.
A model left to write `location` itself picks a different axis per chunk -
timecodes, bare seconds, source line numbers, `Foreword, paragraph 4` - which
makes variants from different models impossible to cluster against one another.
Deriving it makes the axis uniform and the span exact by construction, whatever
the model's own error rate happens to be.

Measured across the corpus 2026-07-31, that error rate is **small**: 2,402
resolvable claims, median absolute drift of **1 character**, flat across document
position, with the digester independently measuring span length at a median 0.95
of quote length. An earlier figure of 149 characters was drift conditioned on
claims that had already failed a containment test - a property of the failing
subset reported as a property of the population. The pointers are essentially
correct, and the residual is a units-frame mismatch rather than accumulating
error.

Deriving is still right, and none of the argument rested on the magnitude: it
removes the axis variance above, it makes drift structurally impossible rather
than merely small, and it fixes the frame problem below by definition. It is also
why a prose location is not a validation failure to be forbidden - the model's
rough guess is a useful *input* for disambiguating which occurrence of a short
quote is meant, and is simply never the stored value. What is constrained is what
gets written, not what the model may say.

#### A span must declare its frame

**Spans are expressed in the materialised pre-digest**, not the raw record body.
The two differ - the pre-digest is whitespace-collapsed and annotation-stripped -
so an offset is uninterpretable without knowing which space it counts in, and a
consumer resolving it against the wrong one lands slightly and consistently off.
That mismatch, not model error, produced the residual above and most of the wrong
numbers found across four components on 2026-07-31.

This needs no new field: the digest's [`pre_digest`](#pre_digest) block already
carries `{sha256, prep_version}`, which names the exact text the offsets index.
What was missing is the declaration that offsets are relative to it. A digest
carrying no `pre_digest` block has **no recoverable frame**, and its spans cannot
be resolved with confidence at all - one more thing re-digestion fixes and
back-stamping cannot.

The stored form is a resolvable span, in the most **re-extraction-stable** axis
the record supports:

| Record | Form | Survives |
|---|---|---|
| Timed media | `HH:MM:SS.d-HH:MM:SS.d` | Re-transcription - anchored to the audio |
| Chaptered work | `ch N:START-END` | Re-pagination and prep changes |
| Everything else | `char:START-END` | Least stable; regenerate on re-digest |

Prefer the highest row the record supports. Global character offsets are the
fallback precisely because they die at the next `prep_version` bump, and a
location is only as durable as the anchor beneath it.

An elided `quote` aligns fragment by fragment - the elision rules already require
each fragment to be individually locatable, so the span runs from the first
fragment's start to the last one's end, and a fragment that will not locate is a
broken quote rather than a location problem.

A claim whose quote cannot be aligned gets **no** `location` rather than a
guessed one. Absence means unresolvable, and it must not be filled with the
model's estimate to avoid an empty field.

### `record`

The five fields describing the source record this digest was produced
from. `id` is the universally unique identifier assigned to the record
node in the knowledge graph and is the join key against
`ingests`. `producer` is in `Last, First Middle` form for
persons ([person naming](node-types.md#person)) or a plain
organisation name. `date` is a string in the form `YYYY` or `YYYY-MM-DD`.
`reference` is an external identifier where one exists (book ISBN,
report number, archive identifier) and is often null.

### `ai_usage`

Optional. What each stage consumed, carried forward onto the digest. **The
contract is two shapes, not one**, switched on the presence of `duration_s`:

```yaml
ai_usage:
  - stage: digest            # AI stage: tokens, no wall-time
    model: claude-opus-4-8
    model_version: claude-opus-4-8   # optional; alias resolved to a versioned id
    tokens:
      input: 208331
      output: 39436
    route: cli               # cli | api | openrouter | opencode; `mixed` if a run crossed routes
    effort: low              # CLI route only: the resolved ANOMALICA_CLI_EFFORT (low | medium | high | xhigh | max)
  - stage: transcribe        # LOCAL (gpu/cpu) stage: wall-time, no tokens
    model: whisperx-large-v3
    duration_s: 412.7
```

`tokens` is **nested**, and that is canonical - it is what every emitter
writes and what carried-forward entries hold. `tokens.input` is the *total*
the model read, input plus cache read plus cache creation, so a consumer
deriving a figure accounts for prompt caching, which dominates the count.

Local stages (`transcribe`, `diarise`, `embed`) carry no tokens: there is no
model-token billing on the local paths, so the entry records the local model
and wall-time only. A consumer must not assume tokens are present - reading
`tokens` unconditionally breaks on every local stage.

**Provenance only - model, version, and token counts. No cost, price, or
currency field appears here, in any other artefact, or in
[format-specs.yaml](../reference/format-specs.yaml).** A consumer that wants
to show a notional cost derives it from the token counts against published
list prices at the point of display. This is the canonical rule for AI usage
across the project, and it holds for the record's `ai_usage`, an article's,
and the AI-operation ledger alike.

The reason is that a stored dollar figure bakes in a price that changes,
turning an interchange artefact into a billing one, and it puts a
cost-shaped field into repositories that are read far more widely than the
dev layer. Nothing is lost by deriving: `extracted_at` already dates the
run, so which price era applied stays recoverable without a stored basis.

The closed contract is therefore `stage`, `model`, `model_version?`,
`tokens{input, output}`, `route?`, `effort?` for AI stages and `stage`,
`model`, `duration_s` for local ones. `route` and `effort` say how the
tokens were spent: every extraction before 2026-09-02 ran on the
subscription CLI at effort `low` without the artefact recording it, and
those entries are stamped `effort: low` retrospectively (except the
effort-medium variants of 2026-09-02); an entry without `effort` on the
CLI route is one the stamping did not reach. A producer builds an entry explicitly from those fields
rather than forwarding an SDK usage object minus a few keys: an
unspecified block accepts anything, which is exactly how a cost field
crept in, and a closed list means the next SDK field cannot drift into an
interchange artefact.

An allow-list applied to the wrong shape is destructive, not merely
untidy. A list built for AI stages, applied to a local entry, strips it to
bare `stage` + `model` and silently discards the only measurement it had.
Switch on `duration_s` before conforming anything.

Amended 2026-07-23: emitted digests previously carried `notional_cost_usd`
and `price_basis` in violation of this rule (59 digests, alongside 53
assembled articles). Both fields are dropped at the producer. No bulk
rewrite - the fields clear as records re-digest and articles re-assemble,
which happens anyway, so old artefacts may still carry them. See
[0037](../decisions/0037-ai-operation-ledger.md), amended.

### `review_state`

The source record's review state **at extraction time**. Provenance, alongside `prompts`, `pre_digest` and `ai_usage` - it records the conditions an extraction ran under, and nothing more.

```yaml
review_state:
  reviewed: false           # true | false - was the source reviewed when this ran
  coverage: 0.0             # fraction of sections observed at that moment
  checked_at: '2026-08-22T04:11:07Z'
```

**Never resolve current review state from this field.** The ingest's review sidecar is the single source of truth; anything that gates behaviour - the assimilator's page gate, the assembler, review-priority ranking - reads the *current* state from the record at import or rebuild. A snapshot used as authority would freeze a record's status at the moment it was digested, so a review would not take effect until re-digestion, which is the opposite of what the field is for ([0046](../decisions/0046-format-conditional-review-gate.md)).

**Absent means not recorded, never unreviewed.** Digests written before this field existed carry no review state at all, and reading their absence as `reviewed: false` would assert something about extractions that were never measured. Three states, all distinguishable: present-and-false, present-and-true, absent.

`coverage` is a fraction rather than a flag because review is measured per section, so a record is reviewed in parts. A digest that ran at 0.4 coverage is a different provenance fact from one that ran at 0.0.

### `prompts`

Optional. Which prompt produced each extraction pass, so a digest is
attributable to an exact prompt - the extraction-side counterpart to the
assembler's auditable assembly ([decision 0010](../decisions/0010-auditable-assembly.md)).
A list with one entry per pass, each recording the prompt `id`, `version`,
content `sha256`, and source `file`:

```yaml
prompts:
  - pass: nodes
    id: nodes
    version: v2
    sha256: a155b450f8e6dfb1...
    file: nodes.txt
  - pass: claims
    id: claims
    version: v2
    sha256: 579539bac029333c...
    file: claims.txt
```

The prompts are versioned files in the digester repo
(`workspace/digester/prompts/`, registered in `registry.yaml`); the `sha256`
pins exact content. A per-run `DIGESTER_NODES_PROMPT_FILE` /
`DIGESTER_CLAIMS_PROMPT_FILE` override is recorded as `version: override` with
the override file's own hash - never silently. Absent on digests produced before
prompt-provenance stamping; those can be attributed by `extracted_at` against
the registry's per-version `added` dates.

**Digests without `prompts` or `pre_digest` have unrecoverable provenance.** The 23 canonical digests written before these blocks landed record neither a prompt sha nor a `prep_version`, and neither is derivable from the artefact - `extracted_at` narrows the prompt to a registry era, not to a version. Such a digest cannot be attributed, reproduced, or compared against another model's output, which makes it unusable as an eval baseline.

The resolution is re-digestion rather than back-stamping, because a guessed provenance stamp is worse than an absent one. Recorded here because it changes what a corpus-wide run *is*: a run that re-digests those 23 alongside new records **replaces** the canonical corpus rather than extending it, yielding one generation at one model, one prompt sha, and one prep version. That uniformity is the point - a corpus of mixed, partly-unknown generations cannot support the model and prompt comparisons the eval depends on.

### `curation`

Optional. Present only when a human changed a value in this digest after
extraction. Absent means the file is model output as emitted.

```yaml
curation:
  - at: '2026-08-21T14:40:00+00:00'
    by: Mark
    changed: [nodes]
    why: >-
      Anonymous person nodes rewritten to the bracketed description form
      (ingest-format.md). Three names; no re-extraction.
```

**Without it, a hand-edited digest is indistinguishable from model output**, and
the file goes on asserting that a named model on a named prompt version produced
a value a person wrote. Nothing downstream can catch it: an edit to `nodes`
leaves the body untouched, so `pre_digest.sha256` still matches and the
staleness check stays silent - correctly, because the *source* did not change.
The one check that would notice a digest diverging from its extraction is
exactly the one that cannot fire.

The cost of the gap is not hypothetical or cosmetic. The whole model-comparison
method rests on a digest being what a model emitted - a single 27-model
comparison run over one record is worthless if edited and unedited artefacts mix
silently, and no reader of the corpus could separate them afterwards. A digest
carrying `curation` is still usable for everything except being cited as that
model's unmodified output, which is precisely the distinction that has to
survive.

**A commit message is not a substitute.** Git history is a different artefact
from the file, and every consumer that reads a digest without its repository -
an eval harness, a copied corpus, a downstream import - sees only the file. The
provenance has to travel with the data.

**Prefer re-extraction where it is affordable.** Curation records an edit
honestly; it does not make the edit as good as a clean run. Where a rule changed
and the budget allows, re-digest instead and leave the block absent.

### `pre_digest`

Optional. The content hash of the **pre-digest** - the ingest after all
deterministic model-prep (irrelevant regions removed, footnotes inlined,
word-timestamps stripped), which is exactly the text the model extracted from
([decision 0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)).

```yaml
pre_digest:
  sha256: 1c0d2ba0347d3592...
  prep_version: 1
```

Together with `prompts` and `model` this makes a digest exactly reproducible:
`(pre-digest hash + prompt version + model)`. `prep_version` names the version of
the deterministic prep that produced the pre-digest. The materialised pre-digest
artefact is stored content-addressed and served for inspection by the workbench's
pre-digest tab; its store layout is in
[ingest-format.md](ingest-format.md). Absent on digests produced before the
pre-digest stage.

### `nodes`

A list of every node mentioned by any claim. Field order per item:
`id`, `type`, `name`, optionally `metadata`. The `id` is a
freshly-minted universally unique identifier per node per digest. The
same real-world person may appear with different ids across digests;
the deterministic import step resolves duplicates via name and alias
matching.

`type` is one of the eight domain node types defined in
[`node-types.md`](node-types.md): `person`, `organisation`, `project`,
`place`, `event`, `object`, `document`, `topic`.

`metadata` is an optional mapping for type-specific extra data
(sentiment markers on organisations, date ranges on documents, role
labels). The schema does not constrain its keys.

### Claims

`domain_claims` and `infrastructure_claims` are two parallel lists with
identical item shapes. The list a claim is in is its category
(`ClaimCategory`: `domain` | `infrastructure`). They are kept separate
because the two extraction passes run independently and, on import, the
assimilator routes each category to its own database - `domain_claims`
to `knowledge.db`, `infrastructure_claims` to `infrastructure.db` (see
[graph-schema.md](graph-schema.md)).

Field order per claim: `id`, `type`, `attestation`, `speaker?`,
`location?`, `date?` or `date_range?`, `refs?`, `quote?`, `text`,
`entailment?`.

`type` is one of the six claim types defined in `node-types.md`:
`observation`, `testimony`, `hearsay`, `opinion`, `measurement`,
`administrative`.

`attestation` is `first_hand`, `second_hand`, or `third_hand`.

`speaker` and each entry in `refs` are objects with both `id` and
`name`. The id makes the digest robust to node renames - the importer
uses it as the canonical join key. The name is included so a human
reading the file can verify each reference without looking up
identifiers. Workbench and other machine consumers join on id and
ignore the name.

`location` is a free-form string indicating where in the source record
the claim was extracted from. Today this is human-readable
(`paragraph 1`, `chapter 23, p. 412`). It may later contain character
offsets to support exact source-to-claim highlighting in the workbench.
The schema does not constrain the format; consumers parse it
opportunistically.

`date` and `date_range` are mutually exclusive. Use `date` for a single
date (`2017`, `2004-11-14`) and `date_range` as a two-element list
(`['2007', '2012']`) when the claim refers to a temporal interval.
Both elements of `date_range` are strings.

`quote` is the verbatim text excerpted from the source record. `text`
is the canonical claim as extracted - usually a tightened or
paraphrased version of `quote`. Both use YAML block scalars (`|-`) so
multi-line content needs no escaping.

A `quote` may be **elided**. An atomic claim distilled from verbose
speech legitimately spans non-contiguous stretches of the source, and
stitching those stretches is preferable to the alternatives - a bloated
quote that carries the filler, or a paraphrase that loses the verbatim
anchor. Elision is governed by four rules:

- **Every fragment is verbatim.** Each stretch between join markers
  appears character-for-character in the source record.
- **Every fragment independently locates.** The re-aligner (see
  `location`) must place each fragment against the source. A fragment
  that does not locate is a *broken* quote - the one fidelity failure -
  and the grader rejects it. Verbatim-but-non-contiguous is *elided*,
  not broken, and passes.
- **Fragments keep source order.** They appear in the quote in the same
  order they occur in the source; the re-aligner's located positions run
  non-decreasing across them. This is what stops an elision from
  reordering or recomposing what the speaker said - a reordered elision
  is a fidelity failure even when every fragment locates.
- **`...` marks each join** and is the only text permitted between
  fragments. It carries no meaning of its own: the re-aligner ignores it
  and matches the verbatim fragments on either side, and a consumer
  detects an elided quote by its presence.

These four are mechanical and checkable. They are necessary, not
sufficient: an elision that drops a negation, condition, or attributive
qualifier can invert the sense of the retained fragments while each one
stays verbatim, located, and ordered. Meaning-preservation across a join
is therefore an authoring obligation that the grader and human review
enforce, not something the re-aligner can guarantee. The eval's
`contiguous` / `elided` / `broken` split follows directly: contiguous and
elided both pass fidelity, only broken fails.

`text` is the only required content field. A claim with neither a
`quote` nor a `text` is malformed.

### `entailment`

Does the source warrant the claim as written? Written by the digester's
last extraction step and by `digester check` on older digests; a local
natural-language-inference classifier, no model calls.

```yaml
entailment:
  label: entails        # entails | neutral | contradicts
  score: 0.973          # probability of `label`, 3 decimals
  model: MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli
  premise: quote        # quote | window
```

Present on every claim that has a non-empty `quote` and `text`; absent
means *not assessed* (no quote, or a digest that predates the check),
which consumers must not read as neutral.

The check runs in two stages, and `premise` says which one produced the
verdict. Stage one takes the speaker name plus the `quote` as premise and
the `text` as hypothesis; `entails` or `contradicts` there is final. Only
a `neutral` goes to stage two, whose premise is the record text 800
characters either side of the located quote; that verdict is final. A
quote that cannot be located in the record gets stage one only.

Why two stages: measured on 50 hand-labelled claims (2026-09-02), the
bare quote licenses about a quarter of good claims. The rest are neutral
at p 0.9-1.0, not because they are wrong but because a claim text is
written self-contained - it names the speaker, expands the acronym,
resolves "that document" - and the quote carries none of that. The
surrounding record does, and with it 38 of 45 good claims entail while
11 of 12 mutated contradictions are still caught. That quarter is the
observed warrant gap of the corpus: a reader shown only the quote is
shown the licence for about one claim in four.

Reading the verdicts:

- `entails` / `quote` - the strong case; the quote alone carries the claim.
- `entails` / `window` - the weaker case; the quote does not carry the
  claim on its own, the record around it does. Report the two entailed
  fractions separately, never averaged.
  An `entails`/`window` with `score` under 0.5 is a near-tie: on 34
  constructed claims that go beyond the record (invented years, inferred
  motives, merged sources) the seven that came out `entails` all scored
  0.39-0.42, and nine good claims sat in the same band. No gate is applied;
  the review order below puts them first.
- `neutral` - not warranted even by the surrounding record.
- `contradicts` - the quote (or, with `premise: window`, the record)
  denies the claim.

Review order: `contradicts` by score descending, `neutral` by score
descending, `entails`/`window` by score ascending, `entails`/`quote` by
score ascending, not assessed last. `score` is the probability of the
label given, so a `contradicts` at 0.9 is a confident contradiction.

Known weak spots of the classifier: unit conversions in the text
("5'10" against "1.78 metres"; knots against km/h) and redaction tokens
in the quote both read as contradiction or neutral more often than they
should. Stage one uses the base checkpoint above; stage two the large
sibling `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli`.

## Round-tripping

The digester maintains two functions paired around this schema:

- `extraction_to_yaml` - emits the schema from a fresh extraction
  result (mints universally unique identifiers for nodes and claims).
- `parse_digest_yaml` - reads the schema into the same internal dict
  shape the downstream importer already consumes.

Tests in the digester repository round-trip representative digests
through both functions and assert byte-equal output. A breaking change
to the format bumps the schema version and writes a new spec document.

## Writing rules

Producers (the digester, the converter, future tooling) must:

- Emit fields in the order listed above; readers may not depend on the
  order but consistency makes the files diffable.
- Omit fields whose value is null, an empty string, an empty list, or
  an empty object. Do not emit `reference: null` - omit the key.
- Use YAML block scalars (`|-`) for any string containing newlines or
  longer than approximately 80 characters. Short strings use plain
  scalars.
- Use unicode allowed: do not escape non-ASCII. Names in non-Latin
  scripts appear as their script.
- Universally unique identifiers are RFC 4122 version 4 in lowercase
  hex form.

Readers must:

- **Pass document-level blocks through whole rather than enumerating them.** A
  parser listing the blocks it knows (`pre_digest`, `prompts`, `run_kind`,
  `ai_usage`, ...) silently drops the next one added, and the failure is
  invisible: the consumer sees a well-formed digest missing a field it never
  knew to ask for. This is how `curation` came to be specified and unreadable on
  the same day - the block existed in the file and every consumer reading it
  through the shared parser still saw the digest as unmodified model output,
  which is the one thing the block exists to prevent.

  Where a block must be withheld from a particular consumer - `ai_usage` must
  not reach the graph, which feeds the public site - that is the CONSUMER's
  policy, applied after parsing. Parsing is not the place to decide what a
  consumer is allowed to see: offer everything and let each consumer choose, or
  every future field inherits an old policy decision by accident.

## Planned: multi-model digestion and canonical reconciliation

Direction recorded in [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md); not yet built. Today the relationship is 1:1 (one model, one digest, `model: <alias>`). The planned direction:

- **N model-variants per ingest** - one ingest digested by several models, each a full digest, stored at `digests/variants/{friendly-name}/{model-id}.{prompt-sha8}.yaml` (a `variants/` subtree beside the canonical digests at the root of `digests/`; the assimilator globs `**/*.yaml` there and drops anything under `variants/`, so they are never imported). The variant key carries the model AND the prompt hash ([0039 amendment 2026-07-04](../decisions/0039-multi-model-digestion-canonical-reconciliation.md)), so a prompt tune on the same model never overwrites the prior output. This layout is built; the variants store now.
- **One canonical** at the unchanged `digests/{friendly-name}.yaml` - a SELECTED per-model digest, not a merge: the selector picks one whole variant as the canonical (no claim-clustering, no dedup-across-variants, no best-phrasing synthesis). Until the selector lands the canonical is latest-written by a production run. It is the only digest the assimilator imports; the variants are inert.
- **Schema `anomalica/digest/2`** (lands with the selector): `model` carries the versioned id; the canonical gains `selected_from` (the candidate variants and the winner) - its presence distinguishes a canonical from a variant.
- **Independence**: multiple models on one source are alternatives, not corroboration - zero added independence. The evidence model counts independence by provenance-root, not claim-count (decision 0039).

## Legacy markdown format

Prior to schema `anomalica/digest/1`, the digester emitted a markdown
intermediate at `digests/extracts/{name}.extract.md`. That
format is described in the codebase under `digester/markdown_format.py`
for historical reference only and is no longer produced. The conversion
script `extract_to_yaml.py` translates existing markdown extracts into
the YAML format without invoking the artificial-intelligence pipeline.
