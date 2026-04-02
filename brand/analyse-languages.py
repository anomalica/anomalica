#!/usr/bin/env python3
"""
Greedy set-cover analysis of world languages using Unicode CLDR data.

For each territory, CLDR provides the percentage of the population that
speaks each language. This script greedily selects languages to maximise
the number of literate people covered, accounting for overlap (people
who speak multiple languages are only counted once).

Data source: Unicode CLDR supplementalData.xml
https://github.com/unicode-org/cldr/blob/main/common/supplemental/supplementalData.xml
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CLDR_FILE = Path("/tmp/cldr-supplemental.xml")
OUTPUT_JSON = Path(__file__).parent / "language-coverage.json"

# Map CLDR language codes to readable names
LANG_NAMES = {
    "en": "English",
    "zh": "Mandarin",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "ar": "Arabic",
    "bn": "Bengali",
    "pt": "Portuguese",
    "id": "Indonesian",
    "ur": "Urdu",
    "ru": "Russian",
    "de": "German",
    "ja": "Japanese",
    "mr": "Marathi",
    "vi": "Vietnamese",
    "te": "Telugu",
    "sw": "Swahili",
    "tr": "Turkish",
    "ha": "Hausa",
    "tl": "Tagalog",
    "ta": "Tamil",
    "fa": "Persian",
    "ko": "Korean",
    "am": "Amharic",
    "th": "Thai",
    "it": "Italian",
    "kn": "Kannada",
    "yo": "Yoruba",
    "ps": "Pashto",
    "gu": "Gujarati",
    "pl": "Polish",
    "ig": "Igbo",
    "my": "Burmese",
    "uk": "Ukrainian",
    "ml": "Malayalam",
    "or": "Odia",
    "om": "Oromo",
    "uz": "Uzbek",
    "pa": "Punjabi",
    "nl": "Dutch",
    "ms": "Malay",
    "ku": "Kurdish",
    "zu": "Zulu",
    "ceb": "Cebuano",
    "ro": "Romanian",
    "ne": "Nepali",
    "mg": "Malagasy",
    "sd": "Sindhi",
    "km": "Khmer",
    "hu": "Hungarian",
    "el": "Greek",
    "sv": "Swedish",
    "cs": "Czech",
    "sr": "Serbian",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "nb": "Norwegian",
    "nn": "Norwegian",
    "is": "Icelandic",
    "si": "Sinhala",
    "he": "Hebrew",
    "fil": "Filipino",
    "rw": "Kinyarwanda",
    "sn": "Shona",
    "xh": "Xhosa",
    "af": "Afrikaans",
    "ny": "Chichewa",
    "so": "Somali",
    "lo": "Lao",
    "ka": "Georgian",
    "az": "Azerbaijani",
    "tk": "Turkmen",
    "ky": "Kyrgyz",
    "kk": "Kazakh",
    "sq": "Albanian",
    "hy": "Armenian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sk": "Slovak",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
    "mk": "Macedonian",
    "bs": "Bosnian",
    "sl": "Slovenian",
    "zh_Hant": "Mandarin",
    "zh_Hans": "Mandarin",
    "yue": "Cantonese",
    "yue_Hans": "Cantonese",
    "wuu": "Wu Chinese",
    "nan": "Min Nan",
    "su": "Sundanese",
    "jv": "Javanese",
    "mad": "Madurese",
    "pcm": "Nigerian Pidgin",
}


# CLDR uses sub-language codes like "zh_Hant" or "uz_Arab".
# We normalise to base language for grouping.
def normalise_lang(code):
    """Map CLDR language code to a canonical base code."""
    # Handle script variants - group Chinese variants together, etc.
    base = code.split("_")[0]

    # Norwegian: nb and nn are both Norwegian
    if base in ("nb", "nn"):
        return "no"

    # Filipino/Tagalog
    if base == "fil":
        return "tl"

    return base


def parse_cldr(path):
    """Parse CLDR supplementalData.xml and return territory-language data."""
    tree = ET.parse(path)
    root = tree.getroot()

    territories = []
    for t in root.findall(".//territory"):
        code = t.get("type")
        pop = int(t.get("population", "0"))
        literacy = float(t.get("literacyPercent", "50")) / 100.0

        if pop < 1000:
            continue

        langs = {}
        for lp in t.findall("languagePopulation"):
            lang_code = normalise_lang(lp.get("type"))
            pct = float(lp.get("populationPercent", "0")) / 100.0

            # Use the higher percentage if a language appears multiple times
            # (e.g., zh and zh_Hant in the same territory)
            if lang_code in langs:
                langs[lang_code] = max(langs[lang_code], pct)
            else:
                langs[lang_code] = pct

        territories.append(
            {
                "code": code,
                "population": pop,
                "literacy": literacy,
                "languages": langs,
            }
        )

    return territories


def greedy_coverage(territories, max_languages=60):
    """
    Greedy set-cover: repeatedly pick the language that covers the most
    literate people not yet covered by any previously selected language.

    For each territory, we track which fraction of the literate population
    is already covered. When a new language is added, it covers additional
    people in every territory where it's spoken, but only those not already
    covered by a previously selected language.

    The overlap model: within a territory, if languages A and B are both
    spoken, we assume speakers of A and B overlap proportionally. So if
    60% speak A and 40% speak B, the union is 1 - (1-0.6)*(1-0.4) = 76%,
    not 100%. This is the independence assumption - not perfect, but a
    reasonable default when we lack per-territory co-occurrence data.
    """
    # For each territory, track the probability that a random literate
    # person is NOT yet covered by any selected language.
    uncovered = {}
    for t in territories:
        literate_pop = t["population"] * t["literacy"]
        if literate_pop > 0:
            uncovered[t["code"]] = {
                "literate_pop": literate_pop,
                "prob_uncovered": 1.0,
                "languages": t["languages"],
            }

    # Collect all candidate language codes
    all_langs = set()
    for t in territories:
        all_langs.update(t["languages"].keys())

    selected = []
    total_literate = sum(u["literate_pop"] for u in uncovered.values())
    covered_so_far = 0

    for rank in range(max_languages):
        # Find the language that would cover the most currently-uncovered people
        best_lang = None
        best_gain = 0

        for lang in all_langs:
            gain = 0
            for tcode, tdata in uncovered.items():
                if lang in tdata["languages"]:
                    speak_pct = tdata["languages"][lang]
                    # New coverage = literate_pop * prob_uncovered * speak_pct
                    gain += tdata["literate_pop"] * tdata["prob_uncovered"] * speak_pct
            if gain > best_gain:
                best_gain = gain
                best_lang = lang

        if best_lang is None or best_gain < 1000:
            break

        # Update uncovered probabilities
        for tcode, tdata in uncovered.items():
            if best_lang in tdata["languages"]:
                speak_pct = tdata["languages"][best_lang]
                # Probability of being uncovered decreases
                tdata["prob_uncovered"] *= 1.0 - speak_pct

        covered_so_far += best_gain
        coverage_pct = covered_so_far / total_literate * 100

        # Get total speakers across all territories for this language
        total_speakers = 0
        for tdata in uncovered.values():
            if best_lang in tdata["languages"]:
                total_speakers += tdata["literate_pop"] * tdata["languages"][best_lang]

        name = LANG_NAMES.get(best_lang, best_lang)

        selected.append(
            {
                "rank": rank + 1,
                "code": best_lang,
                "name": name,
                "total_speakers_m": round(total_speakers / 1_000_000),
                "incremental_m": round(best_gain / 1_000_000),
                "cumulative_m": round(covered_so_far / 1_000_000),
                "coverage_pct": round(coverage_pct, 1),
            }
        )

        all_langs.discard(best_lang)

    return selected, round(total_literate / 1_000_000)


def main():
    if not CLDR_FILE.exists():
        print(f"CLDR data not found at {CLDR_FILE}", file=sys.stderr)
        print(
            "Download from: https://github.com/unicode-org/cldr/blob/main/common/supplemental/supplementalData.xml",
            file=sys.stderr,
        )
        sys.exit(1)

    territories = parse_cldr(CLDR_FILE)
    print(f"Parsed {len(territories)} territories", file=sys.stderr)

    results, total_literate = greedy_coverage(territories, max_languages=60)

    output = {
        "source": "Unicode CLDR supplementalData.xml (2026)",
        "methodology": "Greedy set-cover with independence assumption for bilingual overlap",
        "total_literate_population_m": total_literate,
        "languages": results,
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nTotal literate world population: {total_literate:,}M", file=sys.stderr)
    print(f"\nResults written to {OUTPUT_JSON}", file=sys.stderr)
    print(
        f"\n{'#':>3}  {'Language':<20} {'Total M':>8} {'Incr M':>8} {'Cumul M':>8} {'Cover%':>7}",
        file=sys.stderr,
    )
    print("-" * 70, file=sys.stderr)
    for r in results:
        marker = " <--" if r["rank"] == 30 else ""
        print(
            f"{r['rank']:>3}  {r['name']:<20} {r['total_speakers_m']:>7}M {r['incremental_m']:>7}M {r['cumulative_m']:>7}M {r['coverage_pct']:>6.1f}%{marker}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
