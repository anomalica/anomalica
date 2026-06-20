# 0010. Auditable article assembly

Date: 2026-03-26
Status: accepted

## Context

The platform uses artificial intelligence (AI) to assemble articles from knowledge graph data (decision 0008) and a different AI model to verify them. The knowledge graph is a structured database of interconnected facts. For the platform's transparency commitments to be meaningful, readers must be able to verify not just what the AI produced, but what inputs it received. Without this, "transparent AI use" is a claim that cannot be checked.

## Decision

Every article assembly is auditable. The platform records enough information for any reader to reconstruct the exact prompt that produced an article and verify it independently.

For each assembled article, the following are recorded:

- A cryptographic hash of the article content (a fixed-length fingerprint that changes if even one character of the content changes)
- A hash of the full prompt sent to the assembling AI
- The directives that were active at assembly time
- The knowledge graph version used

All prompt components (knowledge graph data, directives, system template, previous article version) are independently versioned. A reader can reconstruct the full prompt from these components, hash it, and compare against the stored prompt hash. A match proves the article was produced from exactly those inputs.

The knowledge-graph-data component is realised as the **brief** - the per-page graph slice the synthesiser emits and the writer's sole input ([decision 0036](0036-synthesise-stage-brief-as-writer-input.md)). The brief's input hash is this component's audit hash, so one object serves as the writer's input, the per-page staleness unit, and this audit record.

After assembly, a different AI model from a different provider independently verifies that every factual assertion in the article traces to the knowledge graph. The verification report is stored alongside the article, including which model performed the check, when, and what it found.

The verification status is visible on the site. Articles can be published before verification - the status is informational, not a gate.

### Independent verification across providers

The model that assembles an article is never the model that verifies it. Assembly and verification use models from different providers in different jurisdictions (for example a US-developed model for assembly and a Chinese-developed model for verification, or vice versa). This gives:

- **Independence** - different training data, different failure modes, different potential biases.
- **Geopolitical diversity** - neither a single government nor a single company can influence both assembly and verification.
- **Reduced correlated hallucination** - if two models from different backgrounds agree an assertion is supported by the source data, confidence is higher than a model checking its own work.

The specific models may change as the field evolves; the principle of independent models from different providers does not.

The platform's public communication of how and why AI is used lives in the [editorial style guide](../guides/editorial-style.md); this record covers the auditability mechanism.

The site provides a prompt inspector that reconstructs and displays the full prompt for any article version, allowing readers to see exactly what the AI was given.

## Consequences

Every article carries a verifiable chain from inputs to output. A reader does not need to trust the platform's claims about how articles are produced - they can check.

The audit trail adds storage and processing overhead. Each article carries metadata (hashes, directive snapshots, verification reports) alongside the content itself. This is an acceptable cost for a platform whose credibility depends on verifiability.
