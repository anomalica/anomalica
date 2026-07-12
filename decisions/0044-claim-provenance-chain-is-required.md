# 0044. The claim provenance chain is required, and it lives in the claim text when the claim rests on it

Date: 2026-07-12
Status: accepted

## Context

[data-model.md](../architecture/data-model.md) already declares that every claim has a **provenance chain** - "the path a claim took from its original source to the knowledge graph" - and makes the corroboration model depend on it:

> Two claims corroborate each other only if their provenance chains do not share a common root. Ten outlets all reporting the same press release is one source, not ten.

The claim shape in [digest-format.md](../architecture/digest-format.md) has never carried that field. A claim records `type`, `attestation`, `speaker`, `refs`, `quote`, `text` - and nothing about where the assertion came from before it reached the speaker. The chain is declared, depended upon, and not captured. **The corroboration rule is therefore uncomputable**, and its failure mode is not conservative: three podcasts each repeating one anonymous email look like three independent attestations rather than one.

The gap was found empirically. Digesting a 3.5-hour podcast (`a37ee0e7...`, Jon Stewart / DEBRIEFED ep. 69) surfaced an assertion that a filmed entity was "a clone extraterrestrial biological entity type two from the Tau Ceti star system". Its real chain is four removes: an anonymous person claiming to work inside the Defense Intelligence Agency -> an email -> an intermediary who forwarded it -> the speaker -> the podcast. Nothing in it is a fact; the only fact is that someone asserted it.

Extraction (Opus) found the passage and quoted it verbatim, then stored it as `type: testimony`, `attestation: second_hand`, with the Defense Intelligence Agency merely listed in `refs` and the normalised `text` reading "The being ... **was** a cloned extraterrestrial biological entity type two from the Tau Ceti star system." Three failures compounded:

1. **The chain was lost.** There was nowhere to put it. An anonymous actor cannot become a node ([node-types.md](../architecture/node-types.md) forbids person nodes for unnamed actors), so `refs` held only the organisation - making the record indistinguishable from the Defense Intelligence Agency having stated it officially.
2. **Attestation was under-graded** (`second_hand`, when a chain through an intermediary is `third_hand`) - and it was optional, so the model was never forced to answer.
3. **The hedge was stripped from `text`.** The extraction prompt required it: the speaker is already a structured field, so naming them in the text was treated as duplication. The proposition that survives into an article therefore asserts the entity's origin as fact.

Crucially, the model was **not** short of context: the chain is stated at t:6115 and the assertion at t:6329, both inside the same chunk, and neighbouring claims from that same email were correctly typed `hearsay`. It had the information and applied it inconsistently. The problem is not grounding; it is the absence of a **forcing function** - a claim could be emitted without ever answering "where did this come from?".

A separate failure from the same record: a running comedic bit ("a former pro wrestler who ran for governor") was extracted as biography. An insincere utterance is not a claim, and nothing said so.

## Decision

### 1. Every claim carries a `provenance_chain`, and the schema requires it

The claim gains a required `provenance_chain`. Because extraction runs under `--json-schema`, a required field is a hard forcing function: the model cannot return a claim without answering where the assertion came from.

```yaml
provenance_chain:
  origin_kind: anonymous        # speaker | named | anonymous | document | unattributed
  origin: "a person claiming to work inside the Defense Intelligence Agency"
  relay:                        # ordered, origin -> speaker; empty when the speaker IS the origin
    - "an email"
    - "an intermediary known to the speaker"
```

- **`origin_kind`** classifies the root of the chain and is the field corroboration keys on.
  - `speaker` - the speaker originated it (they observed, did, or hold it). `relay` is empty.
  - `named` - an identifiable person, organisation, or document. It is a node, and MUST also appear in `refs`.
  - `anonymous` - an unnamed or unidentifiable source. **It cannot be a node**, so this field is the only place it can survive.
  - `document` - a document or record the speaker is reading from or citing.
  - `unattributed` - the source asserts it with no attribution offered (ordinary narration).
