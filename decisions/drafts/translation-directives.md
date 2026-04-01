# Translation quality via directives

Date: 2026-03-21
Status: draft

## Context

AI-translated articles will contain errors - grammatical mistakes, incorrect terminology, unnatural phrasing. Community members who speak a language natively can identify and correct these. But corrections stored as text overrides are fragile - they break when the underlying English content changes and the article is regenerated.

Edits to articles should not be a channel for introducing new factual information. New facts enter through the source submission pipeline only.

## Decision

Translation corrections will be extracted as **directives** - persistent rules about how to translate or express content in a specific language. Directives will be stored in the article's frontmatter and persist across regeneration cycles.

When a user edits a translated article:
1. The AI will analyse the diff and categorise the changes.
2. Factual additions will be rejected (redirect to source submission pipeline).
3. Quality improvements will be extracted as directives.
4. The AI will regenerate the translation from scratch, applying all directives including the new ones.
5. If the regenerated output substantially matches the user's edit, the directives will be confirmed as correct.
6. If the output differs substantially, the edit will be flagged for review.

Two edit interfaces will be available: users will be able to write directives directly, or edit the article text and let the AI extract directives from the diff.

## Consequences

Corrections will not be lost to regeneration. The verification loop (regenerate from directives, compare to user's edit) will confirm that directives correctly capture the user's intent. Each directive will get its own commit for clean, auditable history.

The system will also act as a safeguard - adversarial edits will need to pass through directive extraction and regeneration verification, making it difficult to silently alter article content.
