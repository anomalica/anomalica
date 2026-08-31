#!/usr/bin/env python3
"""Refresh model prices in architecture/model-policy.yaml from OpenRouter.

The policy file is the single table: the public model-policy page renders it and
every component picks its model through it. Prices in it went stale twice in one
week - Opus 5 was carried at 3x its real cost, and a fifth of a shared price table
was wrong, some of it UNDER-stated, which makes a spend gate authorise more than
it says. A hand-maintained copy of someone else's prices is wrong the moment they
change it and nothing here can notice.

OpenRouter's /api/v1/models carries every provider we use, Anthropic included, so
one call refreshes the whole table. Prices are USD per million tokens.

Reports what changed and writes `prices_checked`. Never invents a price: a model
the API does not list keeps its recorded value and is named in the output, because
silently leaving a stale number is how this started.
"""

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

import yaml

POLICY = Path(__file__).resolve().parents[1] / "architecture" / "model-policy.yaml"
API = "https://openrouter.ai/api/v1/models"
# Claude ids in the policy are the vendor's own; OpenRouter namespaces them.
# The vendor writes claude-haiku-4-5; OpenRouter writes claude-haiku-4.5. Mapped
# explicitly rather than by a rule, so a new model is NOT LISTED (loud) rather
# than silently matched by a guess.
ALIASED = {
    "claude-opus-5": "anthropic/claude-opus-5",
    "claude-sonnet-5": "anthropic/claude-sonnet-5",
    "claude-haiku-4-5": "anthropic/claude-haiku-4.5",
    "claude-fable-5": "anthropic/claude-fable-5",
}


def live_prices() -> dict[str, tuple[float, float]]:
    with urllib.request.urlopen(API, timeout=30) as r:
        data = json.load(r)["data"]
    out = {}
    for m in data:
        p = m.get("pricing") or {}
        try:
            out[m["id"]] = (float(p["prompt"]) * 1e6, float(p["completion"]) * 1e6)
        except (KeyError, TypeError, ValueError):
            continue
    return out


def main() -> int:
    prices = live_prices()
    doc = yaml.safe_load(POLICY.read_text())
    changed, missing = [], []

    for model in doc["models"]:
        mid = model["id"]
        lookup = ALIASED.get(mid, mid)
        live = prices.get(lookup)
        if live is None:
            missing.append(mid)
            continue
        old = model.get("price") or {}
        new = {"input": round(live[0], 4), "output": round(live[1], 4)}
        if (old.get("input"), old.get("output")) != (new["input"], new["output"]):
            changed.append((mid, old, new))
            model["price"] = new

    doc["prices_checked"] = date.today().isoformat()
    header = POLICY.read_text().split("schema:")[0]
    POLICY.write_text(
        header + yaml.dump(doc, sort_keys=False, allow_unicode=True, width=100)
    )

    for mid, old, new in changed:
        was = f"{old.get('input')}/{old.get('output')}" if old else "unpriced"
        print(f"  changed  {mid:28s} {was} -> {new['input']}/{new['output']}")
    for mid in missing:
        print(f"  NOT LISTED, kept as recorded: {mid}", file=sys.stderr)
    print(
        f"{len(changed)} changed, {len(missing)} not listed, {len(doc['models'])} total"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
