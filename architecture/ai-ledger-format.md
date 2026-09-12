# AI-operation ledger format

The ledger is the operational record of every AI or compute attempt the pipeline makes - one durable row per attempt, including a pre-call refusal after a route and payload have been selected, recording its provenance and usage. Schema `anomalica/ai-ledger/1`. SQLite, at `~/.local/share/anomalica/ai-ledger.db` (env-overridable via `ANOMALICA_LEDGER_DB`, or `ANOMALICA_DATA_DIR` for the directory). See [decision 0037](../decisions/0037-ai-operation-ledger.md) for the why.

The producer is a single shared writer in anomalica-common, called at each emission boundary - the pipeline has no single AI call-path, so the uniformity guarantee is held at the writer, not the transport (0037). Like the other interchanges (record format [0019](../decisions/0019-record-interchange-format.md), digest format [0027](../decisions/0027-digest-interchange-format.md), brief format [0036](../decisions/0036-synthesise-stage-brief-as-writer-input.md)), it is versioned: a breaking change bumps the integer. `schema_version` is a per-row column so rows written under different versions coexist. SQLite table changes still require an ordinary database migration; row versioning does not remove that requirement.

## The row

| Column | Group | Description |
|--------|-------|-------------|
| `schema_version` | identity | `anomalica/ai-ledger/1`. Per-row, so versions coexist. |
| `id` | identity | Attempt identifier and SQLite primary key. Created before any provider invocation and never reused. |
| `attempt_group_id` | identity | Optional identifier shared by retries of one logical operation. Each retry still has its own row and `id`. |
| `attempt_number` | identity | One-based position within `attempt_group_id`; null when the operation has no retry group. |
| `timestamp_start`, `timestamp_end` | identity | Attempt start and end (ISO 8601). End is null only while the durable row is pending. |
| `duration_s` | identity | Wall-clock duration of the attempt; null while pending. New instrumentation for the GPU/CPU paths (see below). |
| `component` | attribution | `ingester` / `digester` / `assimilator` / `assembler`. Threaded from the caller. |
| `operation` | attribution | The AI/compute operation (enum below). Threaded from the caller. |
| `target` | attribution | What the call acted on - `content_hash` / record `friendly_name` / `node_id` / page slug, as applicable. Threaded from the caller. |
| `transport` | execution | `subscription` / `openai-subscription` / `openrouter` / `api` / `gpu` / `cpu` (enum below). |
| `transport_implementation` | execution | Selected client/runner, for example `opencode`. Optional generally; required for an `openai-subscription` attempt. This is not the allowance-meter implementation. |
| `transport_version` | execution | Observed executable version. Optional generally. Required for a passed `openai-subscription` qualification; nullable while pending or on refusal when it could not be observed. |
| `transport_config_sha256` | execution | SHA-256 of the observed selected transport configuration's complete raw bytes. Same conditional requirement and hashing basis as `transport_version`; never substitute the policy's expected hash when observation failed. |
| `model_id` | execution | Route-specific policy id for hosted models; local model name on GPU/CPU. A subscription and metered route to the same model keep distinct ids. |
| `model_version` | execution | Dated/version pin where one exists, else null. |
| `policy_path` | execution | Resolved path selected for the exact policy snapshot. Required for every `openai-subscription` attempt, including a refusal caused by unreadable policy bytes. It identifies the selected file but is not a credential. |
| `policy_sha256` | execution | SHA-256 of the complete raw bytes of the exact model-policy YAML snapshot used for the attempt, with no decoding, normalisation, parsing or canonicalisation. Required for a passed `openai-subscription` qualification; nullable while pending or on refusal when policy bytes could not be read. |
| `qualification_status` | execution | `pending` / `passed` / `refused` / `not-required`. Required for every `openai-subscription` attempt; `pending` is the write-ahead state before qualification completes, and `not-required` is for routes without an execution qualification. |
| `qualification_reason` | execution | Stable refusal code from the enum below. Required when qualification is `refused`; null otherwise. It records no exception text, path, credential or provider response. |
| `provider_started` | execution | Whether the inference process or provider request started. Qualification probes such as version and authentication checks do not count. Required for every `openai-subscription` attempt so pre-call refusal and post-start error remain distinguishable. |
| `submitted_payload_bytes` | execution | Length of the exact submitted user/input payload after UTF-8 encoding. Optional generally; required for every `openai-subscription` attempt. |
| `submitted_payload_sha256` | execution | SHA-256 of those same exact UTF-8 bytes. Optional generally; required for every `openai-subscription` attempt. |
| `outcome` | execution | `pending` / `ok` / `error`. `pending` is the durable write-ahead state and is never a successful result. |
| `tokens_in` | usage | `input_tokens`. Null on GPU/CPU. |
| `tokens_out` | usage | `output_tokens`. Null on GPU/CPU. |
| `cache_read` | usage | `cache_read_input_tokens`. |
| `cache_write` | usage | `cache_creation_input_tokens`. |
| `rate_limit_consumed` | reserved | Nullable. Populated when the subscription CLI wrapper exposes a rate-limit/allowance field; nothing reports it today. |

## Usage, by transport

