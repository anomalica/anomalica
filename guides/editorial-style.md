# Anomalica editorial and voice style guide

A living guide to how Anomalica writes: plain language, neutral voice, and open disclosure of AI's role. It consolidates the editorial decisions formerly recorded as ADRs 0006 (plain language), 0007 (neutral voice), and the disclosure half of 0009 (transparent AI use). Edited in place; git is the history. See [decisions/0001](../decisions/0001-record-decisions.md) for how decisions are routed.

## Plain language

Jargon and unexplained acronyms select out readers and give cover to imprecision. All Anomalica documents - code comments, architecture docs, decision records, and public content - use plain language.

### Acronyms

- Spell out every acronym on first use in every document; do not assume the reader has read any other document. "Freedom of Information Act (FOIA)" first, then "FOIA".
- If an acronym appears fewer than three times in a document, spell it out every time. It earns its place only if the full phrase recurs often enough to be genuinely awkward.
- Universally understood computing terms are fine without expansion: URL, PDF, HTML. When in doubt, spell it out.
- Page titles (article headlines) are the one exception: exactly two acronyms are written bare in a title, with no expansion and no bracketed gloss - UFO and UAP. No others. They are the platform's own subject, so no reader arrives without them; expanding UAP would force every title to settle "Anomalous" (the official United States term since late 2022) against "Aerial" (dominant in older sources); and a bare UFO translates into the reader's own language (OVNI, НЛО) where a bracketed English expansion does not. The rule covers the title only: body prose keeps the assembler prompt's wider safe set, and node names keep "Full Name (ACRONYM)" always (see [node-types.md](../architecture/node-types.md)), so a title and its slug diverge for these two ("UFOs" at `/topics/unidentified-flying-object-ufo`) by design. A proper name that contains the words keeps them: "Unidentified Aerial Phenomena Task Force (UAPTF)" is that office's name, not a gloss, and UAPTF is not on the list. Decided by Mark, 2026-09-03.
- Section headings belong on a long page only: use them when an article runs past roughly a thousand words, and continuous prose below that. Removing an entity page's paragraph count in 2026-09 also removed what had been suppressing headings, and the first page rebuilt without it came back sectioned where 7 of 280 entity pages carried any - sections suit a 1,500-word survey and are absurd on a 300-word biography.
- Where a title's subject is a class of countable things, the title takes the plural: "UFOs" and "UAPs", not "UFO" and "UAP". The plural is what generalises - "UFO" as a title reads as one object or as a definition of the acronym, "UFOs" reads as the phenomenon. It is the same reasoning that keeps titles in sentence case (a subject heading, not the proper name of one thing), and it is the one exception encyclopaedic convention makes to singular titles ("Horse", but "Arabic numerals", "Bantu languages"). The boundary: pluralise only where the acronym is the head of the phrase, never where it modifies something - "UAPs" alone, but "UAP encounters", "UAP Disclosure Act", "Mutual UFO Network (MUFON)". The assembler tests for the head as "nothing follows it in the title", which is exact for every title in the corpus today; a head with something trailing in brackets ("UFOs (alleged)") would be the case to revisit, and does not exist yet. Titles only; node names, aliases and slugs are untouched. Decided by Mark, 2026-09-03.

### Jargon

- When a technical term is necessary, explain it in plain terms on first use ("a provenance chain - the path a claim took from its original source to the knowledge graph").
- Prefer the plain version where it loses no precision: "evidence trail" over "provenance chain", "first-hand" over "primary attestation".
- Never use a complex word where a simple one works: "use" not "utilise", "show" not "demonstrate", "build" not "construct".

### Do not explain the interface to the person using it

A label says what a thing is. Then a second sentence tells the reader how to
operate it, and that second sentence is nearly always waste. From the works list:

> Books, articles, films and documents the sources name.
> *Choose one to read what the corpus says about it.*

The first line earns its place. The second instructs the reader to do the only
thing the screen affords - a list of rows is clickable, and nobody has needed
telling that for thirty years.

**The shape is an imperative plus a purpose clause**: *choose one to read what X
says*, *click a row to see its claims*, *select a source to view details*. Do this,
in order to see that. It is a sentence about operating the thing.

**The definite article is the quick tell**, and it is worth scanning for: the
purpose clause has to name the system's own furniture - *the* corpus, *the* record,
*the* list - so a "the" in front of a system noun usually rides along with one of
these. Use it to find candidates, not to convict them.

**IT DOES NOT CONDEMN A SENTENCE THAT SAYS WHAT THE DATA IS.** "Of the 800 works
named across the material, 25 are ones we hold" names internal furniture too, and
it is the most valuable line on that screen. The difference is not the article, it
is what the sentence is for: explaining the furniture to someone who can already
see it is waste; telling them what they are looking at, when they have never seen
it before, is the job. A well-made telephone does not say "pick up to talk" - but a
filing cabinet in someone else's office does need a label saying whose files these
are.

The mistake behind it is treating information as free. It is not. Every added
sentence is something to read, and it weakens the line above it - the label was
doing the work, and now it shares the space with an instruction.

