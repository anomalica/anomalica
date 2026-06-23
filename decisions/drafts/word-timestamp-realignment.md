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
   strip them, so the model reads roughly 2.8x the real
   content as pure noise - and any body-length-based run sizing
   over-estimates by 2-3x for word-timestamp records as a result.

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
- **Re-alignment is MORE accurate than the model's inline timestamps, not just a
  substitute.** The single navy case that disagreed with the model's `location`
  by >10s was checked against the source: the quote is verbatim at 08:06.3
  (486.3s), exactly where the aligner placed it at coverage 1.00, while the
  model's inline location (475.9) pointed to the wrong sentence 10s earlier. The
  aligner anchors to the verbatim text position; the model only guesses. So the
  "agreement with the model" metric undersells the aligner where the model itself
  was off, and correcting such inline errors is an argument FOR re-alignment
  beyond enabling deep-links.

## Decision

1. **Strip `{{t:}}` word tokens before extraction; preserve a word->timestamp
   map.** The digester never sees the tokens; its input is the clean body
   automatically. Two carriers are on the table (see open questions):
   (a) strip inline in the digester, building the map in memory; (b) the ingester
   emits a clean body plus a committed `words.json` sidecar. (b) is the converged
   direction and moots the in-memory map and chunk-offset bookkeeping; (a) is the
   fallback. Either way, the two sub-points below hold.

   1a. **One canonical `clean_body()`, shared - the digester never reimplements
   stripping.** The ingester's `verification.py` already draws cloze challenges
   from a stripped view (`_strip_annotations`), not the raw body. To keep the
   digester's extraction view byte-identical to the cloze source (or
   proof-of-possession answers break), that function moves to a shared
   `clean_body()` in the ingester's `shared/`, imported by both verification.py
   and the digester. Its exact behaviour is pinned here and in record-format.md
   so neither side can drift: strip the YAML frontmatter; replace each
   HTML-comment annotation (`<!-- ... -->`, including `<!-- speaker: X -->`) and
   each inline `{{...}}` annotation (`{{t:}}`, `{{redacted}}`, `{{classification}}`)
   with a SINGLE SPACE; strip the line-leading `HH:MM:SS.D` prefix to nothing; do
   NOT collapse whitespace (so a double space can remain where an annotation sat -
   this is part of the contract, not a bug). The ingester owns this and will land
   it with the v2 render work.

   1b. **Sidecar schema `anomalica/words/1`** (converged between the ingester and
   anomalica/anomalica), stored at `store/{hash}.words.json`. Segment-nested for
   readability:

   ```
   {schema, record_hash, segments: [{ts, start, end, words: [{w, start, end}]}]}
   ```

   The binding is flat word order: flattening every segment's `words` in document
   order yields a `[{w, start, end}]` array that is 1:1 with the clean body's
   spoken-word tokens - exact by construction, because the v2 body is rendered by
   joining those same word tokens (body-word-N === Nth flattened sidecar word, no
   count/order drift). So re-alignment maps quote tokens to the flattened sidecar
   array directly. Exact field names are owned jointly by the ingester and
   anomalica/anomalica - this records the agreed shape, not a second definition.

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

6. **Add an optional timestamp-provenance field to digest/1.** Per-claim,
   ADDITIVE to the existing `location` (which stays - PDF/web records use it for
   page refs like "p. 2"; `timing` applies only to audio/video). Shape, agreed
   by both readers (assembler and workbench) independently:

   ```
   timing:
     start: 68.37        # float seconds - the primitive; consumers derive
     end: 70.58          #   HH:MM:SS display and ?t= offsets themselves
     coverage: 1.00      # fuzzy-LCS coverage of the quote vs source
     resolution: word    # word (record/2) | sentence (record/1) | turn (fallback)
   ```

   Optional and additive, so it does not bump the schema version or break
   consumers that ignore it. Per-claim is sufficient (one fact = one claim = one
   quote); no per-quote span is needed now.

   Consumer-confirmed semantics (so the producer and readers agree on what the
   numbers mean):
   - `coverage` is a SOFT confidence signal, not a gate and not a reviewer chore.
     The workbench renders the jump normally at >=0.9, shows an unobtrusive
     "approximate" hint below 0.9, and only flags prominently below ~0.7. It does
     NOT enter Mark's review queue or the digestibility gate.
   - Both readers degrade gracefully: they emit a precise jump-to-moment (the
     workbench seeks its existing player; the assembler builds a `source_url`
     `?t=int(start)` deep-link) only when `coverage` is high and `resolution` is
     word|sentence; for turn-level or low coverage they fall back to the coarse
     `location` string and never emit a confidently-wrong timestamp.

   Duplicate-phrase disambiguation (decision 3) is the digester's alignment
   problem alone: the assembler keys references to claims by exact `claim_index`/
   uuid with no fuzzy quote->transcript matching, so there is no shared matcher
   to build - only the shared neighbour-context principle.

## Consequences

- Extraction input for record/2 shrinks once stripping lands (the `{{t:}}` markers no longer inflate the body the digester processes).
- Workbench and site gain jump-to-moment deep-links into audio/video.
- New per-claim timing feeds evidence scoring.
- Byte-consistency with the cloze source is handled by the shared `clean_body()`
  (decision 1a) - the ingester owns it, the digester imports it; no drift by
  construction.
- Consumer field shape is settled: assembler and workbench both confirmed
  `timing: {start, end, coverage, resolution}`, per-claim, additive to
  `location` (decision 6). Both degrade gracefully on low coverage.

## Open questions

- **Strip inline (digester) vs clean-body + `words.json` sidecar (ingester).**
  The one remaining open question, and not a separate decision: it is the same
  call as the pending v2 record-format question with Mark (the clean-body +
  committed `words.json` sidecar recommendation). Decision 1's carrier resolves
  when that is answered - the sidecar is the converged direction (the ingester
  has the `anomalica/words/1` schema ready); inline strip is the fallback only if
  the format stays inline.
- Hardening the duplicate-phrase disambiguator (the prototype's naive head-token
  probe did not flag the one real collision) - implementation detail of decision
  3, not a blocker for acceptance.
