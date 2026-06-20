# 0020. Canonical English normalisation for embeddings

Date: 2026-03-20
Status: accepted

## Context

The platform ingests sources in any language and needs to deduplicate claims, detect corroboration, and compute similarity across the entire knowledge graph (a structured database of interconnected facts). Cross-lingual embedding models (systems that convert text into numerical representations so that similar meanings produce similar numbers) exist but perform worse on non-English-to-non-English language pairs (e.g. Japanese to Portuguese) than on within-language comparisons.

Using a multilingual embedding model introduces a dependency on an external service if the best models are cloud-only, and increases vector size and computation cost.

## Decision

All claims will be normalised to a canonical English representation before embedding, regardless of the source language. The original-language excerpt will be preserved in provenance metadata.

The embedding model will be English-optimised rather than multilingual, running locally with no dependency on an external service. The specific model and runtime are implementation details documented in [architecture/embeddings.md](../architecture/embeddings.md).

## Consequences

The cross-lingual problem will be eliminated at the ingestion step. The embedding model will only compare English to English, which is what every model does best. A smaller, English-focused model will be faster and more accurate for this use case than a larger multilingual model.

Normalisation quality at the extraction step will be critical - a poorly normalised claim would fail to match correctly. Since extraction uses Claude (which handles multilingual text well), the normalisation to canonical English will be inherent to the extraction process, not a separate step.

The downloadable SQLite file will contain English-canonical claims with English-only embeddings from a single model. Anyone who downloads it will be able to work with it without multilingual tooling.
