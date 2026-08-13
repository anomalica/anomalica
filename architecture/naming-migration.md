# Naming migration: record, ingest, digest

Status: specified, not started. Companion to the terms in [data-model.md](data-model.md)
and the format spec in [ingest-format.md](ingest-format.md), both of which already
carry the corrected vocabulary.

## The rule

Each stage is named after what produces it.

| Term | What it is | Where it lives |
|------|-----------|----------------|
| **record** | The original artefact, in whatever format it arrived: the PDF, the audio file, the ebook, the captured web page. Immutable. | `records/` (today `sources/`) |
| **ingest** | The markdown transcription of one record, written by the ingester. Has its own hash, its own character offsets, its own edit history. | `ingests/store/{hash}.md` |
| **digest** | The claims file written by the digester from one ingest. | `digests/{slug}.yaml` |
| **source** | Not a file. The person or organisation that produced a record. David Fravor is a source; the New York Times is a source. | Graph node |

A record maps to exactly one ingest. That one-to-one relationship is what makes the
migration tractable, and it is why `record_id` is not being renamed: it identifies
the record, and the ingest is derivable from it.

## This is not a find-and-replace

The word "record" is used correctly in roughly half its occurrences and incorrectly
in the rest, and a blind rename would corrupt the half that is right. Every
occurrence falls into one of three buckets.

**Means the original: leave alone.** Record classification (how close the artefact
is to the events it covers), record provenance, `provenance.publisher`,
`provenance.creators`, the Record node type in the knowledge graph, `record_id` on a
claim, and the reader-facing pages under `content/pages/records/`. All of these refer
to the original document. Under the corrected vocabulary they are already right.

**Means the markdown: rename to ingest.** The schema string, the parser entry points,
the directory of readable-name symlinks, anything that reads or writes the `.md`
file, and any comment describing "the record body" or "the record format".

**Means the original but says "source": rename to record.** `sources/`,
`source_file`, and the `/sources/` path on the content delivery network. These
predate the decision that a source is a person or organisation rather than a file,
and they are the reason the word is ambiguous in both directions.

The third bucket is easy to miss. Correcting only the second leaves "source" still
meaning two things, which is the same defect one word to the left.

## Concrete changes

### Directories

| Now | Becomes | Contents |
|-----|---------|----------|
| `sources/` (plain directory, not a repo) | `records/` | 1,062 originals |
| `ingests/records/` | `ingests/by-name/` | 220 readable-name symlinks into `store/`; pairs with `store/`, which addresses by hash |
| `digests/records/` | `digests/` itself | The 80 canonical digests move up one level; the misnamed folder is removed rather than renamed |
| `digests/variants/` | unchanged | 209 per-model variants, still grouped per ingest |

`ingests/store/` keeps its name. `content/pages/records/` keeps its name: those pages
are about the original document.

### Why the canonical digests are not distinguished by filename

A filename convention was considered and rejected: `{slug}.yaml` for canonical and
`{slug}--{model}.{signature}.yaml` for a variation, in one flat directory.

It reads well and keeps each ingest's digests adjacent in a sorted listing, but the
separator is a parsing convention, and a convention is something a future slug can
violate. Ingest names already contain dots (146 of 220 carry a `.v2` infix), which is
why a dot could not be the separator in the first place; there is no reason to assume
hyphens are safer forever. Every consumer would then have to know the rule, and one
that forgot would silently treat a variation as canonical.

A directory boundary cannot be broken by a filename. So the canonical digests sit at
the root of `digests/` and the variants a level below:

```
digests/
  2020-09-04-pdf-range-fouler-reporting-form.yaml
  variants/
    2020-09-04-pdf-range-fouler-reporting-form/
      sonnet.e9b8b6d4.yaml
```

`digests/*.yaml` is then exactly the canonical set. No filter, no convention, and a
variation cannot match the glob because it is not at that level.

### Identifiers

| Now | Becomes | Live occurrences | Note |
|-----|---------|------------------|------|
| `schema: anomalica/record/1` | `anomalica/ingest/1` | 135 in code, plus all 306 ingests on disk | Consumers validate against this string |
| `source_file` | `record_file` | 73 | Frontmatter field naming the original |
| `parse_record`, `record_body` | `parse_ingest`, `ingest_body` | 61 | Parser entry points |
| `record_id` | unchanged | 158 | Correctly identifies the record |
| `record_hash` | see below | 1,982, nearly all in generated pages | Ambiguous today; resolved below |

`record_hash` needs a decision rather than a rename. Today the hash is taken over the
original file's bytes for PDF and audio but over the extracted text for web and
ebook, an inconsistency [data-model.md](data-model.md) already flags. The corrected
vocabulary resolves it: a record has a hash over its own bytes, an ingest has a hash
over its own text, and they are different numbers. Splitting them is a data change
and should be done as its own step, after the renames, not folded into them.

Nearly all occurrences are in generated pages under `content/`, which the assembler
rewrites, so they are not hand-edited.

### Externally visible: the content delivery network

`workbench/edge/main.ts` mints signed URLs to `/sources/{hash}.{ext}` on the Bunny
storage zone. Renaming the local directory does not move those objects. The storage
path and the URL minting have to change together, or gated originals stop resolving
for anyone holding a link.

This is the only step visible outside the machine, and the only one that can break
something a reader touches. It does not widen access: the same gate applies to the
same files at a different path.

## Order of work

Each step leaves the system working. Steps 3 and 4 must land together per repo.

1. **Vocabulary.** Done: `data-model.md` defines record, ingest and digest;
   `record-format.md` is now `ingest-format.md`.
2. **Document links.** The 51 files across 11 repos that reference the old filename.
   Mechanical, no behaviour.
3. **Directories.** The three renames above, by `git mv` inside each repo so history
   follows.
4. **Code.** Per repo, bucket by bucket, tests run before the commit. The ingester and
   `anomalica-common` first, since every other repo reads what they write.
5. **Schema string.** `anomalica/ingest/1` written into all 306 ingests, with
   consumers accepting both values for exactly as long as the sweep takes.
6. **Content delivery network.** Move the storage prefix and the URL minting together,
   then verify a gated original still resolves through a freshly signed link.
7. **Hash split.** `record_hash` versus ingest hash, as a separate data change.

## Verification

- After step 3: `assimilate` rebuilds the graph and reports the same node and claim
  counts as before the move.
- After step 4, per repo: that repo's test suite, plus one end-to-end ingest of a
  known record producing a byte-identical ingest.
- After step 5: every ingest parses, and the digester refuses an unknown schema.
- After step 6: a signed URL for a gated original resolves, and an unsigned one does
  not.
- Throughout: no `git push --force`, and the corpus measurement in
  `master/tools/claim-fidelity.py` reports unchanged grounding figures. A drop there
  means a path rename silently detached digests from their ingests.
