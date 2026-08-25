# Validating embedding spaces

A note from the assimilator's embedding-space defect (2026-07-17), fixed in assimilator `96db78b`. Written up as the class of mistake rather than the incident, because it recurs whenever an embedding model is added or swapped. Bears on the assimilator's clustering, deduplication and corroboration - see also [claims fusion as a robust SLAM back-end](claims-fusion-as-robust-slam.md).

A vector space can be **completely broken for clustering while passing every retrieval benchmark**, and it fails silently: no error, no exception, just confident numbers that mean nothing. It has already happened here once: a quantised model's raw uint8 output scored every pair of texts at cosine ~0.99 regardless of meaning. Assume it will happen again.

## Why retrieval validation cannot catch it

Retrieval metrics - NDCG, recall@k, precision@k - measure **ranking**. Ranking survives any monotone distortion of the metric.

A quantised embedding whose values share a large constant offset (e.g. uint8 output centred on a zero-point) produces vectors that are a small signal riding on a big shared component. Cosine between any two of them compresses toward ~0.99, but the *order* of neighbours is largely preserved. So retrieval still works, benchmarks look healthy, and the model card ships with a good NDCG figure.

Clustering, thresholding, deduplication and corroboration need **absolute** values. A threshold of 0.83 against a space where everything scores 0.99 either merges the entire corpus or nothing. The same vectors that rank fine are unusable the moment a decision is made against a number rather than an order.

**The rule: if a metric is used for absolute decisions, validate it in absolute terms. Order-based validation cannot detect a distortion that preserves order.**

## The probes

Cheap, run them before trusting any new embedding space. They take a minute and would have caught the above immediately.

1. **The spread probe.** Embed a handful of *maximally unrelated* texts (different domains entirely - a nursery rhyme, a physics definition, a recipe). Compute all pairwise cosines and look at the **spread**, not the values. Unrelated text should be well separated (order 0.2-0.4 here). If the whole set lands in a narrow band, the space is dominated by a constant component and is unusable for thresholding.
2. **The empty-string probe.** Embed `""` and compare it against real sentences. It is the sharpest single diagnostic: a meaningful space scores it low against everything. If `"The cat sat on the mat"` vs `""` scores 0.99, the vectors are constant-dominated - full stop, no further investigation needed.
3. **The separation check.** Measure `min(cosine over known same-meaning pairs) - max(cosine over known different-meaning pairs)`. This is the only number that matters for a threshold: it is the width of the window the threshold has to sit in. If it is near zero, no threshold exists and tuning is a waste of time. Report separation, never a single similarity figure.
4. **The self-consistency check.** Embed the same text twice under different conditions (alone vs alongside others; different batch sizes). The vectors must be identical. If they differ, the result depends on request composition - nothing can be cached and no comparison is reproducible.

## The measured null distribution (assimilator, 2026-08-22)

The probes above tell you a space is not broken. They do not tell you what a number
*means* in it. That needs the null distribution - what unrelated pairs actually score -
and until it is measured every threshold and every merge argument is guesswork wearing a
decimal point.

Measured over 6,000 random pairs of live node-name vectors in the current space
(`Qwen3-Embedding-0.6B-onnx-uint8`, `dequant-v1`, pooling disabled):

| statistic | cosine |
|-----------|--------|
| mean | 0.53 |
| standard deviation | 0.09 |
| p50 | 0.53 |
| p90 | 0.64 |
| p99 | 0.80 |
| p99.9 | 0.86 |
| max observed | 0.88 |

**Read every similarity against this table, not against intuition.** In the merge decision
that produced it, three node names for the UAP term scored 0.79-0.93 and the 0.79 was
initially flagged as worryingly low - a reason to doubt the merge. It is the 99th
percentile. Fewer than one random pair in a hundred reaches it. The instinct was inverted,
and only the distribution showed it.

Corollaries worth stating, because each was nearly got wrong:

- **A single cosine is not evidence.** "These scored 0.79" says nothing; "these scored
  0.79, which is p99 in a space whose median is 0.53" is a finding.
- **Nothing scores near 1.0 in a healthy space.** The observed maximum over 6,000 random
  pairs is 0.88. A space where an ordinary pair reaches 0.99 is the degenerate one this
  note was written about.
- **Re-measure after any model, decode-convention or corpus change.** The table is a
  property of the instrument AND of what is in the corpus; it is not a constant of the
  model. Re-running it is a minute's work.
- **Name vectors are not claim vectors.** This table is node NAMES. Claim-content vectors
  will have their own distribution and must be measured separately before a threshold is
  set against them.

This is the same family as [absence is not a verdict](absence-is-not-a-verdict.md): a
measurement that reads as a fact about the world when it is a fact about the instrument.

## Handling notes that generalise

- **The decode convention is part of the space's identity, not an implementation detail.** The same model file read raw vs dequantised yields vectors that are NOT comparable. Whatever stamps embedding provenance must capture the convention, not just the model name and dimensions, or a superseded convention gets silently mixed with the current one.
- **A model card's usage example encodes its author's use case, not yours.** Ours pointed at a retrieval stack, which is why the defect was invisible from the card. Read the card for what the tensor *is* (dtype, quantisation range, whether pooling is internal), not for how to use it.
- **Never bless an unstamped vector as current.** An embedding with no recorded provenance predates the tracking, which means it predates whatever fix prompted the tracking. Mark it stale and re-embed; stamping it current makes the corruption permanent and invisible to staleness checks.
- **Batching is not free when pooling is internal to the export.** Padding can leak into the result, making a vector depend on what else shared its request. Check probe 4 before batching for speed.
