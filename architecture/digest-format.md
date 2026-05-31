# Digest interchange format

The output of the digester for each record is a single YAML file at
`digests/records/{friendly-name}.yaml`. This file is the canonical
intermediate between the artificial-intelligence extraction step and every
downstream consumer (the SQLite database, the workbench, the assembler).

The companion document on the ingester side is
[`record-format.md`](record-format.md). This document covers the digester
side.

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
`record`, `nodes`, `domain_claims`, `infrastructure_claims`. Null and
empty values are omitted - if a record has no infrastructure claims, the
key is absent rather than present with `[]`.

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
    location: paragraph 1
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

### `record`

The five fields describing the source record this digest was produced
from. `id` is the universally unique identifier assigned to the record
node in the knowledge graph and is the join key against
`ingests`. `producer` is in `Last, First Middle` form for
persons ([decision 0023](../decisions/0023-person-naming-convention.md),
[decision 0026](../decisions/0026-person-name-ordering.md)) or a plain
organisation name. `date` is a string in the form `YYYY` or `YYYY-MM-DD`.
`reference` is an external identifier where one exists (book ISBN,
report number, archive identifier) and is often null.

### `nodes`

A list of every node mentioned by any claim. Field order per item:
`id`, `type`, `name`, optionally `metadata`. The `id` is a
freshly-minted universally unique identifier per node per digest. The
same real-world person may appear with different ids across digests;
the deterministic import step resolves duplicates via name and alias
matching.

`type` is one of the eight ingestion types defined in
[`node-types.md`](node-types.md): `person`, `organisation`, `place`,
`event`, `matter`, `object`, `document`, `concept`.

`metadata` is an optional mapping for type-specific extra data
(sentiment markers on organisations, date ranges on documents, role
labels). The schema does not constrain its keys.

### Claims

`domain_claims` and `infrastructure_claims` are two parallel lists with
identical item shapes. They are kept separate because the two
extraction passes run independently and feed two separate databases.

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

## Legacy markdown format

Prior to schema `anomalica/digest/1`, the digester emitted a markdown
intermediate at `digests/extracts/{name}.extract.md`. That
format is described in the codebase under `digester/markdown_format.py`
for historical reference only and is no longer produced. The conversion
script `extract_to_yaml.py` translates existing markdown extracts into
the YAML format without invoking the artificial-intelligence pipeline.
