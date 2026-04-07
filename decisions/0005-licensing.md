# 0005. MIT licence for code, CC0 for data

Date: 2026-03-23
Status: accepted

## Context

The project needs a licensing strategy for both its code (the knowledge graph engine, the static site generator configuration, the assembly pipeline) and its data (the knowledge graph - a structured database of interconnected facts - assembled articles, and extracted claims).

Options considered:
- **Affero General Public Licence** for code - requires anyone who modifies and runs the code as a service to share their modifications. Strongest copyleft (a licensing approach that requires derivative works to use the same licence terms).
- **General Public Licence** for code - requires sharing modifications when distributing, but has a loophole for software run as a service.
- **MIT** for code - permissive, no restrictions beyond attribution and liability disclaimer.
- **CC BY-SA** for data - requires attribution and share-alike for derivative works.
- **CC0** for data - public domain dedication, no restrictions at all.

## Decision

**MIT licence** for all code. **CC0 (public domain)** for all data.

The platform's purpose is to make information freely available. Restrictive licensing contradicts that purpose. Specific reasoning:

- The project has no resources to enforce a restrictive licence.
- Artificial intelligence tools can read and reimplement code regardless of licence, reducing the practical value of copyleft.
- Permissive licensing removes friction for contributors and users.
- The data (knowledge graph, claims, articles) is intended as a public good. Restricting its use would be contrary to the project's aims. The data is constantly evolving, so a static copy has limited value anyway.
- The platform's real value is not in the code or a snapshot of the data, but in being the living, trusted, evolving source. That cannot be duplicated by copying files.

## Consequences

Anyone can take the code, modify it, and use it for any purpose including commercial use, with no obligation to share changes back. Anyone can take the data and use it for any purpose with no restrictions.

Contributors should be aware that their contributions will be released under these terms.
