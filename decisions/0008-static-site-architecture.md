# 0008. Serve the platform as a static website

Date: 2026-03-20
Status: accepted

## Context

The platform needs to present assembled articles to the public. The hosting strategy requires resilience against takedown attempts and the ability to handle unpredictable traffic spikes with minimal infrastructure.

## Decision

Serve the platform as a static website - pre-built HTML, CSS, and JavaScript files with no server-side application processing requests. Articles are assembled offline from the knowledge graph and built into static files that are then deployed.

Reasons:
- **Replication** - a static site is just a folder of files. It can be copied, mirrored, or redeployed to any hosting provider in minutes.
- **Resilience** - there is no central application server that can be overwhelmed or taken down. Content delivery networks distribute the files globally and handle traffic spikes by design.
- **Cost** - serving static files is significantly cheaper than running application servers.
- **Security** - there is no running application to exploit. The attack surface is reduced to the hosting provider and DNS.

Interactive features (search, maps, language switching, unit conversion) will be handled client-side with lightweight JavaScript.

## Consequences

Dynamic features that require server-side processing (such as semantic search or submission forms) will need to be handled separately as optional serverless functions. The static site must never depend on these - they degrade gracefully if unavailable.

Content updates require a rebuild and redeploy rather than editing a live database.
