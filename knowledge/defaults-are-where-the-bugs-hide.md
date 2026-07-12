# Defaults are where the bugs hide

A note from the ADR 0044 session (2026-07-12), in which four separate safety bugs were found
in one afternoon across the digester, assimilator and assembler. Every single one was a
**default** - the branch that fires when nothing matches - and not one of them was caught by
reasoning. All four were caught by running something.

## The pattern

Each bug had the same shape: a rule was written as a list of danger signals, and anything
matching no signal fell through to the permissive branch.

| Rule | The default that fired | What it did |
|------|------------------------|-------------|
| Independence of two claims | key on speaker, else record | Ten podcasts relaying ONE anonymous email counted as ten independent attestations. Corroboration rewarded repetition of a rumour. |
| "Is this claim's attribution load-bearing?" | no danger signal found -> conduit | A claim of UNKNOWN provenance rendered as a bare fact. 336 null-attestation testimony claims. |
| "Did extraction inline the attribution?" | model declares `false` -> bare_ok | A model told to inline an anonymous attribution, that simply didn't, published the rumour as fact. The original bug, re-entered through the field built to fix it. |
| Claim dedup identity | key on claim text | The later, better-attributed assertion of a proposition was discarded in favour of the earlier bare one. |

In every case the author had reasoned carefully about the branch they were *thinking* about,
and never looked at the branch that fires when nothing matches. As the assimilator put it:
defaults are invisible to that kind of reasoning.

## Why reasoning does not find these

Two authors (both Opus) independently reasoned their way into the *same inverted default*,
forty minutes apart, in two different repos - one of them having just argued the correct
polarity to the other for a different subsystem. Arguing harder produced more confident wrong
answers. What found them:

- an assertion that failed when run,
- a `SELECT` over 5218 rows,
- a count over 5947 brief claims,
- a deterministic re-alignment that contradicted a stored field.

A confident causal story is not evidence. Three times in this session a story was built on a
corrupt or misread field and only execution disproved it.

## The rules that came out of it

1. **Name the default explicitly, in code.** If a rule is a list of danger signals, write down
   what happens when none match - and make that the safe branch. A default that is never
   written down is never reviewed.

2. **Absence of a danger signal is not evidence of safety.** "We don't know where this came
   from" must never resolve to "safe to publish". Unknown fails closed.

3. **Make the safe direction the cheap one.** Where two errors are not equally costly, the
   design should make the expensive error hard to reach. A wrong "the text names its source"
   is harmless prose; a wrong "it doesn't need to" publishes a rumour as fact - so one is
   trusted and the other is vetoed.

4. **One rule, one implementation.** The load-bearing rule lived as prose in three repos and
   drifted to fail-open in two of them within a single session. It now lives in one function in
   `anomalica-common` that all three call, so a future disagreement is a failing test rather
   than a divergent render.

5. **Don't derive a property of a thing from metadata about the thing.** Whether a sentence
   names its source is a fact about the sentence. Deriving it from `origin_kind` and
   `attestation` means the derivation can disagree with the actual words. The component that
   wrote the sentence declares it; everyone else reads.
