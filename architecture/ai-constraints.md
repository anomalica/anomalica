# Artificial Intelligence Constraints

Boundaries on artificial intelligence involvement across all components. These apply to the ingester, digester, assembler, and site.

For full context, see decision 0008 (content traceable to sources), decision 0010 (auditable assembly, including independent verification), and the editorial style guide (open disclosure of AI use).

## Core principle

Artificial intelligence assembles content from existing sources. It does not create content. The information exists in the knowledge graph (a structured database of interconnected facts) before the artificial intelligence touches it; the artificial intelligence arranges it into readable form.

## Specific constraints

- AI does not draw on training data for factual claims in articles
- AI does not generate images, audio, or text from training data
- Assembly and verification use different models from different providers in different jurisdictions (decision 0010)
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

## Which models, and why

Where AI is used is above. WHICH model runs at each stage, and which models are
refused, is a separate question with its own source of truth:
[architecture/model-policy.yaml](model-policy.yaml), reasoned in
[decision 0047](../decisions/0047-centralised-model-policy.md).

That file is authoritative over any component's own choice, is read at runtime by
every component that dispatches a model call, and is published to readers as a
generated page. The rule with the widest reach: models whose providers watermark
generated text are barred from reader-facing writing (pages, translations), and a
provider whose watermarking state is unknown is treated as watermarking rather
than as clean.
