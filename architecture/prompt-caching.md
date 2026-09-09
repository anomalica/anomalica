# Prompt caching

How to send a record to a model without paying for it several times over.
Measured 2026-09-09 against Sonnet 5, one 50,000-character document, three tasks.

## The rule

**The document goes in its own cached block. Anything that varies between calls
goes in a separate block after it.**

Putting varying text *after* the document is not enough if it is inside the same
block. A cache entry is the whole block; change one character and none of it is
reused.

| shape | cache write | cache read | billable input |
|---|---|---|---|
| no cache breakpoint | 0 | 0 | 57,389 |
| varying text inside the cached block | 57,790 | **0** | 72,266 |
| varying text in a separate block | 19,094 | 38,188 | **28,228** |

Getting this wrong is worse than not caching at all: the middle row pays the
1.25x write premium on every call and never earns a read.

The saving grows with the number of passes over one document. Three passes
halve it. The record is written once and read for each pass after that.

## What this project currently does

Measured from the dispatch ledger, one extraction of an 81,520-character record
(about 20,000 tokens):

    input tokens      784,245
    cache read        460,976
    cache write       323,251

**Thirty-eight times the document, for one record.** Caching is doing some work,
but 323,000 tokens are still being written each run, which means the cached
prefix changes between calls.

Three causes, in order of size:

**Chunking.** The claims pass cuts a record into 20,000-character pieces, so a
long record has eleven separate prefixes instead of one, and nothing is shared
between them. The chunk size began as a workaround for Haiku 4.5 timing out on a
50,000-character chunk inside the 900-second CLI limit. Sonnet 5 does not fix
that - see "what actually limits chunk size" below.

**The subscription path has no breakpoint.** `_call_api_doc` in
`anomalica-common` sets `cache_control` correctly. `_call_cli_doc`, which is
what actually runs, builds one flat string of preamble, document and task and
hands it to `claude -p`. Whatever caching happens there is the CLI's own and we
do not control where the boundary falls.

**Each pass re-sends the document.** Nodes, claims, and any later pass each send
it again. They should share one cached prefix.

## The context figure the code was set from was wrong by 5x

`extract.py` said "Sonnet's 200K context" and caps a chunk at 150,000
characters. Sonnet 5 and Opus 5 both have a **1,000,000-token context window and
128,000-token maximum output**.

What that changes, measured across all 332 records in the store (materialised
size, timestamps and notes stripped):

| materialised size | records | share |
|---|---|---|
| median | 53,451 chars | - |
| over 150,000 chars | 70 | 21% |
| over 400,000 chars | 20 | 6% |
| largest | 2,255,883 chars | *Beelzebub's Tales* |

**Four records in five fit in a single call today** and are being cut up for no
reason: the 217,109-character Doty interview is 54,000 tokens, roughly a
twentieth of the window, and its claims come to perhaps 60,000 output tokens,
inside the 128,000 limit.

The remaining fifth are books. The largest is about 560,000 tokens - still
inside the context window, but its claims would run well past the output
ceiling. **Splitting is still needed at the top of the range; the output limit
decides where, not the context window.**

## What actually limits chunk size: wall clock, not tokens

Measured 2026-09-09. A 50,000-character claims chunk from the Doty interview,
the real claims prompt with a 167-node directory, Sonnet 5 via `claude -p`, run
twice:

| run | elapsed | claims returned |
|---|---|---|
| 1 | 507 s | 112 |
| 2 | 681 s | 70 |

`ANOMALICA_CLI_TIMEOUT_S` defaults to 900. Those runs used 56% and 76% of it,
and two identical calls differed by 174 seconds. **A 50,000-character claims
chunk does not have safe headroom under the current timeout**, and a whole
217,000-character record in one call is about four times run 2.

This corrects the earlier note here, which said Sonnet completed the same chunk
in 110 seconds. It does not.

The consequence: the token argument for one call per record is sound and the
scheduling argument is not. Raising `CLAIMS_CHUNK_MAX_CHARS` requires raising
`ANOMALICA_CLI_TIMEOUT_S` with it and measuring a worst case, not just observing
that the context window is large. The cache saving is real but it is not free.

## What chunking costs beyond tokens

- Run-to-run variance. Three identical runs spread 6.5 points of recall on a
  three-chunk record and 1.0 point on a single-chunk one; the divergence happens
  at boundaries, where each run carries a different node directory forward.
- Ordering. An account is a stretch of narration and routinely straddles a
  boundary; a pass that sees one chunk cannot order across the join. The
  abducted-sergeant account in the Doty interview has its two halves in chunk 5
  and chunk 6, and the speaker tells the end first.

## Minimum cacheable prefix

4,096 tokens on Haiku 4.5 and Opus 4.8. Below that nothing caches and there is
no error - `cache_creation` simply reads 0. A whole record clears it; a short
web page may not.
