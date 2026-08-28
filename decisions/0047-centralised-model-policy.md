# 0047. One model policy, read by components and published to readers

Date: 2026-08-28
Status: accepted

## Context

Five components call models: the ingester, digester, assimilator, assembler and
scheduler. Each chose its own model, in its own code, for its own reasons. The
reasons were real but unwritten, so they could not be checked, compared or
inherited - and a choice nobody can see is a choice nobody can correct.

Two things made that untenable.

The first is a rule that cannot be enforced locally. Provider watermarking
embeds a detectable signal in generated text. On a project whose value is that
its text tracks real sources, that signal is wrong on reader-facing output: it
marks as synthetic the prose readers are invited to check against originals, and
it travels into every quotation of our pages. Barring watermarking models from
reader-facing stages is one rule, but enforcing it in five codebases means five
places to get it right and five places for it to rot. A model released tomorrow
would have to be blacklisted five times.

The second is that these choices are interesting to people outside the project.
We ask readers to check our work against sources; which model wrote a page, and
why that model was eligible, is part of what they are checking. Published, the
policy can be argued with. Unpublished, it is a claim about our own rigour that
nobody can test.

## Decision

A single machine-readable file, `architecture/model-policy.yaml`, is the source
of truth for which models are used where. Components resolve their model through
shared code in `anomalica-common` rather than carrying a list. The site generates
a public page from the same file at build time.

Five properties, each chosen against a specific failure:

**The file is authoritative, not descriptive.** Where a component's model choice
disagrees with the file, the component is wrong. A file that documents what the
code does drifts silently and is worth nothing at the moment it matters.

**Deny by provider prefix, never by model id.** `anthropic/*`, not a list of
model names. A deny list naming individual models silently admits every model
released after it was written - which is exactly when a new watermarking model
appears. A prefix cannot be outrun by a release.

**Watermarking has three states: watermarks, clean, unknown.** Unknown is not
clean. A provider nobody has checked has not passed a check, and unknown-state
providers are barred from reader-facing stages regardless of how they benchmark.
Treating silence as absence is how an unevaluated model becomes eligible by
default.

**Unlisted means refused.** A stage requesting a model the file does not list
fails closed and does not dispatch. Warn-and-proceed makes the policy advisory,
and an advisory policy is not a policy.

**Rationale prose is written by a person.** The public page is generated from the
file; the reasons in it are not generated. Where a rationale is absent the page
says "not yet documented", which is true and invites correction. A generated
justification for our own model choices would be the one claim on the site that
readers could not check - and the one most flattering to us.

**A stage that uses no model says so.** `uses_model: false` is a positive
assertion, not an omission. A deterministic stage listed under a model gets filed
into the lane that gates on spend, and is then withheld whenever metered spend is
off - producing a lane that silently does nothing. That has happened once
already, to brief synthesis.

**Every stage names who enforces it.** The scheduler does not dispatch every
model call; the assimilator makes its own inside its run. A stage the scheduler
does not dispatch needs its component to apply the policy, or nothing does, and
"the policy exists" would be true while nothing checked it.

**Aliases resolve before policy applies.** The subscription transport takes bare
names (`sonnet`); this file names real ids (`claude-sonnet-5`) so a reader can
tell which version ran. An alias map joins them. Applying `unlisted means
refused` to an unresolved alias would fail every Claude dispatch on a naming
difference rather than a policy one - and a lane failing closed for the wrong
reason looks exactly like one working correctly.

Policy is also kept distinct from two orderings it is often confused with. The
policy decides what is permissible; a stage's `priority` list decides what is
best; the scheduler's pace decides what is urgent. Three orderings with three
kinds of authority, and collapsing them into one score loses the distinction
between "forbidden" and "currently expensive".

## Consequences

The models we rate most capable are excluded from writing the pages readers see.
That is the intended effect of the watermarking rule and its most expensive
consequence.

Pages already written by a now-barred model are not rebuilt to remove
watermarks. Pages become stale as new claims arrive and are rewritten then, so
the corpus turns over without a bulk rebuild - and a bulk rebuild would spend
real money to re-do work that will be re-done anyway.

Adding a model becomes a documented act rather than an edit to whichever
component needed it. This is deliberate friction: the cost of adding a model is
one rationale sentence, and a model nobody can justify in a sentence is one we
should not be dispatching.

Publishing the policy invites disagreement about choices previously made
privately. That is the point of publishing it.

## Related

- [architecture/model-policy.yaml](../architecture/model-policy.yaml) - the file itself
- [architecture/ai-constraints.md](../architecture/ai-constraints.md) - where AI is used at all
- [guides/editorial-style.md](../guides/editorial-style.md) - AI-authorship disclosure
