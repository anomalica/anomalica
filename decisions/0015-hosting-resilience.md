# 0015. Graceful degradation and data survivability

Date: 2026-03-21
Status: accepted

## Context

The platform publishes information that may attract adversarial attention at a state level. The architecture must ensure the data and the core reading experience survive pressure, while keeping costs sustainable for a donation-funded project. The specific hosting providers, content-delivery network, email, and jurisdiction choices are operational and live in the `operations` repository; this record covers the architectural resilience they serve (the public commitment is the resilience principle in the governance charter).

## Decision

The site is designed in three layers that degrade gracefully:

| Layer | Function | If lost |
|-------|----------|---------|
| Core (static HTML on a content delivery network) | Articles, search, maps | Site is down, but data survives |
| Enhanced (serverless) | Semantic search, advanced filtering | Site works fully, only semantic search lost |
| Data (downloadable SQLite database) | Complete knowledge graph | Distributed copies persist |

The static-site architecture (decision 0014) means redeployment to any provider takes minutes, so no pre-paid backup hosting is needed; a temporary takedown is itself noteworthy and signals interference.

The SQLite knowledge graph (a lightweight file-based database) is downloadable directly from the site. Each release is versioned, cryptographically signed, and available via BitTorrent and distributed file networks, so the complete dataset survives independently of any single host.

Code is hosted on a public git platform with at least one mirror on a different provider and jurisdiction.

## Consequences

- The data outlives the platform: signed, versioned, distributed copies of the knowledge graph persist even if the site is taken down.
- The core reading experience depends only on static files on a content delivery network; the enhanced (serverless) features degrade gracefully and the site must never hard-depend on them.
- The specific provider, content-delivery-network, email, and jurisdiction choices live in the `operations` repository.
