# Embeddings

Embeddings are vector representations of text used throughout the digester for deduplication, similarity search, and corroboration detection. This document covers how embeddings are generated, stored, and managed.

## Canonical English

All text is normalised to canonical English before embedding, regardless of the source language. The original-language text is preserved in provenance metadata. See [ADR: Canonical English normalisation](../decisions/drafts/canonical-english-embeddings.md) for the rationale.

This means the embedding model only ever compares English to English, which is the best-represented language in training data for all models and consistently produces the highest quality results.

## Model selection

The embedding model should be:

- Runnable locally with no external API dependency
- Strong on semantic textual similarity (the MTEB STS benchmark is the most relevant measure, since it directly reflects claim deduplication performance)
- 1024 dimensions (balances quality against storage cost)
- Small enough to bake into a container image

The specific model will change over time as better options become available. The architecture is designed so that changing the model is a routine operation, not a migration crisis.

## Storage

Embedding vectors are stored in separate SQLite databases from the core knowledge graph. This separation exists for several reasons:

- The core knowledge graph (claims, entities, provenance, scores) is the primary data. Embeddings are derived data, computable from it.
- Keeping embeddings separate keeps the primary database download small.
- Different embedding models can coexist as separate databases, all keyed by the same primary identifiers and joinable at query time.
- Re-embedding the entire graph with a new model does not touch the core data.

Each embedding database is specific to one model. The filename or metadata identifies which model produced it.

## Re-embedding

Because embeddings are derived from text already stored in the knowledge graph, re-embedding is straightforward: iterate over every row with a text field, run it through the new model, write the new vector. The knowledge graph itself does not change.

This makes model upgrades low-risk. A new embedding database can be built alongside the existing one, compared for quality, and swapped in when ready.

## Runtime

In development, the embedding model may run via Ollama on the host machine. In production, the model is packaged directly into the container image using a lightweight inference runtime (such as ONNX Runtime) with no external service dependency.

The digester code abstracts the embedding backend so that the rest of the pipeline does not care how vectors are produced.
