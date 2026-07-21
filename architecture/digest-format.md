# Digest interchange format

The output of the digester for each record is a single YAML file at
`digests/records/{friendly-name}.yaml`. This file is the canonical
intermediate between the artificial-intelligence extraction step and every
downstream consumer (the SQLite database, the workbench, the assembler).
Today the relationship is 1:1 (one model, one digest). A planned direction
makes it 1:N - several models per ingest, reconciled into this single
canonical digest - see [Planned: multi-model digestion](#planned-multi-model-digestion-and-canonical-reconciliation)
and [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md).

The companion document on the ingester side is
[`record-format.md`](record-format.md). This document covers the digester
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
  records/
    2020-04-27-web-statement-by-the-department-of-defense-on-the-release-of.yaml
    2024-08-19-ebook-imminent-inside-the-pentagon-s-hunt-for-ufos.yaml
    ...
```

One YAML file per record. Filenames mirror the friendly filenames in
`ingests/records/` (same `{date}-{format}-{slug}` form), with
`.md` swapped for `.yaml`. This pairing is how the workbench joins the
two sides for any given record.

## Document structure

The order of top-level keys is fixed: `schema`, `extracted_at`, `model`,
`ai_usage`, `prompts`, `pre_digest`, `record`, `terminology`, `nodes`,
`domain_claims`, `infrastructure_claims`. Null and empty values are omitted - if
a record has no infrastructure claims, the key is absent rather than present with
`[]`. `ai_usage`, `prompts`, `pre_digest`, and `terminology` are optional blocks
(see below).

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

The span of the source the claim was drawn from. For a timestamped record this is
a canonical `HH:MM:SS.d-HH:MM:SS.d` range, recovered deterministically by
realigning the claim's verbatim `quote` against the record's word timings rather
than by asking the model - a model left to write `location` itself picks a
different axis per chunk (timecodes, bare seconds, even source line numbers),
which makes variants from different models impossible to cluster against one
another.

### `record`

The five fields describing the source record this digest was produced
from. `id` is the universally unique identifier assigned to the record
node in the knowledge graph and is the join key against
`ingests`. `producer` is in `Last, First Middle` form for
persons ([person naming](node-types.md#person)) or a plain
organisation name. `date` is a string in the form `YYYY` or `YYYY-MM-DD`.
`reference` is an external identifier where one exists (book ISBN,
report number, archive identifier) and is often null.

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
[record-format.md](record-format.md). Absent on digests produced before the
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
`location?`, `date?` or `date_range?`, `refs?`, `quote?`, `text`.

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

## Planned: multi-model digestion and canonical reconciliation

Direction recorded in [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md); not yet built. Today the relationship is 1:1 (one model, one digest, `model: <alias>`). The planned direction:

- **N model-variants per ingest** - one ingest digested by several models, each a full digest, stored at `digests/variants/{friendly-name}/{model-id}.{prompt-sha8}.yaml` (a top-level `variants/` tree, NOT under `records/`, because the assimilator globs `records/` recursively and would otherwise import them). The variant key carries the model AND the prompt hash ([0039 amendment 2026-07-04](../decisions/0039-multi-model-digestion-canonical-reconciliation.md)), so a prompt tune on the same model never overwrites the prior output. This layout is built; the variants store now.
- **One canonical** at the unchanged `digests/records/{friendly-name}.yaml` - a SELECTED per-model digest, not a merge: the selector picks one whole variant as the canonical (no claim-clustering, no dedup-across-variants, no best-phrasing synthesis). Until the selector lands the canonical is latest-written by a production run. It is the only digest the assimilator imports; the variants are inert.
- **Schema `anomalica/digest/2`** (lands with the selector): `model` carries the versioned id; the canonical gains `selected_from` (the candidate variants and the winner) - its presence distinguishes a canonical from a variant.
- **Independence**: multiple models on one source are alternatives, not corroboration - zero added independence. The evidence model counts independence by provenance-root, not claim-count (decision 0039).

## Legacy markdown format

Prior to schema `anomalica/digest/1`, the digester emitted a markdown
intermediate at `digests/extracts/{name}.extract.md`. That
format is described in the codebase under `digester/markdown_format.py`
for historical reference only and is no longer produced. The conversion
script `extract_to_yaml.py` translates existing markdown extracts into
the YAML format without invoking the artificial-intelligence pipeline.
