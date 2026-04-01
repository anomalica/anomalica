# Passphrase-based source identity with optional disclosure

Date: 2026-03-21
Status: draft

## Context

The platform will accept submissions from the public (Phase 2). Submitters need a way to authenticate for follow-up communication and to link multiple submissions, without being required to reveal their real-world identity.

Research was conducted into SecureDrop (7-word passphrase, used by NYT/Guardian/Washington Post), GlobaLeaks (16-digit receipt with ECC keypair and identity disclosure framework), and Signal (phone-number-based identity with sealed sender).

## Decision

Submitters will receive a seven-word passphrase (Diceware-style) on first submission. The passphrase will deterministically generate an Ed25519 keypair via Argon2id key derivation in the browser. The server will only see the public key.

Identity disclosure will have three states:
- **Undisclosed** - fully anonymous, platform knows only the public key
- **Optionally disclosed** - identity shared with platform reviewers but not public
- **Disclosed** - identity is public, submitter credited by name

Disclosure will always be the submitter's choice. Each transition is one-way (cannot revert to a less-disclosed state).

Submitters will be able to hold multiple passphrases for different purposes and cryptographically link them later by signing a linking statement with both private keys.

All cryptographic operations will use libsodium (not GPG/PGP) and happen in the browser. The passphrase and private key will never leave the submitter's device.

## Consequences

Anonymity will be the default. Real-world identity will never be required. The passphrase model (proven by SecureDrop) is accessible to non-technical users. Over time, pseudonymous identities will be able to accumulate credibility through consistent, high-quality submissions.
