# Naming migration: record, ingest, digest

Status: steps 1 to 5 landed 2026-08-13. Step 6 (the content delivery network) is
held pending approval of its cost, and step 7 (the hash split) is superseded - see
Identifiers. Companion to the terms in [data-model.md](data-model.md) and the format
spec in [ingest-format.md](ingest-format.md), both of which carry the corrected
vocabulary.

## The rule

Each stage is named after what produces it.

| Term | What it is | Where it lives |
|------|-----------|----------------|
| **record** | The original artefact, in whatever format it arrived: the PDF, the audio file, the ebook, the captured web page. Immutable. | `records/` |
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

All three landed on 2026-08-13.

| Was | Is | Contents |
|-----|----|----------|
| `sources/` (plain directory, not a repo) | `records/` | 1,062 originals, 30GB |
| `ingests/records/` | `ingests/by-name/` | 219 readable-name symlinks into `store/`; pairs with `store/`, which addresses by hash |
| `digests/records/` | `digests/` itself | The 80 canonical digests moved up one level; the misnamed folder was removed rather than renamed |
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

Only the paths were renamed. The identifiers below are NOT done, deliberately: each
one rewrites stored data or a public contract, and none of them changes behaviour.
They are listed so the remaining work is visible rather than assumed finished.

| Identifier | Status | Occurrences | Note |
|-----------|--------|-------------|------|
| `schema: anomalica/record/1` | NOT CHANGED, and probably never as its own step | 135 in code, all 306 ingests on disk | The version is a compatibility marker, not a label. Move it when the FORMAT breaks, not when the word does |
| `source_file` | OUTSTANDING | 73 | Frontmatter field naming the original; rewrites every stored ingest |
| `parse_record`, `record_body` | OUTSTANDING | 61 | Parser entry points; pure code, safe to do any time |
| `record_id` | CORRECT AS IS | 158 | Identifies the record, and one record has exactly one ingest |
| `record_hash` | rule settled, data lagging | 1,982, nearly all in generated pages | See below |

`record_hash` needs no decision: the rule was already settled on 2026-07-25
([ingest-format.md](ingest-format.md#store)). `content_hash` hashes the archived
original's bytes plus any scope string, never the extracted body, which is what makes
re-extraction in place safe.

THE NARRATIVE AND THE DATA DISAGREE, and the data is consistent enough to be
believed. Across all 221 ingests: audio, pdf and video (171) hash the original's
bytes and carry no `source_hash`; web and ebook (50) hash the body and every one
carries `source_hash`. No exceptions either way, and ebooks extracted after the
reconciliation date behave identically to those before it. So this is a two-hash
design for the two types whose original is not the text, not an unmigrated tail.
Either the reconciliation never shipped for web and ebook or its written scope is too
broad; the ingester owns the hashing and is resolving which. `ingest-format.md`
carries the measured table and a pointer to the contradiction.

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

Each step leaves the system working. Steps 3 and 4 landed together per repo.

1. **Vocabulary.** DONE. `data-model.md` defines record, ingest and digest;
   `record-format.md` is now `ingest-format.md`.
2. **Document links.** DONE. 51 files across 11 repos.
3. **Directories.** DONE. All three renames, by `git mv` inside each repo so history
   follows. `sources/` is not a repo, so that one is a plain move.
4. **Code.** DONE. Every repo's suite green: digester 147, assimilator 275,
   scheduler 185, anomalica-common 179, ingester 347 across four handlers,
   workbench 340.
5. **Schema string.** NOT NEEDED as a separate step - `anomalica/record/1` names the
   ingest format, and renaming it would rewrite all 306 stored ingests and every
   consumer's validation for no behavioural gain. The version is a compatibility
   marker, not a label; it moves when the FORMAT breaks, not when the word does.
   Revisit at the next breaking change, when it costs nothing extra.
6. **Content delivery network.** HELD, pending Mark's approval of the cost. Sequence
   corrected by the workbench, which owns `edge/main.ts`: COPY the objects to the new
   prefix, SWITCH the minting in one deploy, DELETE the old prefix once the gate's
   300-second token lifetime has elapsed. A true rename has a window in which an
   issued link points at an object that no longer exists; three steps has none. The
   set is 19 copyright-gated originals totalling 104MB, so the transient duplication
   is negligible.
7. **Hash split.** SUPERSEDED. The rule was already settled on 2026-07-25; what
   remains is the stored data catching up with it, described under Identifiers.

## What the sweep missed, and why

Two sites survived every pattern-based sweep and both failed in the quiet
direction - after the expensive work, in a way that reads as something else.

- **`ingester/ingest` staged `records/`.** Every ingest after the rename acquired the
  source, extracted it, wrote the ingest, wrote its symlink and its verification
  sidecar, and then exited 128 on `pathspec 'records/' did not match any files`. The
  output was correct and simply never committed, so ingests piled up untracked and
  the failure read as a git problem rather than as work going nowhere.
- **`digester/reports/run-queue.sh` resolved `$DIGESTS/records/{slug}.yaml`.** The
  comment directly above that line already warned that getting it wrong "reads every
  record as undigested and re-runs the entire corpus" - which is what it would have
  done, on the plan, at corpus scale.

THE PATTERNS WERE THE PROBLEM. The sweeps matched shapes that appear in Python -
`ingests/records`, `/ "records"`, `digests_path / "records"` - and a bare `records/`
inside a shell command matches none of them. Neither site is exotic; both are the
most ordinary way to write a path in shell.

So when renaming a directory, grep for the BARE segment (`records/`) across every
executable file type including shell, and read every hit rather than filtering to
the shapes you expect. Most hits will be prose and public URLs that must not change,
which is the cost; the alternative is a path that only bites after the expensive
work has been done.

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
