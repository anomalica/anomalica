# 0013. Domain registration strategy

Date: 2026-03-21
Status: accepted

## Context

The platform publishes information that may attract adversarial attention. Domain names are a single point of failure - US courts have seized .com, .net, and .org domains by compelling the US-based registries. The domain strategy needs to balance accessibility with resilience.

Research was conducted into top-level domain jurisdictions, registrar track records, and domain seizure case studies (WikiLeaks, Sci-Hub, The Pirate Bay).

## Decision

Register the following domains:

| Domain | Registrar | Purpose |
|--------|-----------|---------|
| anomalica.is | ISNIC (direct) | Primary. Icelandic jurisdiction. |
| anomalica.com | Porkbun | Defensive registration. |
| anomalica.org | Porkbun | Defensive registration. |

ISNIC was chosen for the primary domain because it is the Icelandic registry itself (no middleman), and Iceland has a demonstrated track record of resisting US domain takedown pressure. Domain registration privacy for individuals is enabled by default.

Porkbun was chosen for the defensive registrations for its straightforward pricing and transparent approach. These domains redirect to the primary and are not critical infrastructure.

An attempt to register anomalica.nl (Netherlands, SIDN registry) through Porkbun failed repeatedly. This may be retried through a different registrar.

## Consequences

The primary domain is outside US legal jurisdiction. Defensive registrations prevent squatting on the .com and .org. The .nl backup for jurisdictional diversity remains an open item.
