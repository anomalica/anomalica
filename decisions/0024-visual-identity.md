# 0024. Visual identity

Date: 2026-03-27
Status: accepted

## Context

The platform needs a visual identity that reflects its values: neutral, scholarly, jurisdiction-independent, and accessible across all supported languages and scripts. The identity needs to work at every scale from favicon to printed material, and avoid associations with conspiracy aesthetics, government/military imagery, or Silicon Valley startup conventions.

## Decision

### Logo

The logo is a triangle with rounded corners. It is used in two forms:

- **Mark** - the triangle alone, used as favicon, app icon, and small-context identifier. Defined in `brand/anomalica-mark.svg` (a scalable vector graphics file).
- **Wordmark** - the triangle followed by "nomalica" in Outfit Regular, where the triangle serves as the letter "A". Defined in `brand/anomalica-logo.svg`.

Both files contain black paths with no colour or font dependencies. Colour is applied in context.

The triangle was chosen for its simplicity and because it carries relevant associations without being explicit about any of them: it echoes commonly reported unidentified anomalous phenomena shapes, ancient structures, and the act of looking upward. It does not declare any of these connections. It is deliberately simple enough to work at any size, in any medium, and to be memorable without being complex.

### Colour

The primary palette is a deep teal, chosen for its associations with depth, neutrality, and quiet authority. It avoids the sensationalism of red/orange, the government associations of navy blue, and the conspiracy associations of black/green.

Primary teal range:
- Midnight: #031F1F
- Deep Sea: #064D4D
- Deep Teal: #0B6E6E (primary brand colour)
- Teal: #14A3A3
- Light Teal: #72D3D3
- Ice: #D1F1F1

Warm neutrals:
- Ink: #1E1D19
- Slate: #5E5A50
- Stone: #B5B0A6
- Fog: #D6D2C9
- Bone: #E9E5DC
- Paper: #F8F6F1

Accents:
- Copper: #B35A28
- Light Copper: #D4915E
- Amber: #D49F3D

### Typography

Two font families only:

- **Outfit** - used for the wordmark, navigation, buttons, labels, and user interface chrome. A geometric sans-serif with clean proportions and personality. Not used for article body text.
- **Noto Sans** - used for all content: article headings, body text, source citations, footnotes. Script-specific variants (Noto Sans JP, Noto Sans Arabic, Noto Sans Devanagari, etc.) are loaded per language. Noto was chosen because it covers every script required by the platform's supported languages with visual consistency across all of them.

### Name treatment

The name is written as **Anomalica** (capital A) in running text. The wordmark uses the triangle as the "A" followed by lowercase "nomalica".

The preferred lockup for name plus descriptor is inline with separator:

Anomalica | Encyclopaedia of Anomalous Phenomena

## Consequences

The two-font approach keeps page weight low and ensures visual consistency across all supported languages. Noto Sans variants are loaded per-language via stylesheet unicode-range rules, so readers only download the glyphs their language needs.

The logo vector graphics files are the definitive reference for rendering. Any reproduction should be derived from these files rather than recreated.

The colour palette is defined as hex values. Pantone equivalents are not required while the platform is digital-only but can be matched if physical materials are needed in future.

Working brand assets (interactive brand board, typography samples, language coverage analysis) are maintained separately and may move or change format over time. This decision record is the authoritative reference for the visual identity.
