# Prompt caching

How to send a record to a model without paying for it several times over.
Measured 2026-09-09 against Sonnet 5, one 50,000-character document, three tasks.

## The shape

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

## Rules

Six rules. The first four are checkable; the last two are why the others were
wrong for a year.

**1. The source text comes FIRST. Instructions come after it. Anything that
changes between requests comes last.** Not "the source text and the
instructions, then the varying part" - the instructions go after the text too,
even though they never change within a pass. A record is read by more than one
pass (nodes, then claims) and each pass has different instructions; put them
first and the two passes share no prefix, so the same document is stored twice.
Put the document first and the second pass reads what the first one stored.

A cache entry is everything up to the breakpoint. One changed character anywhere
in it and none of it is reused, so the order is simply most-stable to
least-stable and nothing else.

**2. Never put an accumulating list in front of the source text.** The
found-so-far list, the exclude list, the node directory - these grow with every
round, and in front of the text they make the text look new every round. This
is not a missed optimisation, it is worse than no caching at all: writing costs
double the normal rate and reading costs a tenth, so a prefix that never
survives pays the expensive direction on every call and never earns the cheap
one. Both extraction passes did this until 2026-09-09.

**3. Cut a source only to bound what rides along in each request. Never to make
it fit.** Cutting does not reduce the number of requests - that is set by how
many claims the model returns per reply, which is a property of the model. A
book yielding 3,185 claims takes about 120 requests whole or in forty pieces.
What cutting changes is the payload on each of those requests. Deciding chunk
size from a context window is the mistake that produced every constant in
`extract.py`; decide it from what each request has to carry.

**4. Read `cache_write` against `cache_read` in the ledger after any prompt
change.** Writes should be a small fraction of reads: the text is written once
and read back on every round after. If the two are within sight of each other,
the prefix is changing and rule 1 or 2 is broken somewhere. On *Surviving
Death*: 15,841,159 written against 14,847,413 read, over 120 calls. That
one-to-one ratio is the signature.

**5. Record what a provider does in the policy file, not in a comment.**
`anomalica/architecture/model-policy.yaml` holds a `caching` block: per route,
whether caching is automatic or needs a marker, where the marker goes, the
lifetimes offered, what storing and reading cost as multiples of that model's
own input price, the smallest prefix that caches at all, and the date it was
checked. Transports read from it (`Policy.caching_ttl`,
`Policy.caching_minimum_tokens`). An empty entry means NOBODY HAS CHECKED, not
"no caching here" - unchecked routes are marked `mode: unknown` on purpose, so a
missing key is a route somebody added without recording its behaviour. The site
renders the block, which is what stops it going stale unnoticed.

**6. Re-measure a model limit before setting a constant from it.** Every chunk
size in this project descends from "Sonnet holds 200,000 tokens", which was
true once. The models now hold 1,000,000. Nothing re-checked it, so the
constants stayed, the reasons in the comments stayed, and each new constant was
derived from the last one. A figure copied from a comment is not a measurement.

## Where the 132,000 tokens per call went

*Surviving Death*, 1,133 nodes, digested 2026-07-31, 15,841,159 tokens written
over 120 calls. Traced 2026-09-09 by measuring each component:

| component | tokens | share |
|---|---|---|
| session furniture the CLI loads (see below) | ~64,000 | 48% |
| node directory, in the prompt | 16,094 | 12% |
| the chunk of the book itself | ~12,500 | 9% |
| node-name enum, in the JSON schema | 11,320 | 9% |
| claims instructions | 7,219 | 5% |
| exclude list and remainder | ~21,000 | 16% |

**Half of it was never ours.** `claude -p` loads an interactive session's worth
of context before reading a word of the prompt: connected MCP servers (~31,700),
the CLAUDE.md files (~11,000), built-in tool descriptions and settings
(~16,200). `--strict-mcp-config` and `--restricted` strip it. An earlier note in
`transport.py` recorded the symptom - "a control call carrying a 30-character
prompt still wrote 32,486" - without finding the cause.

Every component that builds its own `claude` command carried it. Measured
2026-09-09, each against that component's own command with a six-word prompt:

| call | before | after |
|---|---|---|
| digester, document on stdin | 63,799 | 6,095 |
| digester, document via the Read tool | 132,626 | 13,015 |
| assembler, writing a page | 69,379 | 5,140 |
| ingester, extracting a PDF page | 132,626 | 39,077 |

A path that uses a file tool keeps more, because the file tools stay loaded -
that is what those paths are for. `--restricted` confines them to the working
directories, so `--add-dir` has to name the directory holding the file.
`--dangerously-skip-permissions` cannot be combined with `--restricted` and is
not needed once `--tools` is empty or `--allowedTools` names the one tool used.

**The node names go out twice.** 16,094 tokens as a directory in the prompt and
11,320 as an enum in the JSON schema: 27,414 tokens of the same 1,133 names in
two formats on every call. Both are stable for the life of a record, so with the
prefix fixed they are written once and read cheaply - but they are the reason a
node-dense record costs what it does, and a catalogue-shaped source with 3,017
nodes reaches the CLI's per-argument ceiling on the enum alone.

**What the book should now cost.** Stable prefix per chunk of about 53,200
tokens, written once and read on later rounds: roughly 3.2M token-equivalents
against the 33M it billed. About ten times, at list price about $6 against $66.
Not yet confirmed by a run - the weekly allowance was at 88%.

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

**Four records in five fit in a single call on tokens**: the 217,109-character
Doty interview is 54,000 tokens, roughly a twentieth of the window, and its
claims come to perhaps 60,000 output tokens, inside the 128,000 limit. Fitting
on tokens is not the same as fitting in the time budget - see the next section.

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
