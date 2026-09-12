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

**Deny accepts a provider glob or a single model id, in two layers.** Both
granularities are kept because they answer different questions. A provider glob
(`anthropic/*`) bars a family including models not yet released, and is the only
form that cannot be outrun by a release - which matters most for watermarking,
where the risk is a new model becoming eligible by not being on a list. A model
id (`claude-opus-5`) bars one thing without judging its siblings, which is what a
failed benchmark or a deprecation calls for.

The layers are a global deny that no stage can exempt itself from, and a per-stage
deny that adds to it. Nearly everything belongs at stage level, because a model is
rarely wrong everywhere: watermarking bars a model from writing pages while
leaving it correct for extraction. The global layer is for a model that must not
run at all, and exists so a bar cannot be lost through an omission in a stage
added later. A model must pass both layers, and denial beats priority - a model
both prioritised and denied is denied, which is how a stage inherits a global bar
without its priority list being rewritten.

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

## Amendment 2026-09-11: route-specific subscription candidates

One provider can expose materially different routes to the same named model.
Those routes may have different context limits, allowance accounting, caching
and failure modes, so they are separate policy identities rather than one model
whose route is changed underneath it. The first application is the candidate
`openai-subscription/gpt-5.6-*` family alongside the existing metered
`openai/gpt-5.6-*` family. Both families carry `provider: openai`; their route
fields and route-qualified ids carry the execution distinction.

The authenticated route has a 400,000-token total context split into a maximum
272,000-token input and 128,000-token output. The policy records 272,000 as its
provider input ceiling. OpenCode 1.18.30 with the selected no-tools
configuration adds a hidden system scaffold measured within a 12,000-token
reserve, recorded as `input_reserve`. Dispatch uses the conservative check
`len(submitted_payload.encode("utf-8")) + input_reserve <= max_input`: each
visible UTF-8 byte is treated as at most one token. The resulting visible
submitted-payload ceiling is 260,000 bytes.

`input_reserve_qualification` binds that measurement to transport
implementation `opencode`, executable version `1.18.30`, and configuration
SHA-256
`5c4867f4ae4b635d34b4f4020f37c02ccbafffab23900a6b687d48ffb14484c7`.
The configuration hash covers the complete raw byte sequence of the exact
artefact selected through `OPENCODE_CONFIG`, with no decoding, newline
normalisation, parsing or canonicalisation. It is the same value written to
`built_by.transport_config_sha256`. Dispatch fails before a model call if the
qualification is absent or malformed, or if the actual implementation,
version or selected-configuration hash cannot be read or differs.

All facts used for one dispatch come from one atomic policy snapshot. The
loader resolves the selected policy path once, reads its complete raw bytes
once, computes SHA-256 over those bytes without normalisation, and parses those
same bytes. The resulting object retains the resolved path and raw-byte hash;
provider identity, stage eligibility, capacity and transport qualification for
the attempt are all read from that one object. A cache may reuse only that exact
path-and-hash snapshot. It must not key solely on modification time or combine
lookups from separately loaded revisions.

This is materially smaller than the metered route: an existing assembly input
measured 544,043 tokens. An explicitly selected subscription candidate must be
refused when its submitted payload does not fit; candidate selection cannot
trigger automatic fallback or rerouting. A larger-context route may run only
after it is selected and authorised separately. Automatic stage sizing remains
based on `priority`, not the smallest explicit-only candidate. The reserve
belongs in central policy rather than a transport-local constant so the stated
limit and enforced limit cannot drift.

The subscription entries are in `assemble.candidates`, not `assemble.priority`.
A candidate passes an explicit policy check for manual evaluation, but automatic
choice, rerouting and stage context sizing use `priority` only. This amendment
therefore does not change the default, lower the current assembly brief budget,
activate production dispatch, or make the entries eligible for `translate` or
`digest`. Their allowance can be paced from the authenticated route's
provider-reported usage percentages when implementation lands.

Candidate eligibility and operational dispatch state answer different
questions. A stage `candidates` entry means the model may be named explicitly;
it does not assert that its allowance pool is currently dispatchable. The
scheduler records each pool as one of:

- `disabled`: unattended dispatch is switched off by an operator;
- `unknown`: no valid allowance observation is available;
- `stale`: the last valid observation is older than its declared freshness
  interval;
- `exhausted`: a fresh observation reports no usable allowance;
- `available`: a fresh observation reports usable allowance and no operational
  hold is active.

Pool status records the meter source, observation time and freshness interval.
Every state except `available` fails closed for unattended dispatch. An explicit
authorised manual evaluation remains dry-run only: it may inspect policy,
estimate fit and construct the payload, but it must not start an inference
process or return cached generated content. It cannot bypass `disabled` or any
other operational state while the activation blockers below remain. The
operational reason may be private; the state and refusal remain visible to
operators. Disabling a pool must not remove an eligible candidate from policy
or misreport it as stage-ineligible.

The allowance meter and generation client may be different programs only when
they are proven to address the same provider account and allowance pool. The
current Codex app-server meter and OpenCode generation route have no recorded
same-account binding. This is a production-activation blocker, not an inference
that they differ. Production also remains blocked until the canonical
per-attempt SQLite ledger records the qualification evidence and pre-call
refusals required by [0037](0037-ai-operation-ledger.md). Live manual and
unattended calls share these activation gates. Until every gate exists and
passes, explicit candidate evaluation means dry-run/no-call only.

## Related

- [architecture/model-policy.yaml](../architecture/model-policy.yaml) - the file itself
- [architecture/ai-constraints.md](../architecture/ai-constraints.md) - where AI is used at all
- [guides/editorial-style.md](../guides/editorial-style.md) - AI-authorship disclosure
