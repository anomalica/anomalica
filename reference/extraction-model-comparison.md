# Which model extracts claims best?

Measured, not assumed. Every model choice in this project has until now rested on
a single 45 KB video record; this page records what has actually been graded
against a reviewer's own gold, and what has not.

Last updated 2026-08-31.

## The headline, and a retraction

**On chain-heavy gold, Opus leads. The earlier "Opus is worse than Sonnet"
finding does not survive a second record and should not be repeated.**

That claim came from one 45 KB video with 10 highlights, where Opus scored worst
of the Claude tiers. On the Jon Stewart record - 197 reviewer highlights, 109
context chains - Opus is first or tied-first on every axis. Both measurements are
real; they disagree because one record is not a sample.

## NOT YET RUN - read the table above as four models, not as the field

**The four rows are an accident of which runs happened to exist on a record that
has gold, not a considered field.** GLM-5.2 appears because someone ran 5.2
months ago, not because 5.2 was preferred to 5.3. A reader seeing
opus/sonnet/haiku/glm-5.2 would reasonably assume OpenAI was tested and lost. It
was not tested at all.

Never run for extraction against reviewer gold, as of 2026-09-01:

| model | status |
|---|---|
| openai/gpt-5.6-luna | running now |
| openai/gpt-5.6-terra | NOT A CANDIDATE HERE - article-writing tier, different gold |
| openai/gpt-5.6-sol | NOT A CANDIDATE HERE - article-writing tier, different gold |
| qwen/qwen3.8-max | not run - $3.83 |
| z-ai/glm-5.3 | not run - $2.80; only 5.2 has been measured |
| deepseek/deepseek-v4-pro | running now |
| moonshotai/kimi-k3 | not run - $9.26, the dearest in the field |

The blocker is the shared $3/day OpenRouter budget, not a judgement about any of
them. Terra and Sol are excluded on purpose rather than on cost: they are
candidates for ARTICLE WRITING, judged on citation density against entity pages,
not on recall against highlights. Testing them here would measure the wrong
thing.

**The question this sweep exists to answer** is what runs claim extraction if
Claude becomes unusable - the watermarking retrofit is announced, undated and
undetectable, and claim text is published prose. The permitted candidates are
Qwen3.8-max, GLM-5.3, DeepSeek and Luna. A claim that Luna is unfit for claim extraction was made on a public MRCR
score - a synthetic needle-in-haystack task, not this job - and is being settled
by measurement rather than left standing.

## Graded against reviewer gold

Record: `2026-01-02-video-the-alien-interview-tape-might-be-real-jon-stewart`
193 gold units, 101 carrying context chains. Identical production two-pass
prompt across all four, so the model is the only variable.

| model | claims | recall | quote fidelity | coref rate |
|---|---:|---:|---:|---:|
| **opus** | 756 | **0.650** | 0.939 | **0.914** |
| z-ai/glm-5.2 | 663 | 0.629 | 0.936 | 0.875 |
| sonnet | 555 | 0.617 | **0.942** | 0.911 |
| haiku | 471 | 0.437 | 0.776 | 0.783 |

**Read against a ~2-point noise floor.** The same model, record and prompt scored
63.7 and 61.7 on two runs (`digester/workspace/benchmarks/glm-repeat-variance.md`),
so a gap under about 2 points is not a difference.

- **Haiku is decisively worse on this material** - 21 points of recall below the
  others, and the only model whose quote fidelity drops below 0.9. Not a close
  call and not noise.
- **Opus, GLM-5.2 and Sonnet are close.** Opus leads recall by 3.3 points over
  Sonnet, which clears the floor but only just. Fidelity and coref are tied
  three ways.
- **GLM-5.2 reaching Opus-adjacent scores matters commercially**, since it is a
  fraction of the price. On this record it gives up 2.1 points of recall and 3.9
  of coref against Opus.

### Claim count is not capability

Haiku emitted 471 claims and recalled 43.7% of the gold; Sonnet emitted 555 and
recalled 61.7%. Opus emitted the most claims AND had the best recall, but the
ordering does not hold generally - a model can fragment one fact into three and
inflate its count without covering more gold. Score recall against gold, never
raw claim count.

## What the gold measures

The gold is a reviewer's own highlights: a span they drew expecting a claim out
of it. Two properties make it unusually hard and unusually relevant:

- **A highlight expects AT LEAST ONE claim, not exactly one.** Two claims from one
  highlight is a pass. Recall is coverage-weighted per unit, so a model cannot
  game the score by fragmenting, nor be penalised for consolidating.
- **101 of 193 units are context chains** - a later span says "he", and the
  extraction must name the person from an earlier linked span. So this set mostly
  measures cross-passage coreference on long transcripts, which is what separates
  models on hard content and what no public benchmark tests on our material.
  Chains score partial credit: a partly-resolved chain must rank above a wholly
  missed one.

## What has NOT been measured, and why the corpus cannot answer it yet

The gradeable intersection is close to empty, and it is inverted:

| record | highlights | chains | model runs |
|---|---:|---:|---:|
| Jon Stewart | 197 | 109 | 4 |
| Ex-AFOSI / Doty | 263 | 143 | 0 (record unfinished) |
| Raymond Fowler | 73 | 21 | 1 |
| Garry Nolan | 48 | 13 | **0** |
| Coulthart Q&A | 43 | 7 | **0** |
| Oval Office | 22 | 6 | **0** |
| McDonald (Australia) | 11 | 2 | **27** |

**The richest gold has almost no models run on it; the record with 27 models has
almost no gold.** So the corpus supports one properly-graded comparison, on one
record, which is exactly the single-sample problem this page exists to end.

Also untested for extraction: every OpenAI model and every Qwen model. A claim
that Luna is unfit for claim extraction was made on the strength of a public MRCR
score - a synthetic needle-in-haystack task, not this job - and should not be
treated as established.

## Related measurements

- Cost and quote-fidelity across 27 models on one video record:
  `digester/reports/model-comparison.html` (grades coverage against highlights,
  not chains).
- Run-to-run variance: `digester/workspace/benchmarks/glm-repeat-variance.md`.
- Corpus-wide quote verification: `scheduler/backend/quote_audit.py` finds 1,714
  stored excerpts absent from the documents they cite, and the per-model fidelity
  above is the same property measured at extraction time.
