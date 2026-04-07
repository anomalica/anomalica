# 0017. Website analytics

Date: 2026-03-31
Status: accepted

## Context

Anomalica needs to understand how people use the site - which articles are read, where visitors come from, and how the site grows over time. This data also feeds back into the assembly pipeline: page view counts can surface popular articles on the homepage and help prioritise content work.

However, the project has a strong privacy stance (see 0004) and operates across jurisdictions (see 0002). Analytics must not compromise visitor privacy, must not require cookie consent banners, and should align with General Data Protection Regulation (GDPR) and ePrivacy Directive requirements.

The main options considered were:

- **Umami** - open source (MIT), self-hostable, cookieless. US-based company (San Francisco), venture capital funded. Already used on a separate project.
- **GoatCounter** - open source (European Union Public Licence), self-hostable, cookieless. Created by Martin Tournoij, based in Ireland. Solo developer, funded through GitHub Sponsors and paid tiers.
- **Plausible** - open source (Affero General Public Licence), self-hostable, cookieless. EU-based (Estonia). Hosted plans from 9 USD/month.
- **Cloudflare Web Analytics** - free, cookieless. US-based, closed source. Sampled data (not actual traffic), limited retention.
- **Google Analytics** - rejected outright. Requires cookies, consent banners, and sends data to a US advertising company.

Key evaluation criteria: GDPR compliance without consent banners, open source licence, self-hosting capability, jurisdiction alignment, long-term sustainability, and programmatic data access for the assembly pipeline.

## Decision

Use GoatCounter for website analytics, self-hosted on EU infrastructure.

GoatCounter was chosen over Umami and other alternatives for these reasons:

1. **Jurisdiction.** GoatCounter is developed in Ireland (EU) and uses the European Union Public Licence (a copyleft licence originating from the EU). This aligns with Anomalica's jurisdiction-independent stance and avoids dependency on US-based companies.

2. **Sustainability.** GoatCounter is a solo developer project funded through GitHub Sponsors and paid hosting tiers. This is more predictable than venture capital funding, which creates pressure to change direction when investors need returns.

3. **Simplicity.** GoatCounter is a single Go binary with SQLite storage (a lightweight file-based database). No Node.js runtime, no external database dependencies. This reduces the operational surface and makes self-hosting straightforward.

4. **Pipeline integration.** GoatCounter provides a web-based programming interface with cursor-based export for incremental syncing. When self-hosted, the SQLite database can also be queried directly. This allows the assembly pipeline to read page view data and surface popular articles.

5. **Privacy.** GoatCounter uses no cookies, stores no personal data, and does not fingerprint devices. It is GDPR and ePrivacy compliant without requiring a consent banner. The privacy policy should mention that analytics are collected, but no opt-in mechanism is needed.

6. **No-JavaScript option.** GoatCounter supports a tracking pixel fallback for visitors who block JavaScript, providing basic page view counts without any client-side code.

The analytics script (or tracking pixel) will be added to the site when it is closer to going live. The implementation is a single script tag in the base template.

## Consequences

- A GoatCounter instance needs to be provisioned on EU infrastructure before the site launches.
- The privacy policy page should mention that cookieless, privacy-respecting analytics are collected and explain what data is gathered (page views, referrer, country-level location, browser type - all aggregated, no personal data).
- The assembly pipeline can query GoatCounter data to surface popular content, but this is a future enhancement that requires actual traffic to be meaningful.
- As a solo developer project, GoatCounter carries bus-factor risk. However, it is open source and simple enough to fork and maintain if needed.
