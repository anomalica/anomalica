# 0004. Transparent use of AI with independent verification

Date: 2026-03-23
Status: accepted

## Context

AI-assembled content carries a reputation problem. Many people associate AI-produced text with hallucination, bias, and a lack of accountability. For a platform whose credibility depends on accuracy and traceability, using AI to assemble articles could undermine trust if not handled openly.

At the same time, the platform's design requires AI. Maintaining thousands of articles across 30 languages, keeping them current as the knowledge graph evolves, and ensuring every assertion traces back to a specific source - this is not feasible with manual editing alone. AI is not a shortcut; it is the mechanism that makes the platform's core promises possible. The distinction between AI that creates content and AI that assembles content from existing sources is addressed in ADR 0010.

## Decision

The platform's use of AI will be clearly communicated to users. It will not be hidden, minimised, or apologised for. The website will explain:

- **Why AI is used** - the scale of maintaining articles across 30 languages with full source traceability requires automated assembly. AI enables provenance chains that would be impractical to maintain manually.
- **How AI is constrained** - articles are not created from the AI's training data. The AI receives structured data from the knowledge graph and assembles articles based only on that data. Every claim in an article must trace back to a specific source in the graph.
- **How quality is ensured** - a different AI model from a different provider independently verifies that every assertion in an assembled article has a corresponding source in the knowledge graph. Unmatched assertions are flagged.
- **How humans participate** - all articles are open for human correction. Human edits are processed into persistent directives that the AI respects in future updates. The AI and humans work together on the same documents.

### Independent verification across providers

The AI that assembles articles will not be the same AI that verifies them. Assembly and verification will use models from different providers in different jurisdictions. For example, a US-developed model for assembly and a Chinese-developed model for verification, or vice versa. This provides:

- **Independence** - different training data, different failure modes, different potential biases
- **Geopolitical diversity** - neither a single government nor a single company's influence can affect both assembly and verification
- **Reduced correlated hallucination** - if two models from different backgrounds agree that an assertion is supported by the source data, confidence is higher than if one model checks its own work

The specific models used for assembly and verification may change over time as the field evolves. The principle of using independent models from different providers will remain.

## Consequences

Users will understand how AI is involved and what safeguards are in place. The methodology page on the website will explain the assembly and verification process in accessible terms.

Some users will distrust AI-involved content regardless of the safeguards. AI is involved at every stage - extracting claims from source documents, building the knowledge graph, assembling articles, and translating. These are unavoidable black boxes. What the platform can do is make the inputs and outputs of each black box visible: here is the source document, here is what was extracted from it, here is the assembled article, here is the verification report. A reader can check the source document themselves and judge whether the extraction is accurate. The aim is not to eliminate the need for trust, but to make the platform as verifiable as possible at every step.
