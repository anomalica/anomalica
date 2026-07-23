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

## Amendment 2026-07-23: implementation status, and two specification defects

This record describes an audit trail that **is not built**. Measured against
the assembler on this date: `hashlib` is not imported, and nothing in the
list below is computed or stored.

| Component this record requires | Status |
|---|---|
| Hash of the article content | Not emitted. |
| Hash of the full prompt | Not computed. |
| Knowledge-graph data, versioned | Brief mode only (`brief_hash`). Record mode has the digest's `content_hash`. **Node mode - the majority of the corpus - has no slice identity, and no mechanism exists to create one.** |
| Directives, versioned | Not versioned. |
| Previous article version | Has never existed (see below). |
| Verification report | Does not exist. `validate_article` is a structural parser with quirk repair, not verification: no second model, no stored report. |

Until these land, the transparency commitment this record makes - that a
reader can reconstruct the prompt and verify an article independently, via
a prompt inspector - is **unbacked**. The commitment is not withdrawn; it
is recorded here as outstanding so the gap is not mistaken for a solved
problem. Tracked as three separate pieces of work, because one title hid
three very different sizes: the generator/output stamp (small), node-mode
slice identity (design, cross-component with the assimilator), and the
verification report (a feature, not a field).

Two defects in this record's own specification, corrected in
[content-format.md](../architecture/content-format.md#auditable-assembly):

- **"A hash of the full prompt" is underspecified**, because the prompt
  differs by transport: the subscription path appends a system prompt, the
  API path sends none. One blended hash would give the same authored prompt
  two identities depending on billing path, and could not say which
  component differed. Replaced by component hashes - user prompt, system
  prompt, resolved directives - plus a `transport` stamp. The divergence
  itself is a defect to close: `<COMPONENT>_USE_API` selects a billing
  path, and prompt content is meant to be invariant across it.
- **"Previous article version" is dropped from the prompt-component
  list.** It was never implemented - `build_prompt` takes node, claims,
  related nodes, and directives - and it should not be. Feeding an
  article's previous version back in makes assembly a function of its own
  history: the article can no longer be rebuilt from its inputs alone, so
  two people holding identical inputs get different articles depending on
  what happened to be there before. That contradicts the reconstructability
  this record exists to guarantee - reconstructing the prompt would require
  the whole version chain rather than the current inputs - and it makes the
  `body_sha256` staleness axis incoherent, because regeneration would never
  converge.

  The need it presumably served, preserving human edits across
  regeneration, now has a deterministic mechanism instead: `body_sha256`
  detects that a human edited the body and the assembler's preserve-list
  keeps the authored keys, rather than feeding old text to a model and
  hoping it is carried through. If iterative human-guided refinement is
  wanted later it is a piece of work in its own right, with the
  idempotency trade-off stated - not a line item in a component list.

Directives, when versioned, must hash the **resolved** list rather than
point at files: they are resolved at build time from up to five sources
walking up the folder tree, so the file set that produced a given article
is not recoverable from the article.
