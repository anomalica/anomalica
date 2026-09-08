# Pick the densest signal, not the biggest

Choosing an instrument by the ABSOLUTE amount of signal it carries, rather than
by signal per unit of cost, picks the slowest and most expensive case almost
every time. It is not a judgement error; it is reading the wrong column.

## What it cost

A model comparison needed records with dense reviewer highlights, because
recall is measured against them. The two records with the MOST highlights were
chosen: 291 and 503. They are also the two longest things in the corpus, 41,792
and 40,046 words, and a single extraction of one takes about two and a half
hours. Nine cells came to roughly twenty-two hours and would not have finished
inside the window at all.

The right column was highlights per word. A 10,001-word record carried 73
highlights and a 4,609-word record carried 43 - the same human signal density,
at a fifth and a twentieth of the runtime. The comparison did not need hard
records. It needed measurable ones.

## The same shape elsewhere

- Recall itself once rewarded verbosity, because coverage counted a character
  once per claim that quoted it rather than once in total. Bigger output scored
  higher without being better. Same error one level down: counting the amount of
  a thing rather than its density against what it is being measured for.
- A guard measured the largest enum in a schema because that was where the
  failures had been seen, while the variable was the node directory that
  travelled in the prompt as prose.

## The cheaper half: ask what already exists

Before planning generation, ask whether the artefacts are already on disk.

In the case above, once the record choice was corrected, most of the grid
turned out to exist already: one record carried the full model trio and an
effort arm, the other was missing a single cell. Ten hours of planned
subscription spend collapsed to one run and a query. Neither the component
doing the work nor the one directing it asked "do we already have this" before
designing the batch.

The check costs one command. It is worth making it the first step of any
comparison, not because generation is expensive - though it is - but because a
regenerated artefact is a NEW sample, and comparing a fresh run against an
existing one silently adds run-to-run variance to whatever is being measured.

## Related

- [reading-a-model-comparison](reading-a-model-comparison.md) - the noise floor
  that makes a small difference meaningless, and the rule that one record
  cannot carry a recall finding.
- [the-guard-eats-its-own-experiment](the-guard-eats-its-own-experiment.md)
- [absence-is-not-a-verdict](absence-is-not-a-verdict.md)
