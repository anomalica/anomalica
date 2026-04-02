# 0001. Record decisions

Date: 2026-03-21 (retroactive; the first batch of ADRs were written on this date to capture decisions already made)
Status: accepted

## Context

Decisions are made through conversation and research. Without a record, the reasoning behind choices is lost. Future contributors (human or AI) would need to rediscover the same ground.

Open-source projects such as Kubernetes, Rust, and Python use Architecture Decision Records (ADRs) to maintain a public, version-controlled log of significant decisions. This practice is well-established and proven at scale.

## Decision

Record significant decisions as sequentially numbered markdown files in `decisions/`. Each record follows the ADR format: Context, Decision, Consequences. Records are immutable once accepted - to change a decision, a new record is created that supersedes the old one.

Detailed technical specifications live separately in `specs/` and are referenced from ADRs where relevant.

## Consequences

Decisions become searchable, persistent, and auditable. Anyone can read the full reasoning behind every architectural and organisational choice from the project's founding.
