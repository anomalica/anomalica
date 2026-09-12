# 0037. An AI-operation ledger: provenance and usage per call

Date: 2026-06-21
Status: accepted

## Context

Every AI or compute call the pipeline makes - a digester extraction, an assimilator consolidation, an assembler write, an ingester transcription - consumes resources (model usage, compute time) and is a provenance fact (which model, which version, produced this output). Today none of it is persisted. Token usage exists only as a process-global in-memory accumulator in the shared transport (`anomalica-common`'s `llm` module - per-run, lost on process exit) and as a transient `USAGE_JSON:` stdout line the workbench runner scrapes into a capped 50-entry `processing.json`. There is no cross-component record, no per-call granularity, no model-version provenance, and no persistent usage history.

Two needs converge on one store:

- **Usage.** Per-call usage (tokens, cache, duration) has no durable record today and needs a data source.
- **Provenance.** [0008](0008-content-traceable-to-sources.md) and [0010](0010-auditable-assembly.md) trace a page to its source claims; neither records WHICH model (and version) produced each extraction. Reproducibility and audit need that.

A grounding sweep of the actual code established the shape of the problem - in particular that the pipeline has no single AI call-path (see Consequences).

## Decision

A single append-only **AI-operation ledger**: one row per AI/compute call, recording its usage and its provenance. Schema `anomalica/ai-ledger/1`. SQLite (per [0016](0016-sqlite-storage.md)), at `~/.local/share/anomalica/ai-ledger.db`. The field-level contract is [architecture/ai-ledger-format.md](../architecture/ai-ledger-format.md).

### One shared writer, many call sites (the single-producer discipline)

The pipeline does NOT have a single AI call-path. Grounding confirmed five distinct emission sites (listed under Consequences). The single-producer guarantee is therefore held at the **writer**, not the transport: one shared ledger-append helper in anomalica-common, imported and called at each emission boundary - the same discipline applied to the shared `claim_hash` and the canonical slugifier. Every site emits through the one writer, so rows are uniform no matter which path produced the call.

### Usage

Per call, the ledger records usage (tokens in/out, cache, duration).

### Model identity and provenance

`model_id` + `model_version` per row. For Claude: the alias on the subscription path (the only identity the CLI is given), the versioned id on the API path (`API_MODEL_MAP`), with `model_version` the dated pin where one exists (haiku is dated; sonnet and opus are version-pinned but undated). For GPU/CPU: the local model and version (e.g. `whisperx-large-v3`, `pyannote-3.1`, the fastembed model). Together with `target` and `operation`, this answers "which model version produced this claim/record" - the provenance half of the ledger.

### Attribution columns must be threaded from callers

`component`, `operation`, and `target` do not exist at the transport choke point (`_call`, deliberately component-agnostic). They must be threaded in from each caller. This is the load-bearing implementation change.

## Why

- **One store, both jobs.** Usage accounting and model provenance are per-call facts about the same event; splitting them would double the instrumentation.
- **Append-only, per-row `schema_version`.** A ledger is a log, not mutable state; rows written under different schema versions coexist, so a version bump never needs a migration.
- **Separate from `knowledge.db` / `infrastructure.db`.** Those are the assimilator's knowledge graph (domain content), regularly dropped, rebuilt, and snapshotted - which would wipe a ledger. The ledger is process telemetry: a different domain, a different producer (the shared transport plus paths that never touch the graph). NB: the assimilator's `infrastructure.db` holds infrastructure *claims* (domain content routed by `ClaimCategory`) - not to be confused with this operational ledger.
- **A new shared data dir.** The producer is anomalica-common, loaded by every component; the ledger is cross-component, so it must not sit under any one component's directory. `~/.local/share/anomalica/` is greenfield. anomalica-common has no data-dir abstraction today - the ledger gives it its first on-disk store, so a new env-overridable resolver (`ANOMALICA_DATA_DIR` / `ANOMALICA_LEDGER_DB`) lands there.

## Consequences: the implementation fan-out (grounded)

Five emission sites, only three of which share a transport today.

**Through the shared transport** (`anomalica_common.llm._call`) - one instrumentation point covers three operations, but needs `component`/`operation`/`target` threaded in:

- digester `extract`
- assimilator `consolidate`
- assimilator `corroborate`

**Bypassing the shared transport** - each needs its own call to the shared writer:

- **assembler `assemble`** - has a private duplicate transport that currently DISCARDS usage (reads only the result text, drops `message.usage` / `total_cost_usd`). It must stop discarding and emit. Load-bearing gap 1.
- **ingester PDF `ingest`** - private Anthropic path; already has tokens in its `meta`, just not persisted. Emit.
- **ingester audio/video `ingest`** (transcribe + diarise) - local GPU/CPU; no tokens, and NOTHING measures call wall-time today (the only duration recorded is the source-media length). GPU duration needs new timing instrumentation. Load-bearing gap 2.
- **assimilator `embed`** - local CPU fastembed; no tokens; duration only if instrumented.

The ingester repo has zero `anomalica_common` imports, so its paths can never route through the shared transport - they call the shared writer (or emit rows) directly.

**Reserved, not yet populated:** `rate_limit_consumed`. The subscription CLI wrapper exposes no rate-limit or allowance field today; the column exists for when it does.

**Partially supersedes** the workbench runner's `processing.json` token/cost scrape. Once the ledger is populated, the Schedule tab reads per-call cost and tokens from the ledger; `processing.json` keeps job-orchestration state (on/failed/margin, job outcome, GPU job records). The two are joined, not merged - the ledger is per-call, `processing.json` per-job.

## Scope

A new operational store, a shared writer, and per-site emits. It gives per-call usage a durable home and adds model provenance to the [0008](0008-content-traceable-to-sources.md)/[0010](0010-auditable-assembly.md) audit trail. It changes no model behaviour. The operation and transport enums align to the scheduler's existing job vocabulary. Field detail is in [architecture/ai-ledger-format.md](../architecture/ai-ledger-format.md) (`anomalica/ai-ledger/1`), scaffolded now and filled as the writer lands at each site.

## Amendment 2026-07-23: no stored cost, anywhere

Stored dollar figures come out of emitted AI usage. `notional_cost_usd`
and `price_basis` are dropped at the producer; `model`, `model_version`,
and token counts stay. A consumer that wants to show a notional cost
derives it from tokens against published list prices at the point of
display. The canonical statement of the rule is in
[format-specs.yaml](../reference/format-specs.yaml); the field-level
contract is [digest-format.md](../architecture/digest-format.md#ai_usage).

Two clauses in this record are superseded by it:

- The assembler item in the implementation fan-out lists
  `message.usage` / `total_cost_usd` together as what the private
  transport discards and "must stop discarding and emit". It must emit
  **usage**, not cost - `message.usage` yes, `total_cost_usd` no.
- The `processing.json` supersession says the Schedule tab "reads
  per-call cost and tokens from the ledger". It reads **tokens** and
  derives cost at display. This was loose wording rather than a schema
  decision: the ledger's own field table
  ([ai-ledger-format.md](../architecture/ai-ledger-format.md)) never had
  a cost column, so the ledger schema was always compliant.

Grounds. A stored dollar figure bakes in a price that changes and turns
an interchange artefact into a billing one. The spread when measured was
59 digests and 53 assembled articles carrying stored dollars, and
`content/` feeds the public site - so a cost-shaped field was sitting in
a repository read far more widely than the dev layer. Nothing is lost by
deriving: `extracted_at` already dates each run, so which price era
applied stays recoverable without a stored basis.

No bulk rewrite. The fields clear as records re-digest and articles
re-assemble, both of which happen anyway; artefacts produced before this
date may still carry them.

## Amendment 2026-09-11: subscription routes are distinct provenance

`subscription` no longer identifies every subscription-backed call. The
Anthropic subscription retains that existing value; the candidate authenticated
OpenAI route records `openai-subscription`. Metered and subscription access to
the same OpenAI model use separate policy ids because their context limits,
allowance accounting and transport behaviour differ. The ledger records the
route-specific model id and transport on every call. Provider-reported allowance
percentages pace a route but do not replace per-call token and duration fields.

## Amendment 2026-09-11: qualified attempts include pre-call refusals

For a route with mandatory execution qualification, the auditable event starts
when a route and final submitted payload have been selected, not only when a
provider process starts. A failed capacity, authentication, executable-version
or configuration check is therefore one ledger attempt with an error outcome,
no usage, and `provider_started: false`. A request that passes qualification and
then fails remains an error attempt with `provider_started: true`. Dry runs and
rejections before route and payload selection make no attempt and write no row.

The field contract records exact submitted-payload byte identity, the exact raw
model-policy snapshot identity, qualification status and a closed non-secret
refusal code. Transport version and configuration hash are observed values: on
a refusal caused by an unreadable value they remain null rather than copying the
expected policy value and falsely claiming observation. The policy snapshot
contains the expected qualification.

These are conditional additions within `anomalica/ai-ledger/1`: historical and
unqualified-route rows may omit them, while every `openai-subscription` attempt
must satisfy the route-specific completeness rules in
[ai-ledger-format.md](../architecture/ai-ledger-format.md). The current aggregate
JSONL run log is not this ledger and must not acquire the canonical name by
adding similarly named fields. OpenAI subscription production remains blocked
until the shared SQLite writer records one row per attempt, including pre-call
refusals.

The original physical "append-only" wording is corrected for crash-safe
implementation. An attempt row is inserted and committed as `pending` before
provider execution, its invocation boundary is committed before the process or
request starts, and it is finalised once in place. Final rows are immutable and
conflicting finalisation fails. Each provider retry is a new row, correlated by
an optional attempt-group id rather than aggregated into a retry count. A
database failure before invocation refuses dispatch; a failure afterwards
leaves a durable pending row and prevents the output being accepted. Startup
does not close pending rows because another process may still own one; any later
maintenance closure requires independent evidence that its attempt is no longer
running and never retries inference automatically. The exact lifecycle is in
[ai-ledger-format.md](../architecture/ai-ledger-format.md).
