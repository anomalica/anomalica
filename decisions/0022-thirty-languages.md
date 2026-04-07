# 0022. Supported languages

Date: 2026-03-27
Status: accepted

## Context

Existing platforms covering unidentified anomalous phenomena and non-human intelligence are overwhelmingly English-only. GEIPAN (France) is the only significant non-English resource. The platform's position as international and not American-centric requires genuine multilingual support, not English-first with translations added later.

## Methodology

Languages are ranked by incremental coverage using data from the Unicode Common Locale Data Repository, an open dataset maintained by the Unicode Consortium. For each of 244 territories, the dataset provides the percentage of the population that speaks each language, the territory's total population, and its literacy rate.

The selection algorithm is a greedy set-cover: at each step, the language that would cover the most currently-uncovered literate people across all territories is chosen. Overlap between languages within a territory is modelled using an independence assumption (if 60% speak language A and 40% speak language B, combined coverage is 76%, not 100%).

The analysis is reproducible. The script (`brand/analyse-languages.py`), source data, and output (`brand/language-coverage.json`) are in the repository. The methodology and results are published on the site as part of the platform's transparency commitments.

**Caveat:** The locale data measures functional language populations, which includes spoken fluency. For some languages, the number of people who read and write the language is lower than the number who speak it. The editorial adjustments below address these cases.

Mandarin Chinese is treated as one translation with two rendering variants: Simplified (mainland China, Singapore, Malaysia) and Traditional (Taiwan, Hong Kong, Macau). The conversion between character sets is a mechanical transformation, not a separate translation. Traditional Chinese is not counted as a separate language but is always produced alongside Simplified.

## Decision

The supported set is determined by the algorithmic ranking with three editorial adjustments.

**Algorithmic ranking (top 27):**

 1. English - 1,397M incremental - 21.4% cumulative
 2. Mandarin Chinese - 1,247M - 40.6%
 3. Spanish - 379M - 46.4%
 4. Hindi - 295M - 50.9%
 5. Arabic - 221M - 54.3%
 6. Portuguese - 198M - 57.4%
 7. Russian - 191M - 60.3%
 8. Indonesian - 166M - 62.8%
 9. French - 150M - 65.1%
10. Japanese - 116M - 66.9%
11. Bengali - 113M - 68.6%
12. Urdu - 85M - 69.9%
13. Swahili - 85M - 71.2%
14. Vietnamese - 84M - 72.5%
15. Korean - 74M - 73.7%
16. Turkish - 62M - 74.6%
17. Persian - 61M - 75.6%
18. Thai - 37M - 76.1%
19. German - 36M - 76.7%
20. Burmese - 34M - 77.2%
21. Italian - 30M - 78.2%
22. Uzbek - 27M - 78.6%
23. Telugu - 27M - 79.0%
24. Marathi - 24M - 79.4%
25. Tamil - 22M - 79.7%
26. Polish - 17M - 80.0%
27. Tagalog - 17M - 80.2%

**Excluded from algorithmic ranking:**

Three languages that appear in the top 30 algorithmically are excluded:

- **Javanese** (algorithm rank 21, 32M incremental): primarily a spoken language. Most literate Javanese speakers read and write in Indonesian, which is supported at position 8.
- **Malay** (algorithm rank 27, 17M incremental): Malay and Indonesian are mutually intelligible in written form. Indonesian is supported at position 8. Malaysian readers can access Indonesian content and vice versa. Supporting both would produce near-identical output.
- **Nigerian Pidgin** (algorithm rank 30, 14M incremental): a pidgin language used primarily for spoken communication, not a standard written language for reference works. Speakers are covered by English.

**Added by editorial decision:**

- **Ukrainian** (algorithm rank 33, 13M incremental): Ukrainian is included by editorial decision because the platform does not wish to support Russian without Ukrainian during an active conflict between the two countries.

**Final supported set:** 28 translations producing 30 displayed languages. The 28 translations come from the algorithmic top 30 (minus 3 excluded) plus Ukrainian. Two additional displayed languages are produced by mechanical conversion, not separate translation:

- **Traditional Chinese** - character conversion from Simplified Chinese (Mandarin, position 2)
- **American English** - spelling and formatting conversion from British English (position 1)

Total coverage of literate world population: approximately 80%.

## Consequences

30 languages multiplied by thousands of articles produces hundreds of thousands of pages. This is the primary driver behind the Hugo choice (decision 0014) - build performance at this scale eliminates most other frameworks.

Script support requires multiple script families, all covered by the Noto Sans font family: Latin, Devanagari, Arabic, Nastaliq, Bengali, Cyrillic, Han (Simplified and Traditional), Kana, Hangul, Thai, Tamil, Telugu, Ge'ez, Myanmar, and Hangul.

Arabic, Persian, and Urdu require right-to-left layout support. Chinese, Japanese, and Korean require appropriate font loading and affect search tokenisation.

Artificial intelligence translation quality varies by language. High-resource languages (the top 15-20) produce reliable translations. Lower-resource languages (Burmese, Uzbek) may initially produce lower-quality output and should be flagged accordingly in metadata. Translation quality is expected to improve over time as language models advance.

Translation corrections are handled through the directive system. Community members edit articles in their language, and the changes are extracted as durable directives that persist across reassembly.
