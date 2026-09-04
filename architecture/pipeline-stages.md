# Pipeline stages: what runs, when, and what it costs

Every step the pipeline performs, in the order material passes through it. The
[overview](overview.md) tells the story of how data moves between components
and [`reference/architecture.yaml`](../reference/architecture.yaml) draws the
components and data stores; neither lists the *steps*, which is what someone
needs to answer "when does the quote check happen" or "what runs after an
import". That is this document.

**How to read the table.** *Trigger* is what makes the step due, and it is
always a fact about an artefact on disk, never a person remembering. *Runs on*
is which of the scheduler's three cards contends for the resource. *Costs* is
money or subscription allowance; a step marked free spends neither.

## The stages

| # | Stage | Trigger | Runs on | Costs | Writes |
|---|-------|---------|---------|-------|--------|
| 1 | **Intake** | A URL or file the operator adds | Local CPU | free | A stub in `ingests/store/v1/` with the source's real title |
| 2 | **Acquire** | A stub with no archived original | Local CPU | free | The original in `records/{hash}.{ext}`, plus a frozen page and a full-page render for web sources |
| 3 | **Ingest: transcribe** | An audio or video stub | Local GPU | free | A record with per-word timestamps (Whisper on the card) |
| 4 | **Ingest: extract** | A web, ebook or image stub | Local CPU | free | A record, extracted by rule (no model) |
| 5 | **Ingest: read** | A PDF stub | Remote AI | metered | A record, read by a vision model |
| 6 | **Cleanup pass** | A record just ingested | Local CPU | free | Proposed frontmatter corrections, for approval in the workbench |
| 7 | **Pre-digest** | A record with no current pre-digest | Local CPU | free | The exact model input, stored so it can be inspected ([decision 0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)) |
| 8 | **Digest** | A record with no digest, or one whose body was re-extracted | Remote AI | plan or metered | Claims and nodes in `digests/` |
| 9 | **Quote check** | Runs as the **last step of every digest**, and as a backfill for any digest whose claims carry no verdict | Local GPU | free | A label on each claim: does its quote support it, contradict it, or neither |
| 10 | **Variant digest** | A record already in the comparison - one a reviewer highlighted, or one that already carries a variant - and a model that has not covered it | Remote AI | metered | A second digest under that model, for side-by-side comparison only |
| 11 | **Import** | A digest not yet in the graph | Local CPU | free | Claims and nodes in the knowledge graph |
| 12 | **Embed** | Claims without vectors | Local CPU | free | Claim vectors, for corroboration and merge shortlisting |
| 13 | **Merge shortlist** | The graph changed since the last pass | Local GPU | free | Candidate node pairs, scored by a reranker so the likeliest duplicates sort first |
| 14 | **Merge verify** | Shortlisted pairs no human or model has judged | Remote AI | plan | A verdict per pair; nothing merges without a human |
| 15 | **Corroborate** | Claim pairs across records that may agree or conflict | Remote AI | plan | Corroboration links |
| 16 | **Propose pages** | The graph changed | Local CPU | free | Which pages should exist |
| 17 | **Synthesise** | A page whose brief is stale or missing | Local CPU | free | One brief per page: the graph slice that page is written from |
| 18 | **Assemble** | A brief newer than its page, or a page with dead citations | Remote AI | metered | The page's prose in `content/` |
| 19 | **Publish** | New or changed content | Local CPU | free | The rendered site |

## What decides what runs next

One rule, in `scheduler/backend/priority.py`, orders every job whatever card it
lands on. Highest first:

1. **Repair** - something published is broken (a page with dead citations).
2. **Finish** - an item already part-way through the pipeline.
3. **Verify** - checking what already exists (stages 9 and 13 above).
4. **New** - taking in material that is not in the pipeline yet.

Within a band: free work first (it cannot be held by a budget), then the
producing stage's own value for the job, then oldest first. An explicit
staging by the operator still wins over all of it.

## Two things worth knowing

**A model on this machine is still a model.** Stages 9 and 13 run neural
models on the graphics card. They spend no money and no plan allowance, but
they are resolved through [`model-policy.yaml`](model-policy.yaml) like every
other model stage and recorded in the AI-usage ledger with their model id and
wall time, so the record of what touched an artefact is complete.

**A record earns a comparison; it does not get one by default.** Stage 10 once
crossed every digestible record with every model that had not covered it, which
put 197 comparison-only jobs in the queue against 46 records that had never been
digested at all - evaluation work outranking the artefact it evaluates. A new
record gets no variants. It earns them by being highlighted by a reviewer, or by
already being one of the records the comparison is measured on.

**Nothing is triggered by a person remembering.** Every trigger in the table
is derived from an artefact: a record with no digest, a brief newer than its
page, a graph newer than the last merge pass. A step that needed someone to
run a command would be a step that silently stops happening.