- **`origin`** is a short prose identification of the root. For `anonymous` it describes the claimed identity without conferring it ("a person *claiming* to work inside the Defense Intelligence Agency").
- **`relay`** is the ordered path from origin to speaker. Its length is what makes the chain a chain.

This is the claim-level chain [data-model.md](../architecture/data-model.md) already requires. It is **distinct from the record's `provenance` block** ([0043](0043-canonical-provenance-block.md)), which is source-origin metadata about the *document* (publisher, dates, URL). Provenance says where the document came from; the provenance chain says who, inside the document, asserted the claim and through whom it reached the speaker. A claim has both.

### 2. Attestation is required, and derived from the chain

`attestation` stops being optional and stops being a matter of feel. It follows from the chain:

| Chain | Attestation |
|-------|-------------|
| `origin_kind: speaker`, `relay` empty | `first_hand` |
| One remove (the speaker heard it directly from the origin) | `second_hand` |
| Two or more removes (it reached the speaker through an intermediary) | `third_hand` |
| `origin_kind: unattributed` | omitted - there is no evidential stance to record |

**Grade by the whole chain, not by the last mouth it passed through.** A speaker naming their immediate contact does not make the claim second-hand if that contact was themselves relaying someone else. Count the removes. This is what made the Tau Ceti claim `second_hand` when it is `third_hand`.

### 3. When a claim rests on who asserted it, the attribution belongs in the claim text - and extraction DECLARES that it does

Where the claim's truth-status depends on the assertion itself, **the attribution goes inside the `text`**:

  - RIGHT: "An anonymous source claiming to work inside the Defense Intelligence Agency, in an email forwarded to the speaker by an intermediary, said the filmed entity was a cloned extraterrestrial biological entity type two from the Tau Ceti star system."
  - WRONG: "The being was a cloned extraterrestrial biological entity type two from the Tau Ceti star system."

The reason is not stylistic. For such a claim, "the entity came from Tau Ceti" is not a fact about the world and is not what the source establishes. The fact about the world is *that an anonymous person asserted it*. Stripping the attribution does not tidy the claim - it **changes what the claim says**, from a true statement about an assertion into a false statement about reality. A claim must be safe read alone, because eventually something will read it alone: `text` is what flows into articles, and safety cannot depend on every consumer, forever, remembering to check a sidecar field.

**Attribution-in-text means naming the ORIGIN inside the sentence** - normally as its grammatical subject ("David Fravor observed the object accelerate"; "Jon Stewart considers the account a PSYOP"). It does NOT mean prefixing the claim with the RELAYER or the containing document ("According to the DoD statement of 2020-04-27, ..."), which remains forbidden by the anchor rules. Those are different things: the first is ordinary prose, the second is the quotation-pile the anchor rules exist to prevent.

**Extraction declares it; nobody derives it.** Every claim carries a required boolean:

```yaml
attribution_in_text: true    # the text names who asserted this
```

It is set by the model that just wrote the text, so it cannot drift from it. Downstream consumers **read** it and must never re-derive it from `origin_kind`/`claim_type`/`attestation`: those are proxies for a property of the sentence, and a proxy can disagree with the sentence. Deriving it was the original design and it was wrong - a `named` or `document` origin is always at least one remove, so it grades `second_hand` and any depth-based rule routes every ordinary citation into "attribution required", contradicting the conduit case in the same breath. The only stable invariant is: *the attribution is in the text if and only if the writer put it there.*

Consumers therefore branch on three states, and the third is the one that matters:

| `attribution_mode` | Condition | Consumer behaviour |
|--------------------|-----------|--------------------|
| `in_text` | chain present AND `attribution_in_text` | Render as-is. Suppress a separate speaker line. Never wrap in a second attribution. |
| `bare_ok` | chain present AND NOT `attribution_in_text` | Safe as a bare fact. |
| `unknown` | no chain (every pre-0044 claim), or ungradeable | **Fail safe.** The text is bare but unvouched. Do NOT assert it, do NOT render as-is. Hedge or drop. |

