# Proposal: Pseudonymous identity system and backend infrastructure

## Overview

This proposal covers two connected decisions: how reviewers are identified in the system, and where the backend service that handles their identity runs. These are linked because the identity system's security guarantees depend on where the trust boundary sits.

## Pseudonymous identity

### Problem

Reviewers submit corrections to ingests and digests. These corrections are stored as git commits and need attribution for audit purposes. But reviewers may not want their real names publicly associated with corrections to records about sensitive topics (UAP/UFO disclosures, government programmes, intelligence operations). Some reviewers may be military personnel, government officials, or journalists who need to protect their identities.

### Design

Every reviewer is identified in git commits by a one-way hash of their email address:

```
Author: a1b2c3d4 <a1b2c3d4@reviewers.anomalica.is>
Committer: Anomalica Workbench <workbench@anomalica.is>
```

The hash is computed as `SHA-256(salt + email)`, truncated to 8 hex characters. The salt is a fixed public string (`anomalica-reviewers`). The salt prevents rainbow table attacks but does not need to be secret - its purpose is to make pre-computed hash tables useless.

The reviewer's browser can compute the same hash from their OAuth session, allowing the workbench to show "your reviews" without the server needing to store who they are.

### Visibility tiers

Each reviewer controls how identifiable they are. The options are:

| Tier | Who can see their real name | Where it's stored |
|------|----------------------------|-------------------|
| **None** (default) | Nobody | Nowhere - only the hash exists |
| **Internal** | Anomalica project members only | Encrypted mapping file |
| **Reviewers** | Other logged-in reviewers | Encrypted mapping file |
| **Public** | Anyone | Encrypted mapping file |

The mapping file stores entries like:

```yaml
salt: anomalica-reviewers
identities:
  a1b2c3d4:
    display_name: Jane Smith
    visibility: reviewers
  e5f6g7h8:
    display_name: Anonymous Contributor
    visibility: public
```

The workbench backend reads this file, decrypts it in memory, and filters entries based on the viewer's access level. The file is encrypted at rest - the storage provider cannot read it.

### Identity lifecycle

1. Reviewer logs in via OAuth (Google, GitHub, etc.)
2. Backend receives name and email from the OAuth provider
3. Backend computes `SHA-256(salt + email)`, discards the plaintext email
4. The hash goes into the session cookie and is used for git commits
5. On first login, the reviewer is prompted to choose a visibility tier
6. If they choose anything above "none", their display name is added to the encrypted mapping
7. To delete their identity: their entry is removed from the mapping. Git commits remain but are no longer resolvable to a name. Effectively anonymous.

### GDPR compliance

The right to erasure is handled by removing the mapping entry. The pseudonymous hash in git commits is not personal data on its own (it cannot be reversed without the mapping). Once the mapping entry is deleted, the commits are anonymous.

The backend never stores plaintext email addresses. The OAuth token exchange is transient - the email is seen momentarily during authentication, used to compute the hash, and discarded. No email addresses exist on the server after the request completes.

## Authentication

### OAuth providers

Authentication uses OAuth via Authlib. Multiple providers are supported:

- **Google** - widest reach, recommended default
- **GitHub** - convenient for developers
- Additional providers (Microsoft, institutional SSO) can be added later

Each provider requires a client ID and client secret, configured as environment variables. The OAuth flow:

1. Reviewer clicks "Log in with Google" (or GitHub, etc.)
2. Browser redirects to the provider's authorisation page
3. Provider redirects back with an authorisation code
4. Backend exchanges the code for the reviewer's name and email
5. Backend computes the identity hash, sets a signed session cookie
6. Subsequent requests include the cookie for authentication

### Session management

Sessions are stored in signed cookies (not server-side). The cookie contains:

- Identity hash (the pseudonymous ID)
- Display name (from OAuth, for showing in the UI during the session)
- Avatar URL (for display only)
- OAuth provider name (for the login flow)

The cookie is signed with a secret key held only by the backend. It cannot be tampered with. It expires after 30 days or on logout.

No server-side session store is needed. The backend is stateless except for the encryption key and service account credentials.

## Backend service (trust boundary)

### What it holds

The backend is the single trust boundary. Everything sensitive flows through it:

1. **Encryption key** for the identity mapping file
2. **Git service account credentials** for committing to anomalica-ingests and anomalica-digests
3. **OAuth client secrets** for Google, GitHub, etc.
4. **Session signing key** for the cookie