Each row records the call's usage and wall-time. Tokens are recorded on hosted paths (`subscription`, `openai-subscription`, `openrouter`, `api`) and are null on the local `gpu` (whisperx / pyannote) and `cpu` (fastembed) paths; `duration_s` is wall-time across all paths (new instrumentation on the GPU/CPU paths). Subscription allowance percentages pace dispatch but are route state, not per-call token usage and not a substitute for the model and transport recorded here.

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
| `assemble` | assembler | subscription / openai-subscription / openrouter / api |

These align to the scheduler's existing job vocabulary (`ingest`/`digest`/`synthesise`/`assemble`/`embed`/`corroborate`/`import`); the ledger splits `ingest` into the finer `pdf_extract`/`transcribe`/`diarise` and names `digest`'s AI call `extract`. Deterministic stages that make no AI/compute call (`synthesise`, `coverage`, `reclassify`, `import`, `search`) do not appear.

**`transport`**: `subscription` (Anthropic), `openai-subscription`, `openrouter`, `api`, `gpu`, `cpu`.

`openrouter` is explicit because it is a distinct metered execution and billing route, not an alias for an arbitrary direct provider `api` call. The assembler uses it for provider-qualified models dispatched through OpenRouter.

**`qualification_reason`**: `policy-unavailable`, `policy-invalid`, `implementation-mismatch`, `version-unavailable`, `version-mismatch`, `config-unreadable`, `config-mismatch`, `authentication-unavailable`, `authentication-not-oauth`, `input-too-large`, `config-unsafe`.

For an `openai-subscription` attempt, route selection and final payload construction begin the ledger attempt. A dry run or rejection before either exists is not an attempt. Every later result writes exactly one row. A pre-call refusal has `outcome: error`, `qualification_status: refused`, `provider_started: false`, null usage and one reason code. A qualified request that later fails has `qualification_status: passed`, `provider_started: true`, `outcome: error`, and no qualification reason. Observed fields stay null when their unavailability caused refusal; expected implementation, version and configuration hash are recovered from the exact policy snapshot identified by `policy_sha256`, not copied into observed fields.

Each provider invocation, including each retry, is a separate attempt row. `attempt_group_id` and `attempt_number` correlate retries without aggregating their timestamps, outcomes, payload identity or usage. No retry count is stored on a row.

### Durable attempt lifecycle

Before any inference process or provider request may start, the shared writer inserts the complete known attempt as `outcome: pending`, `provider_started: false` and commits that transaction. If SQLite cannot open, migrate, insert or commit, dispatch fails closed and no provider invocation occurs. Route preflight then either finalises that row as a refusal or continues.

Immediately before crossing the inference boundary, the writer sets `provider_started: true` and commits. Failure to commit again refuses dispatch. The process or request starts only after that commit. A crash after this point may leave a pending row whose `provider_started: true` conservatively means the invocation boundary was reached; it does not claim a response was received.

Finalisation is one conditional transaction from `pending` to `ok` or `error`, filling end time, duration and available usage. It is idempotent: repeating the same final values succeeds without changing the row, while a conflicting second finalisation fails. Final rows are immutable. If finalisation cannot commit after provider execution, the durable pending row remains and the caller reports failure rather than treating the result as publishable.

A crash leaves the durable row `pending`, with its last committed `qualification_status` and `provider_started` values. Pending is never read as success, its output is never publishable, and recovery never retries inference automatically. The writer must not sweep pending rows to error at startup because another process may still own one. A later maintenance action may finalise a pending row as `error` only when it has independent evidence that the owning attempt is no longer running, using the same conditional finalisation rule. Thus a crash can leave qualification or usage unknown, but cannot erase evidence that an attempt was durably admitted or turn an uncertain result into publishable output.

The allowance meter is route state, not inference execution provenance. Its implementation, source observation time and freshness belong to scheduler pool status, not `transport_implementation` and not a per-call allowance-consumption field.

**`component`**: `ingester`, `digester`, `assimilator`, `assembler`.

## Relationship to other stores

- **Not the knowledge graph.** Distinct from the assimilator's `knowledge.db` / `infrastructure.db` (domain content, regularly dropped and rebuilt - which would wipe a ledger). The assimilator's `infrastructure.db` holds infrastructure *claims*, not operational telemetry; the names are unrelated.
- **Partially supersedes `processing.json`.** The workbench runner's per-job state file keeps job orchestration (on/failed/margin, outcome, GPU job records); the per-call token/cost stats move to the ledger, and the Schedule view joins the two.
- **Provenance, complementary to 0010.** 0010's `brief_hash` audits WHAT a page was built from; the ledger's `model_id`/`model_version` per `target` audits WHICH model produced it.

## Filled as it lands

The schema is scaffolded now and populated as the shared writer is wired in at each emission site. The five sites and their gaps (assembler discards usage today; the GPU path measures no wall-time today) are in [0037](../decisions/0037-ai-operation-ledger.md). `rate_limit_consumed` stays null until the CLI wrapper exposes the field.

The current anomalica-common writer is a legacy aggregate JSONL run log, not this canonical per-attempt SQLite ledger. Adding similarly named JSON fields would not satisfy this contract. Production dispatch through `openai-subscription` remains blocked until a shared per-attempt SQLite writer implements the durable lifecycle and conditional fields above for both pre-call refusals and started requests. Historical and non-subscription rows may omit the conditional fields; the shared writer enforces completeness for subscription attempts.
