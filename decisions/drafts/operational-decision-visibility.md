# Operational and strategic decisions are private by default

Date: 2026-05-29
Status: draft (proposed - amends 0004)

## Context

Decision 0004 (open source with transparent operations) states that "all code,
documentation, and operational decisions will be public," with the only private
elements being credentials and the CLAUDE.md files that reference the founder's
vault.

That wording is too broad. It was written early, before the operating side of the
project existed. In practice the project needs a balance of openness and control:

- The platform's credibility rests on transparency about a narrow set of things -
  where money comes from and goes, the governance and legal structure, and the
  neutrality and methodology policies. These are what let a reader trust that the
  platform is not captured or biased.
- It does not rest on the founder publishing every operational and strategic
  decision. Provider negotiations, who to approach for interviews, business
  development, growth strategy, and half-formed ideas are the founder's to
  disclose or not. Publishing them by default would offer no credibility benefit
  and would remove necessary room to operate.

Transparency is most valuable as a deliberate act on specific things, not as a
blanket setting applied to everything.

## Decision

Amend the transparency principle in 0004 to distinguish published, private-but-
tracked, and secret information.

- **Published:** decisions concerning money (sources and uses) and editorial
  independence (neutrality, methodology, governance, legal structure). These live
  in the public meta-repo and on the website.
- **Private but tracked:** operational and strategic decisions - providers,
  account management, business development, positioning, and the like. These live
  in the private `operations` repository. The founder may graduate a
  specific item to the published tier when it serves the mission.
- **Secret:** credentials, in Bitwarden, never in any repository.

The product itself - code, data, and the architecture decision records that
govern them - remains public as 0004 intends. This amendment narrows only the
"all operational decisions will be public" clause.

## Consequences

The transparency claim becomes precise and defensible: the things that matter for
trust are public, and the founder retains room to operate. A private
`operations` repository becomes the home for the private-but-tracked
tier. When promoted to a numbered record, this supersedes the relevant clause of
0004; 0004 itself is annotated with a pointer to the superseding record rather
than edited in place.
