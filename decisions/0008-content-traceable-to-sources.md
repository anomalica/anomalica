# 0008. Content traceable to sources

Date: 2026-03-23
Status: accepted

## Context

Decision 0009 establishes that artificial intelligence (AI) is central to the platform's operation and that its use is transparent. This decision clarifies the boundary of that role.

AI necessarily produces prose when assembling articles - it chooses words, structures sentences, and decides how to present information. This is unavoidable and is not the concern. The concern is whether the factual content of an article can be traced back to specific sources in the knowledge graph (a structured database of interconnected facts), or whether the AI is drawing on its training data to add information that does not come from any identifiable source.

Some platforms in the unidentified anomalous phenomena space use AI-generated illustrations as article imagery - fabricated depictions of alleged incidents, beings, or craft. Others allow AI models to draw on training data when writing articles, producing claims that cannot be traced to any specific source. Both practices blur the line between what is known and what is imagined.

## Decision

Every factual claim in an article traces to a specific source in the knowledge graph. The AI assembles articles from knowledge graph data - claims, sources, relationships, evidence scores - arranging existing information into readable prose. The AI produces the language; the knowledge graph provides the facts.

This principle applies across all content types:

- **Text.** Every factual claim traces to a specific source. The AI does not draw on its training data for factual assertions and does not add information that is not in the knowledge graph. The AI does produce the prose that connects and presents those facts.
- **Images.** Only real photographs, video stills, official documents, maps, diagrams, and biographical photos are used. No AI-produced imagery. If no suitable real image exists for a topic, the article appears without an illustration.
- **Audio.** Only real recordings are used. No AI-produced speech, narration, or sound.

The platform makes no assumption about whether a claim is true or false. That is determined by the evidence scoring system - the strength of sources, degree of corroboration, and quality of evidence. The AI's job is to present what the sources say and let the scoring speak for itself.

## Consequences

The platform will sometimes have less visual content than competitors that use AI-produced illustrations. Some articles will have no images at all.

Every piece of content on the platform can be traced back to its source. A reader never has to wonder whether a factual claim was drawn from evidence or invented by a model.