### What it does

- Authenticates reviewers via OAuth
- Serves ingests from the private repository (gated by copyright status and hash verification)
- Serves original source files (gated by copyright status)
- Accepts review submissions and creates git commits with pseudonymous authorship
- Resolves identity hashes to display names (based on the viewer's access level)

### Where it runs

**Production: Scaleway (France)**

Scaleway is a French cloud provider with data centres in Paris and Amsterdam. French jurisdiction, EU data protection law, outside the Five Eyes intelligence alliance.

Key reasons:
- **Jurisdiction**: France / EU. Not subject to US CLOUD Act or Five Eyes intelligence sharing agreements.
- **Secrets Manager**: Purpose-built service for storing encryption keys and credentials. The encryption key for the identity mapping is injected at runtime from Scaleway Secret Manager, never stored on disk.
- **Cost**: Small instances suitable for FastAPI start at a few euros per month.
- **No VPS management needed**: Scaleway Serverless Containers or a small managed instance can run the FastAPI app without operating system maintenance.

The static frontend (Svelte app) is served from **Bunny CDN** (Slovenian, EU), which is already in the Anomalica stack. The frontend contains no secrets and no sensitive logic - it is just HTML, CSS, and JavaScript.

**Local development: identical code**

The same `backend/` directory runs locally via `just dev`. The only differences are environment variables:

| Variable | Local | Production |
|----------|-------|------------|
| `INGESTS_PATH` | Local clone path | Not set (uses GitHub API) |
| `SOURCES_PATH` | Local sources directory | Object storage URL |
| `GITHUB_CLIENT_ID` | Dev OAuth app | Production OAuth app |
| `GITHUB_CLIENT_SECRET` | Dev secret | Production secret |
| `INGESTS_REMOTE` | Not set | `anomalica/anomalica-ingests` |
| `GITHUB_TOKEN` | Not set | Service account token |
| `IDENTITY_KEY` | Auto-generated locally | From Scaleway Secret Manager |

No containerisation is required. The same Python file runs in both environments.

## Architecture summary

```
Reviewer's browser
    |
    |  HTTPS
    v
Bunny CDN (Slovenia, EU)
    |  Serves static frontend (HTML/CSS/JS)
    |  No secrets, no sensitive logic
    |
    |  /api/* requests proxied to:
    v
Scaleway backend (France, EU)
    |  FastAPI application
    |  Holds: encryption key, OAuth secrets,
    |         git service account, session signing key
    |  Stores: nothing persistent (stateless)
    |  Reads:  identity mapping (encrypted, from Scaleway storage)
    |          ingests (from GitHub API via service account)
    |          source files (from Bunny Storage or local)
    |  Writes: git commits (to GitHub via service account)
    |
    v
GitHub (git hosting)
    |  anomalica-ingests (private)
    |  anomalica-digests (public)
    |  Commits authored by pseudonymous reviewer hash
    |  Commits committed by workbench service account
```

## What needs to change

| Component | Change |
|-----------|--------|
| **Backend (server.py)** | Add pseudonymous hash computation, update commit authorship |
| **Backend (auth.py)** | Add Google OAuth provider, discard plaintext email after hashing |
| **Frontend** | Add visibility tier selector, "your reviews" feature, mode indicator bar |
| **Identity mapping** | New encrypted file, not in git, stored in Scaleway Secret Manager or equivalent |
| **Infrastructure** | Scaleway account, DNS configuration, Bunny CDN proxy rules |
| **Meta-repo** | Update architecture docs, add ADR for identity system |

## Risks

- **OAuth provider outage**: if Google/GitHub is down, reviewers cannot log in. Mitigated by supporting multiple providers.
- **Encryption key loss**: if the Scaleway Secret Manager key is lost, the identity mapping is unrecoverable. Mitigated by key backup procedures.
- **Single backend instance**: if the Scaleway instance is down, reviews cannot be submitted. Acceptable for the current scale. Can be scaled later.
- **Scaleway jurisdiction change**: France is currently strong on data protection. If this changes, the backend can be moved to Switzerland (Infomaniak) or another EU provider without code changes - only infrastructure configuration.

## Recommendation

Adopt this proposal. The pseudonymous identity system protects reviewers by default while allowing optional identification. The trust boundary is clearly defined (one backend service in EU jurisdiction) and the deployment path from local development to production requires no code changes.
