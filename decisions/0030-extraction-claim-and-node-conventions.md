# 0030 - Extraction claim and node conventions (units, attestation, anchoring, Q&A, location, portability)

Status: accepted
Date: 2026-06-14
Supersedes/amends: refines the claim/node rules implied by 0011 (claims as atomic
unit), 0023/0026 (person naming), 0027 (digest interchange format); does not change
the schema version.

## Context

The digester moved from the Claude Code subscription onto the metered API, making the
model a real cost lever. We tested whether the cheap Haiku model can do extraction
well enough to rebuild dense, well-cited articles, tuning Haiku and Sonnet prompts
against a hand-built ground truth for one interview record (the 2021 60 Minutes "Navy
pilots describe encounters with UFOs"). Doing so forced several claim/node conventions
that were previously implicit, inconsistently applied, or wrong in the prompt. This
record fixes them so they survive beyond the tuning session.

The downstream contract is unforgiving: the assembler invents no facts (0008) and
writes neutral prose (0007), so a fact not extracted is lost forever and a
mis-extracted token ships corrupted. Extraction quality is the lever for both coverage
and fidelity.

## Decisions

1. **Units: SI only in claim text, with full unit names.** The `content`/`text` field
   uses metric SI spelled out ("kilometres per hour", "metres", "kilograms"), never
   abbreviations and never imperial - not even in parentheses. The original imperial
   value survives only in `original_excerpt` (the verbatim quote). Preserve the
   source's precision and hedges ("about", "approximately"); never fabricate precision.

2. **Attestation is optional.** Omit `attestation` for plain narration, framing, or a
   bare fact with no evidential stance; set it only when there is a genuine stance, and
   with respect to the EVENTS described (a person briefed on an event is second_hand
   about it). Previously the field was required and the parser defaulted missing/invalid
   values to `first_hand`, which manufactured "narrator-as-eyewitness" errors. The DB
   column is now nullable end to end (models, import, scoring, markdown all tolerate a
   null). Existing databases need a one-off migration to drop the NOT NULL constraint.

3. **Assertion, not reported speech.** The claim text IS the fact. A reporting-verb
   anchor naming the speaker ("X stated/said/noted/confirmed that ...") is forbidden -
   the speaker is already in the structured `speaker` field. Two correct forms: (a) when
   the speaker merely relays a fact about something else, drop the name and state the
   bare fact; (b) when the speaker is the actor/observer/opinion-holder, name them as
   the SUBJECT with a substantive verb ("David Fravor observed ...", "Ryan Graves
   considers ..."). The full natural-order name in claim text is still required when the
   person is a participant, because the assembler uses it to resolve pronouns when a
   claim is read in isolation.

4. **Question-and-answer handling.** The claim is the ANSWER, attributed to the
   answerer; a leading question that contains the fact does not make the interviewer the
   source. For a Q&A-derived claim the verbatim quote MUST contain both turns, each
   speaker named, so the quote alone supports the claim; the location spans both turns.

5. **Location format.** `location_in_record` carries the most precise span the source
   allows. For audio/video that is an `HH:MM:SS.D-HH:MM:SS.D` timestamp RANGE with an
   ASCII hyphen (a range, not a point - an assertion spans seconds, and a Q&A claim
   spans question and answer). The schema field stays free-form for back-compat; this is
   a prompt-level convention.

6. **Place node names carry no locational qualifier.** "USA, California, San Diego",
   never "San Diego (vicinity)/(offshore)". The vicinity nuance belongs in claim text.
   Bare countries/regions/operating-areas are not place nodes; geography lives in the
   claim text.

7. **Node completeness.** The nodes pass must sweep every type, including the
   easily-missed: the central phenomenon as a TOPIC (e.g. "Unidentified Aerial Phenomena
   (UAP)"), military branches, legislative bodies and committees, schools/academies, and
   named aircraft/vehicle/vessel types as OBJECTS ("F/A-18").

8. **Per-model prompts.** Haiku and Sonnet carry separate prompts
   (`DIGESTER_NODES_PROMPT_FILE` / `DIGESTER_CLAIMS_PROMPT_FILE` override the defaults).
   Haiku needs more forceful, example-heavy rules (hard atomicity numeric limits, an
   explicit "emit the obvious entities" sweep); Sonnet follows the lean default.

## Result (one interview record, graded against ground truth)

| model  | node recall | claim recall | claim defects |
|--------|-------------|--------------|---------------|
| Sonnet | 1.00        | 0.95         | 0 merged, clean |
| Haiku  | 0.90        | ~0.95        | 1 merged, a few vague |

Both meet the bar. Sonnet is the benchmark (perfect node recall, no tuning beyond the
defaults). Haiku is viable at ~1/3 the cost; its residual weakness is inconsistently
dropping 2-3 organisation nodes even when named in the prompt, and over-emitting a
couple of background regions as places. End to end the pipeline works: a Sonnet digest
imported into a fresh graph (34 nodes, 94 claims) assembled into a 5-paragraph,
20-reference Nimitz-encounter article with SI units in prose, original units preserved
in quotes, timestamp-range citations, and claim-id traceability, passing the assembler's
date-fidelity guardrail.

## Adversarial note

Ground truth is not automatically right. During tuning, Haiku dated the UAP Task Force
to August 2020 where the hand-built ground truth said 2021; Haiku was correct (the
segment aired May 2021, "this past August" = 2020). The ground truth was fixed. The
LLM-based claim-recall grader is noisy and undercounts; verify key facts directly.

## Open follow-ups

- Existing-DB migration to make `attestation` nullable (fresh DBs already are).
- `preserved_facts` (0027 draft) remains the highest-value fidelity lever - emit the
  exact source tokens deterministically so the assembler cannot corrupt them.
- Node grader (`benchmarks/runner.py`) loose-match still keys off a 0.6 token-coverage
  threshold; fine for now, revisit if it mis-grades longer event/document names.
- Extend ground truth to 3-5 records across the type spectrum (short official
  statement, congressional testimony, dense book chapter) per the orientation guidance.
