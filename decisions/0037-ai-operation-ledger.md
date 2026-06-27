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