So: write the label, then stop. If the interaction genuinely is not obvious, that
is a fault in the design, and a sentence of explanation hides it rather than fixing
it.

### Audience

- Architecture and code documentation: write for a competent programmer who may not know this specific domain.
- Public-facing content (website, README): write for a curious person with no technical background.
- Decision records: write so someone unfamiliar with the project can follow the reasoning.

## Neutral voice

The platform's model is wire-service reporting, not a magazine: report what sources say, attribute it, and let the reader draw conclusions. This applies to all content, whether AI-assembled or contributed by humans through the directive system.

- **No opinion pieces** - no editorials, perspective articles, or commentary.
- **No characterisation of the field or community** - articles do not call the topic "controversial", "fringe", or "legitimate"; they present what sources say.
- **No promotional language** - the platform does not call itself "groundbreaking" or "the first"; it states what it does.
- **No speculative conclusions** - no "this extraordinary claim" or "this compelling evidence"; the evidence score speaks for itself.
- **No assumption of truth or falsehood** - the platform does not declare claims true or false; it presents what sources say, how well-corroborated they are, and what the scoring produces.
- **Every assertion traces to a source** - if it cannot be attributed to a specific source in the knowledge graph, it does not appear (the architectural guarantee is [decision 0008](../decisions/0008-content-traceable-to-sources.md)).

Human directive contributions follow the same rules: corrections and additions must cite sources; the directive system is for factual input, not opinion.

## Quotation

Quotes are as long as they need to be to convey their point. The platform does not artificially truncate quotations or enforce a quote-length cap - a supporting quote runs to the length that conveys the fact, no more. Every quote is attributed to its source record.

This is lawful quotation (Japan's Copyright Act Article 32, with attribution under Article 48) and standard editorial practice, not a liberty the platform takes. It applies to the short evidential quotes that substantiate claims - NOT to full source bodies or transcripts, which stay behind the proof-of-possession gate (quote is not body). The copyright basis and the substantiality line are in [source types and copyright](../decisions/drafts/source-types-and-copyright.md#quotation-policy).

## Disclosing AI's role

AI is central to the platform and its use is communicated openly - never hidden, minimised, or apologised for. The methodology page on the website explains, in accessible terms:

- **Why AI is used** - maintaining articles across 30 languages with full source traceability is not feasible by hand; AI is the mechanism that makes the platform's promises possible, not a shortcut.
- **How AI is constrained** - articles are assembled only from knowledge-graph data, never from the model's training data; every claim traces to a source (see [decision 0008](../decisions/0008-content-traceable-to-sources.md)).
- **How quality is ensured** - a different model from a different provider independently verifies that every assertion traces to the graph (see [decision 0010](../decisions/0010-auditable-assembly.md)).
- **How humans participate** - all articles are open for human correction; edits become persistent directives the AI respects on future updates.

AI is involved at every stage (extraction, graph-building, assembly, translation) - unavoidable black boxes. The platform's answer is to make each box's inputs and outputs visible: the source document, the digest extracted from it, the assembled article, the verification report. The aim is not to remove the need for trust but to make every step as verifiable as possible.

**Watermarked models do not write what readers read, and do not reproduce sources.** Some providers embed a
statistical watermark in generated text (Google, and Anthropic for models launched from 2026-08-02, extending to
earlier models). On a reproduction or a published page that signal marks as synthetic the very text readers are
invited to check against sources. The model policy (`architecture/model-policy.yaml`,
[decision 0047](../decisions/0047-centralised-model-policy.md)) therefore refuses any provider not verified clean for the ingest, assemble
and translate stages. Stages whose output is a judgement or a structured claim rather than prose (digest,
assimilate, verify) may use them. The policy file is enforced in code and is the source of truth; this paragraph
only explains it.

## Editorial positions are stated, never encoded

Anomalica will hold positions. Some are unavoidable: which sources are
worth acquiring, how much weight a witness account carries against a
contemporaneous document, whether an institution's public conclusions are
treated as evidence or as a claim to be tested. These are judgements, and
having them is not the problem.

**Where a judgement is a value judgement rather than a measurement, it is
written down in prose, with its reasoning, where a reader can find it and
argue with it. It is never expressed as a constant inside a scoring
function.**

The failure this prevents: a number that looks neutral and is not. A
reader shown a confidence score reasonably takes it as the output of a
method. If an editorial preference has been folded into that number - a
coefficient down-weighting one class of source because the platform
distrusts it - then the score is quietly carrying an argument the reader
was never shown, and cannot examine, disagree with, or discount. That is
worse than an openly stated bias, because a stated position is
defensible and arguable while a buried coefficient is neither.

It also protects the person who holds the position. An editorial stance
set out in the open, with the thinking behind it, can be defended on its
merits or revised when someone makes a better argument. The same stance
discovered inside a scoring constant reads as concealment, whatever the
intent was.

This follows directly from the platform's disclosure commitments above.
Making each box's inputs and outputs visible is not much use if the
weighting between them is where the real judgement lives. So: the
scoring model computes what can be computed; everything else is an
editorial position, and editorial positions live here.