`unknown` must never fall through to "safe to assert". Absence of a danger signal is not evidence of safety - that is how a claim of unknown provenance gets published as fact, which is the failure this record exists to prevent.

### 4. Only sincere assertions are claims

Exhaustive extraction means never skimming and never curating for importance. It does not mean literalising every sentence spoken. A claim is extracted only where the source **sincerely asserts** a fact. These are not claims, even though the words appear verbatim:

- **Jokes, deadpan, irony, running bits.** Deadpan gives no signal that a joke is underway; comedic self-description is not biography.
- **Hypotheticals and rhetorical questions.**
- **Statements quoted in order to be rejected.**
- **Hyperbole and figures of speech** - never convert them into measurements.

Omitting a joke costs little. Asserting one as fact manufactures a false fact, which is the worst output this system can produce.

### 5. The nodes pass emits a document-level attribution profile

The nodes pass already reads the whole document. It additionally emits a short profile - the speaker's epistemic role (witness / investigator / relayer), and the named and unnamed sources the document leans on - which is threaded into the claims pass alongside the node directory. This costs no additional model call.

It grounds a chunked claims pass when a chain is established in one chunk and its claims land in another. It is a **grounding aid, not the forcing function**: the Tau Ceti failure occurred with the chain in the same chunk, so context alone does not fix this. The required field does.

## Why

- **The corroboration model is already staked on this.** Independence is defined by non-shared chain roots. Without the chain, corroboration cannot be computed, and it fails *unsafely* - repetitions of a single anonymous email present as independent corroboration. For a project whose entire claim to legitimacy is recording what people said rather than what is true, that is the worst available bug.
- **A required field beats an instruction.** Attestation was documented, optional, and skipped. Under `--json-schema` a required field cannot be skipped. It converts a judgement the model may quietly decline into one it must make at the moment it makes it - and it lifts every model, including the cheap ones, rather than buying fidelity with a bigger model.
- **An anonymous source has nowhere else to live.** Since it cannot be a node, omitting the chain does not merely lose detail: it silently promotes an anonymous assertion into an institutional one.
- **Safety must not be a convention.** `text` is rendered downstream. A hedge held only in a sidecar is one careless consumer away from being published as fact.

## Consequences

- **Digest format**: `provenance_chain` is added to the claim ([digest-format.md](../architecture/digest-format.md)); `attestation` becomes required except for `unattributed`. The field is additive for readers - digests written before this record lack it, and consumers must treat its absence as "not captured" rather than "no chain". A re-digest backfills.
- **Extraction**: the claims JSON schema marks `provenance_chain` required; the claims prompt gains the chain, whole-chain attestation, load-bearing-attribution, and sincere-assertion rules; the nodes pass gains the attribution profile.
- **Downstream consumers** are affected and must be told: the **assimilator** (corroboration and independence can now actually be computed from chain roots, and its embeddings can cluster anonymous origins that are worded differently), the **assembler** (claim text for hearsay now carries its own attribution, so it must not add a second one), and the **workbench** (adjudication should surface the chain, since a flattened chain is a defect a reviewer must be able to see and mark).
- **Evidence scoring** can finally discount repetition of a shared root instead of rewarding it.
- Prompt and schema changes bump the prompt version, so digests produced before and after are distinguishable by the `prompts` block already recorded ([0039](0039-multi-model-digestion-canonical-reconciliation.md), [0042](0042-pre-digest-stage-and-eval-only-highlights.md)).

## Scope

Implements the claim-level provenance chain that [data-model.md](../architecture/data-model.md) already declares and that the corroboration model already depends on, making it a required extraction field rather than an optional judgement; derives attestation from chain depth; requires the attribution to appear in the claim text wherever the claim's truth rests on it; and excludes insincere utterances from being claims. Does not change the record's `provenance` block ([0043](0043-canonical-provenance-block.md)), which is a separate concern - source origin, not assertion chain.
