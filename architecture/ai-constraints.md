# Artificial Intelligence Constraints

Boundaries on artificial intelligence involvement across all components. These apply to the ingester, digester, assembler, and site.

For full context, see architecture decision record 0009 (transparent artificial intelligence use) and architecture decision record 0008 (no artificial intelligence-generated content).

## Core principle

Artificial intelligence assembles content from existing sources. It does not create content. The information exists in the knowledge graph (a structured database of interconnected facts) before the artificial intelligence touches it; the artificial intelligence arranges it into readable form.

## Specific constraints

- AI does not draw on training data for factual claims in articles
- AI does not generate images, audio, or text from training data
- Assembly and verification use different models from different providers in different jurisdictions (architecture decision record 0009)
- All AI involvement is transparent and documented
- The inputs and outputs of every AI step are visible: source document in, digest out, knowledge graph in, assembled article out
- If no real image exists for a topic, the article has no image

## Where AI is used

| Component | AI role |
|-----------|---------|
| **Ingester** | Speech-to-text, speaker diarisation, optical character recognition, text extraction (standard signal processing, not generative) |
| **Digester** | Claim extraction, node identification, relationship detection, evidence scoring |
| **Assembler** | Arranging knowledge graph data into articles, applying directives, per-language assembly |
| **Assembler** | Extracting directives from human edits, classifying edits as presentational or meaning-altering |
| **Verification** | Independent model verifies that assertions in assembled articles trace to knowledge graph sources |
