# 0015. Hosting strategy and graceful degradation

Date: 2026-03-21
Status: accepted

## Context

The platform publishes information about programmes that may attract adversarial attention at a state level. The hosting strategy needs to ensure continuity of service under pressure while keeping costs sustainable for a self-funded project.

Research was conducted into censorship-resistant hosting providers (FlokiNET, Bahnhof, 1984 Hosting), content delivery network options (bunny.net, Cloudflare, KeyCDN), and case studies of platforms under pressure (WikiLeaks, Sci-Hub, The Pirate Bay). A content delivery network distributes copies of files to servers around the world so readers download from a nearby location rather than a single central server.

## Decision

The site is designed in three layers that degrade gracefully:

| Layer | Function | If lost |
|-------|----------|---------|
| Core (static HTML on content delivery network) | Articles, search, maps | Site is down, but data survives |
| Enhanced (serverless) | Semantic search, advanced filtering | Site works fully, only semantic search lost |
| Data (downloadable SQLite database) | Complete knowledge graph | Distributed copies persist |

Primary content delivery network: bunny.net (Slovenian jurisdiction, not venture-funded). No pre-paid backup hosting - the static site architecture means redeployment to any provider takes minutes. A temporary takedown is itself noteworthy and signals interference.

The SQLite knowledge graph (a structured database of interconnected facts stored as a lightweight file-based database) is downloadable directly from the website. Each release is versioned, cryptographically signed, and available via BitTorrent and distributed file networks.

Code hosted on a public git platform with at least one mirror on a different provider and jurisdiction.

Email via Proton Mail (Swiss jurisdiction) on the anomalica.is domain.

## Consequences

Infrastructure costs are low (estimated 15,000-25,000 yen/month including domains, content delivery network, and email). The architecture is designed so that no single provider failure or takedown can permanently destroy the platform or its data.
