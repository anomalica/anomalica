# 0014. Auditable article assembly

Date: 2026-03-26
Status: accepted

## Context

The platform uses AI to assemble articles from knowledge graph data (ADR 0010) and a different AI model to verify them (ADR 0004). For the platform's transparency commitments to be meaningful, readers must be able to verify not just what the AI produced, but what inputs it received. Without this, "transparent AI use" is a claim that cannot be checked.

## Decision

Every article assembly is auditable. The platform records enough information for any reader to reconstruct the exact prompt that produced an article and verify it independently.

For each assembled article, the following are recorded:

- A hash of the article content
- A hash of the full prompt sent to the assembling AI
- The directives that were active at assembly time
- The knowledge graph version used

All prompt components (knowledge graph data, directives, system template, previous article version) are independently versioned. A reader can reconstruct the full prompt from these components, hash it, and compare against the stored prompt hash. A match proves the article was produced from exactly those inputs.

After assembly, a different AI model from a different provider (ADR 0004) independently verifies that every factual assertion in the article traces to the knowledge graph. The verification report is stored alongside the article, including which model performed the check, when, and what it found.

The verification status is visible on the site. Articles can be published before verification - the status is informational, not a gate.

The site provides a prompt inspector that reconstructs and displays the full prompt for any article version, allowing readers to see exactly what the AI was given.

## Consequences

Every article carries a verifiable chain from inputs to output. A reader does not need to trust the platform's claims about how articles are produced - they can check.

The audit trail adds storage and processing overhead. Each article carries metadata (hashes, directive snapshots, verification reports) alongside the content itself. This is an acceptable cost for a platform whose credibility depends on verifiability.
