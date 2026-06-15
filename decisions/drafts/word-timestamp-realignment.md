# Word-timestamp stripping and quote re-alignment

Date: 2026-06-15
Status: draft

## Context

record/2 (`schema: anomalica/record/2`, `word_timestamps: true`) carries
word-level timing: an inline `{{t:SECONDS}}` token precedes every word in the
body, on top of the sentence-level `HH:MM:SS.D` prefix and the
`<!-- speaker: ... -->` comments (see the inline-metadata-format draft).

Two problems follow for the digester:

1. **The tokens are noise the model should never see.** Measured on a 39-minute
   record/2 (StarGate, content_hash 2399fe4e...): 5,424 `{{t:}}` tokens make up
   **64% of the body characters**. Today `record_parser.parse_record` does not
   strip them, so the model reads - and we pay for - roughly 2.8x the real
   content as pure noise. The cost-pre-flight gate (0033) sizes the run on body
   length, so it also over-estimates 2-3x for word-timestamp records.

2. **We still want the timing.** Per-claim and per-quote timestamps let the
   workbench and site deep-link to the exact moment in the audio/video, and feed
   the evidence-scoring model (algorithmic-evidence-scoring draft).

The plan: strip the tokens to a clean-text view for extraction, then re-align
the model's emitted quotes/claims back to word timing afterwards. The uncertain
part was whether the re-alignment would work, because the model normalises text
(British spelling, expanded contractions, "u.s" -> "U.S.", merged Q&A turns), so
an emitted string is rarely a verbatim substring of the source.

## Evidence (zero-spend prototype)

`digester/workspace/benchmarks/align_prototype.py` tested the matching in
isolation with no metered run, reusing the navy digest's existing model-assigned
`location` per claim as a reference: strip it, re-align the quote with unanchored
fuzzy token-LCS, measure agreement.

- **Aligning on the verbatim quote** reproduces the model's inline location:
  86.8% exact (<0.05s), 92.1% within 2s, 98.7% within 10s, at 100% coverage
  (>=0.9). The feared normalisation problem does not bite the quote - a quote is
  near-verbatim by nature.
- **Aligning on the paraphrased text instead** collapses to 11.8% coverage>=0.9
  and 10.5% within 2s. So alignment must use the quote, never the paraphrase.
- **Every claim carries a quote.** All 98 navy claims have both a verbatim quote
  and a location. The quote IS the anchor; no anchor-span prompt change and no
  metered re-extraction are needed to align.
- **Model-independent.** The verbatim-excerpt field is 100% coverage>=0.9
  (mean 1.00) for Haiku, Sonnet and Opus alike (imminent ch8 compare set); the
  paraphrase is unalignable for all three. Haiku copies quotes as faithfully as
  the larger models - it stays a viable cheap choice for a corpus backfill.
- **Word-level mechanism works end to end** on a real record/2: strip `{{t:}}`,
  keep a parallel word->timestamp map, align the quote -> word-level start/end
  ("lateral transition" -> 72.20-72.70s, coverage 1.00).

## Decision

1. **Strip `{{t:}}` word tokens before extraction; preserve a word->timestamp
   map.** The digester never sees the tokens. The cost estimate then reflects the
   clean body automatically. The map (clean-text word index -> source seconds) is
   built at strip time and carried through to re-alignment. Two carriers are on
   the table and this is the open question below: (a) strip inline in the
   digester via a reversible helper, building the map in memory; (b) the ingester
   emits a clean body plus a committed `words.json` sidecar, so the body arrives
   clean and timing lives in the sidecar. (b) is the converged direction and
   moots the in-memory map and the chunk-offset bookkeeping; (a) is the fallback.

2. **Re-alignment is a deterministic post-process, not a model task.** For each
   claim: tokenise its verbatim quote, fuzzy-LCS against the word->timestamp map,
   emit `(start, end)` word timestamps. No prompt change, no re-extraction; it
   runs over existing and future extraction output alike.

3. **Disambiguate duplicate phrases by context window.** Short quotes match in
   several places (the navy prototype's single >10s miss matched a repeated
   "...white tic-tac-looking object..." at the wrong occurrence). Prefer the
   occurrence whose neighbouring source words also match. This is the same class
   as the assembler's citation-matching problem (short strings, multiple sites);
   solve it once and share the approach.

4. **Emit a coverage/confidence score per aligned claim.** Keep the LCS coverage
   in the output. It is the signal the evidence-scoring model wants, and it lets
   the workbench surface low-confidence alignments for review rather than
   trusting them silently.

5. **Coarse fallback for the rare quote-less claim.** Align to the speaker turn
   (sentence/diarisation granularity). Carry only what the labels support: never
   synthesise attestation or named attribution beyond the diarisation. Turn-level
   attribution is only meaningful on reviewed records, where the anonymous
   Speaker 1/2/3 labels have been replaced with real names during review.

6. **Add an optional timestamp-provenance field to digest/1.** Per-claim/quote
   `(start, end, coverage)`. Optional and additive, so it does not bump the
   schema version or break consumers that ignore it.

## Consequences

- Cost gate (0033) auto-corrects for record/2 once stripping lands.
- Workbench and site gain jump-to-moment deep-links into audio/video.
- New per-claim timing feeds evidence scoring.
- Consumers to coordinate on the field shape before this is accepted: the
  assembler (reads timing for citations) and the workbench (surfaces low
  confidence, renders deep-links). The clean-text view must stay byte-consistent
  with the ingester's `verification.py` cloze source, or proof-of-possession
  answers break.

## Open questions

- **Strip inline (digester) vs clean-body + `words.json` sidecar (ingester).**
  This is not a separate decision: it is the same call as the pending v2 record
  format question with Mark (the clean-body + committed `words.json` sidecar
  recommendation). Decision 1's carrier resolves when that is answered - the
  sidecar is the converged direction; inline strip is the fallback only if the
  format stays inline. Affects who owns the word->timestamp map and whether
  chunk-offset bookkeeping is needed at all.
- Exact field name and shape for the digest/1 provenance addition.
- Hardening the duplicate-phrase disambiguator (the prototype's naive head-token
  probe did not flag the one real collision).
