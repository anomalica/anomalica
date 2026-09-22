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

Stages 2-5, the source-map/`digest/2` parts of 7-8, and Asset-derived work in 15
describe the accepted 0051 migration target. Deployed components still use the
legacy single-source Record, scalar digest location and graph schema.

| # | Stage | Trigger | Runs on | Costs | Writes |
|---|-------|---------|---------|-------|--------|
| 1 | **Intake** | A URL or file the operator adds | Local CPU | free | An untracked scheduler-owned `queue/*.md` candidate |
| 2 | **Acquire Asset** | A candidate with no archived original | Local CPU | free | Immutable bytes at `records/{asset_hash}.{ext}` plus acquisition/rights metadata |
| 3 | **Create Record** | A new Asset with no Record | Local CPU | free | A default whole-Asset Record and canonical ordered Selection; PDF/image may be explicitly marked temporary for structural review |
| 4 | **Ingest: transcribe/extract** | A Record with no current Ingest | Local GPU, CPU or authorised remote AI by format | format-dependent | The current generated Ingest and structural Record page map |
| 5 | **Structure Record** | A reviewer submits a CAS-bound split/composition | Local CPU | human | Atomic children/composite plus parent retirement; no sidecar inheritance |
| 6a | **Housekeeping: deterministic** | Scheduler reconciliation finds an eligible unreviewed live record without a current version 3 deterministic result; a valid post-commit ingest result runs the same check immediately | Local CPU | free | Deterministic `anomalica/housekeeping/3` proposals and a pending-research sidecar |
| 6b | **Housekeeping: metadata research** | The same exact-input sidecar has deterministic complete and research pending; an authenticated waiver is the only non-run completion | Remote AI | subscription only | Research proposals merged into the same sidecar, or an explicit durable waiver |
| 7 | **Pre-digest** | A Record with no current pre-digest; page-mapped PDF/image also lacks a current source map | Local CPU | free | The exact model input; PDF/image preparation version 9 also emits the deterministic Asset-page source map ([decision 0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)) |
| 8 | **Digest** | A Record with no digest, or one whose body was re-extracted | Remote AI | plan or metered | Digest 2 with exact anchors for page-mapped PDF/image; digest 1 for other media pending typed coordinates |
| 9 | **Quote check** | Runs as the **last step of every digest**, and as a backfill for any digest whose claims carry no verdict | Local GPU | free | A label on each claim: does its quote support it, contradict it, or neither |
| 10 | **Variant digest** | A record already in the comparison - one a reviewer highlighted, or one that already carries a variant - and a model that has not covered it | Remote AI | metered | A second digest under that model, for side-by-side comparison only |
| 11 | **Import** | A digest not yet in the graph | Local CPU | free | Claims and nodes in the knowledge graph |
| 12 | **Embed** | Claims without vectors | Local CPU | free | Claim vectors, for corroboration and merge shortlisting |
| 13 | **Merge shortlist** | The graph changed since the last pass | Local GPU | free | Candidate node pairs, scored by a reranker so the likeliest duplicates sort first |
| 14 | **Merge verify** | Shortlisted pairs no human or model has judged | Remote AI | plan | A verdict per pair; nothing merges without a human |
| 15 | **Relate evidence** | Claim pairs that may agree or conflict | Remote AI plus deterministic validation | plan | Semantic agreement links, exact Asset-page/text-frame evidence units and separately evidenced provenance independence |
| 16 | **Propose pages** | The graph changed | Local CPU | free | Which pages should exist |
| 17 | **Synthesise** | A page whose brief is stale or missing | Local CPU | free | One brief per page: the graph slice that page is written from |
| 18 | **Assemble** | A brief newer than its page, or a page with dead citations | Remote AI | metered | The page's prose in `content/` |
| 19 | **Publish** | New or changed content | Local CPU | free | The rendered site |

## What decides what runs next

One consequence rule, in `scheduler/backend/priority.py`, orders every job
whatever card it lands on. Highest first:

1. **Repair** - something published is broken (a page with dead citations).
2. **Finish** - an item already part-way through the pipeline.
3. **Verify** - checking what already exists (stages 9 and 13 above).
4. **New** - taking in material that is not in the pipeline yet.

Within `finish`, a stage never completed precedes regeneration; known stale
published output precedes known stale unpublished output, then unknown
currentness. Within an equal consequence and completion state: free work first
(it cannot be held by a budget), then the producing stage's own value for the
job, then oldest first. Token estimates constrain dispatch inside an authorised
allowance; they are not a universal priority score. An explicit staging by the
operator still wins over all of it. Priority never grants model or batch
authorisation; the full contract is [end-to-end freshness](freshness.md).

Housekeeping metadata research is the highest-priority automatic remote work. It
runs before every other unstaged remote candidate once allowance is available;
only an explicit operator staging may precede it. This ordering does not grant a
metered route: `housekeep-research` remains subscription-only and fails closed
when that route is unavailable.

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
