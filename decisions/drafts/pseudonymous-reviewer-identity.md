# Pseudonymous reviewer identity

Date: 2026-04-13
Status: draft

## Context

Reviewers submit corrections to ingests and digests. These corrections are stored as git commits and need attribution for audit purposes. But reviewers may not want their real names publicly associated with corrections to records about sensitive topics. Some reviewers may be military personnel, government officials, or journalists who need to protect their identities.

The system needs to balance accountability (knowing which corrections came from which reviewer) with privacy (not exposing reviewer identities without consent).

Options considered:

- **Real names in git commits.** Simple but exposes reviewer identity in the git history permanently. GDPR right to erasure would require rewriting git history.
- **Pseudonymous hashes with an optional mapping.** Commits use a one-way hash of the reviewer's email. A separate mapping (encrypted, outside git) resolves hashes to names for those who opt in. Deletion means removing the mapping entry - commits become anonymous.
- **Fully anonymous.** No attribution at all. Prevents accountability and contributor recognition.

## Decision

Reviewers are identified in git commits by a one-way hash of their email address: `SHA-256(salt + email)`, truncated to 8 hex characters. The salt is a fixed public string (`anomalica-reviewers`).

```
Author: a1b2c3d4 <a1b2c3d4@reviewers.anomalica.is>
Committer: Anomalica Workbench <workbench@anomalica.is>
```

Each reviewer controls their visibility through four tiers:

| Tier | Who can see their real name | Stored in mapping |
|------|----------------------------|-------------------|
| **None** (default) | Nobody | No entry |
| **Internal** | Anomalica project members | Yes |
| **Reviewers** | Other logged-in reviewers | Yes |
| **Public** | Anyone | Yes |

The mapping file is encrypted at rest and stored outside git (see the hosting jurisdiction decision for storage details). Entries look like:

```yaml
salt: anomalica-reviewers
identities:
  a1b2c3d4:
    display_name: Jane Smith
    visibility: reviewers
```

The backend discards the reviewer's plaintext email after computing the hash. No email addresses are stored on the server. The OAuth session is transient.

GDPR right to erasure is handled by removing the mapping entry. The pseudonymous hash in git commits is not personal data on its own (it cannot be reversed). Once the mapping entry is deleted, the commits are effectively anonymous.

## Consequences

- Reviewers are protected by default. No action required for anonymity.
- The reviewer's browser can compute the same hash from their OAuth session, enabling "your reviews" features without the server storing identity.
- The mapping file is a high-value target and must be encrypted and stored in a secure jurisdiction.
- Authentication via OAuth (Google, GitHub, etc.) is required to establish the email for hashing. Multiple providers are supported - reviewers do not need a GitHub account.
- The git commit authorship convention (`Author` vs `Committer`) is the same as used by git hosting platforms for merged pull requests.
