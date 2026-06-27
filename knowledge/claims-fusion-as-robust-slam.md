# Claims fusion as a robust SLAM back-end

Internal design knowledge (a reference note, not public-facing copy). A deliberate design lens for the claims pipeline, drawn from robotics perception - sensor fusion for SLAM (simultaneous localisation and mapping). It is borrowed on purpose, not a loose metaphor, and bears directly on the assimilator's corroboration and evidence-scoring work and on the [algorithmic-evidence-scoring draft](../decisions/drafts/algorithmic-evidence-scoring.md) - it is the robustness theory under that draft.

## The core claim

Anomalica's claims pipeline is structurally a SLAM back-end. The map being built is the knowledge graph; the measurements are claims with provenance and noise; the hard part - robustness to bad measurements - is a solved-ish problem in the robust pose-graph SLAM literature, and that literature ports largely wholesale.

## Stage-by-stage mapping

Pipeline: raw -> ingester -> ingests -> digester -> digests -> assimilator <-> knowledge graph -> assembler -> content -> site, with the workbench as the human-in-the-loop.

- A source or claim coming in = a **sensor measurement**, with noise and a provenance.
- The SQLite knowledge graph = the **map / state estimate** being built.
- Evidence scoring = assigning each measurement its **covariance / information weight** (the sensor model). A reliable independent instrument source = low covariance (trust it); a flaky aggregator = high covariance (barely move the estimate on it).
- Assimilator corroboration = **data association** (which claims refer to the same underlying fact) plus **fusion** (combine into a posterior). Almost all robustness must live here.
- Bayesian updating = the filter **update step**: prior + new measurement weighted by relative confidence -> posterior. The same operation run every frame in SLAM, applied to "did event X happen" instead of robot pose.
- Disinformation = a **spoofed / adversarial sensor** injecting coordinated biased measurements.

## The key insight: disinformation is a false loop closure

A knowledge graph is a graph; claims are edges / constraints. Disinformation is a **false loop closure**. Robust pose-graph SLAM already solved "stop a few false loop closures from wrecking an otherwise good map". Techniques to port:

- Switchable constraints (Sunderhauf & Protzel)
- Dynamic covariance scaling
- Max-mixtures (Olson & Agarwal)
- Graduated non-convexity / GNC (in GTSAM)
- Robust kernels (Huber, Cauchy)

Every one is a mechanism for: let possibly-false constraints in, then down-weight or switch off the ones that fight the consensus of everything else. That is Anomalica's stated posture of "tolerant of rubbish in, filter it out over time".

## Two load-bearing principles

1. **Eventual consistency only tracks truth if the conflict-resolution operator is truth-tracking.** Random error averages out with volume (the law of large numbers); adversarial disinformation does not - it is systematically biased, the same direction by design, so more volume concentrates it rather than diluting it. Resolution must therefore weight by **provenance and independence, never by corroboration-frequency**. The relevant robust-statistics notion is the **breakdown point** - the fraction of contaminated data an estimator tolerates before giving arbitrary answers (mean = 0%, median = 50%). Anomalica needs high-breakdown-point estimators and per-source influence caps so an adversary cannot hijack the map by flooding.

2. **Correlated measurements break fusion.** Fusion assumes independence; if two "sensors" are secretly the same source (an echo chamber, a re-published wire story, a laundered claim), naive corroboration double-counts and converges overconfidently on the wrong answer. Data association must check not just "do these claims say the same thing" but "are these independent observations, or is one a copy". Provenance-lineage tracking is the defence; without it an adversary manufactures corroboration for free.

## Trusted sources: by properties, not identity

Examples: Ross Coulthart, Chris Ramsay / Area 52, George Knapp. Encode trust as the design already demands - by measurable **properties**, not named identity. Hard-coding named people contradicts the charter (confidence from measurable properties of the sources, not human editorial judgement; jurisdiction-independent). Score the properties that make a source reliable - shows primary documents, names sources, original investigation versus aggregation, verifiable track record - so any source worldwide that scores high gets weight automatically.

Treat such sources as **strong, calibratable sensors with bounded influence**: high prior weight, but never breakdown-point-zero influence (even excellent journalists are prime disinformation targets - feeding a credible reporter is the classic operation). Their best use is **calibration**: their track record is labelled data to tune the scorer. Use them to train the model, not to be the model.

## Epistemic stance

Bayesian and abductive (inference to the best explanation), operating like the observational / historical sciences - astronomy, geology, epidemiology, forensics - which converge without controlled experiments, because Anomalica cannot run experiments either. Outputs are theories with explicit uncertainty, never asserted truths, revisable as evidence arrives.

The slogan "we don't judge" should be sharpened: judgement is not removed, it is **relocated** - from the gate (open ingestion, which is correct) to a transparent, evidence-weighted, revisable inference layer that anyone can inspect.
