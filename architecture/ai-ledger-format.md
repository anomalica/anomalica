# AI-operation ledger format

The ledger is the operational record of every AI or compute call the pipeline makes - one append-only row per call, recording its provenance and usage. Schema `anomalica/ai-ledger/1`. SQLite, at `~/.local/share/anomalica/ai-ledger.db` (env-overridable via `ANOMALICA_LEDGER_DB`, or `ANOMALICA_DATA_DIR` for the directory). See [decision 0037](../decisions/0037-ai-operation-ledger.md) for the why.

The producer is a single shared writer in anomalica-common, called at each emission boundary - the pipeline has no single AI call-path, so the uniformity guarantee is held at the writer, not the transport (0037). Like the other interchanges (record format [0019](../decisions/0019-record-interchange-format.md), digest format [0027](../decisions/0027-digest-interchange-format.md), brief format [0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)), it is versioned: a breaking change bumps the integer. Because the store is append-only, `schema_version` is a per-row column - rows written under different versions coexist, so a bump needs no migration.

## The row

| Column | Group | Description |
|--------|-------|-------------|
| `schema_version` | identity | `anomalica/ai-ledger/1`. Per-row, so versions coexist. |
| `id` | identity | Row identifier. |
| `timestamp_start`, `timestamp_end` | identity | Call start and end (ISO 8601). |
| `duration_s` | identity | Wall-clock duration of the call. New instrumentation for the GPU/CPU paths (see below). |
| `component` | attribution | `ingester` / `digester` / `assimilator` / `assembler`. Threaded from the caller. |
| `operation` | attribution | The AI/compute operation (enum below). Threaded from the caller. |
| `target` | attribution | What the call acted on - `content_hash` / record `friendly_name` / `node_id` / page slug, as applicable. Threaded from the caller. |
| `transport` | execution | `subscription` / `api` / `gpu` / `cpu` (enum below). |
| `model_id` | execution | Claude alias on the subscription path; versioned id on the metered path (`API_MODEL_MAP`); local model name on GPU/CPU. |
| `model_version` | execution | Dated/version pin where one exists, else null. |
| `outcome` | execution | `ok` / `error`. |
| `retries` | execution | Retries before this outcome. |
| `tokens_in` | usage | `input_tokens`. Null on GPU/CPU. |
| `tokens_out` | usage | `output_tokens`. Null on GPU/CPU. |
| `cache_read` | usage | `cache_read_input_tokens`. |
| `cache_write` | usage | `cache_creation_input_tokens`. |
| `rate_limit_consumed` | reserved | Nullable. Populated when the subscription CLI wrapper exposes a rate-limit/allowance field; nothing reports it today. |

The row also carries per-call billing columns; their definition and the rate detail are tracked privately in the `operations` repository and are not documented here.

## Usage, by transport

Each row records the call's usage and wall-time. Tokens are recorded on the Claude paths (`subscription`, `api`) and are null on the local `gpu` (whisperx / pyannote) and `cpu` (fastembed) paths; `duration_s` is wall-time across all paths (new instrumentation on the GPU/CPU paths). Per-call billing is derived from these and the private `operations` rate detail.

## Enums

**`operation`** (AI/compute-bearing only):

| Operation | Component | Transport |
|-----------|-----------|-----------|
| `pdf_extract` | ingester | subscription / api |
| `transcribe` | ingester | gpu / cpu |
| `diarise` | ingester | gpu / cpu |
| `extract` | digester | subscription / api |
| `consolidate` | assimilator | subscription |
| `corroborate` | assimilator | subscription / api |
| `embed` | assimilator | cpu |
| `assemble` | assembler | subscription / api |

These align to the scheduler's existing job vocabulary (`ingest`/`digest`/`synthesise`/`assemble`/`embed`/`corroborate`/`import`); the ledger splits `ingest` into the finer `pdf_extract`/`transcribe`/`diarise` and names `digest`'s AI call `extract`. Deterministic stages that make no AI/compute call (`synthesise`, `coverage`, `reclassify`, `import`, `search`) do not appear.

**`transport`**: `subscription`, `api`, `gpu`, `cpu`.

**`component`**: `ingester`, `digester`, `assimilator`, `assembler`.

## Relationship to other stores

- **Not the knowledge graph.** Distinct from the assimilator's `knowledge.db` / `infrastructure.db` (domain content, regularly dropped and rebuilt - which would wipe a ledger). The assimilator's `infrastructure.db` holds infrastructure *claims*, not operational telemetry; the names are unrelated.
- **Partially supersedes `processing.json`.** The workbench runner's per-job state file keeps job orchestration (on/failed/margin, outcome, GPU job records); the per-call token/cost stats move to the ledger, and the Schedule view joins the two.
- **Provenance, complementary to 0010.** 0010's `brief_hash` audits WHAT a page was built from; the ledger's `model_id`/`model_version` per `target` audits WHICH model produced it.

## Filled as it lands

The schema is scaffolded now and populated as the shared writer is wired in at each emission site. The five sites and their gaps (assembler discards usage today; the GPU path measures no wall-time today) are in [0037](../decisions/0037-ai-operation-ledger.md). `rate_limit_consumed` stays null until the CLI wrapper exposes the field.
