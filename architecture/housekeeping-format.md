# Housekeeping proposal format

The interchange contract between the housekeeping worker (which proposes) and the
workbench (which lets a human decide). One file per record:

```
ingests/store/{content_hash}.housekeeping.json
```

Beside `{content_hash}.md` and `{content_hash}.verification.json`, following the
sidecar precedent already in the store. Committed to `ingests`, which is how a
proposal written on Mark's machine reaches the deployed workbench.

See [housekeeping.md](housekeeping.md) for what the pass is and why. This document
is the file shape.

## Worked example

The real record `1d24cbe9…` is the case the whole component exists for. Its
frontmatter today:

```yaml
title: 'UFOs in Australia – Eyewitnesses Talk to Dr. James E. McDonald During His Investigative Tour (1967)'
publisher: 'Eyes On Cinema'
source_url: 'https://www.youtube.com/watch?v=8NIy61DkTWw'
date_published: '2026-08-11'
source_type: 'video'
```

Three things are wrong, and they are wrong in a way no rule can fix. `Eyes On Cinema`
is a channel that reposts archival footage, so it is the **copy**, not the publisher.
`2026-08-11` is when that channel uploaded it, not when the work was published - the
title says 1967. And the actual publisher is unknown until someone looks.

The sidecar that proposes the correction:

```json
{
  "schema": "anomalica/housekeeping/1",
  "content_hash": "sha256:1d24cbe9e49ad5279cd4975a2b37b3b3ab60a260be30a9264e34ef168d7f9e0e",
  "checked_at": "2026-08-19T19:40:11Z",
  "checker_version": 1,
  "usage": {
    "transport": "subscription",
    "model": "claude-sonnet-5",
    "input_tokens": 4180,
    "output_tokens": 610
  },
  "items": [
    {
      "id": "1d24cbe9-posted-by",
      "check": "redistributor-filed-as-publisher",
      "field": "publisher",
      "operation": "move",
      "to_field": "posted_by",
      "current": "Eyes On Cinema",
      "proposed": "Eyes On Cinema",
      "confidence": "high",
      "evidence": {
        "reasoning": "The channel republishes archival broadcast footage it did not produce. The title dates the work to 1967, decades before the channel existed.",
        "sources": ["https://www.youtube.com/@EyesOnCinema/about"],
        "record_spans": ["title"]
      },
      "status": "proposed"
    },
    {
      "id": "1d24cbe9-posted-date",
      "check": "redistributor-filed-as-publisher",
      "field": "date_published",
      "operation": "move",
      "to_field": "posted_date",
      "current": "2026-08-11",
      "proposed": "2026-08-11",
      "confidence": "high",
      "evidence": {
        "reasoning": "This is the upload date of the copy, not the publication date of the 1967 work.",
        "sources": ["https://www.youtube.com/watch?v=8NIy61DkTWw"],
        "record_spans": ["date_published"]
      },
      "status": "proposed"
    },
    {
      "id": "1d24cbe9-date-published",
      "check": "work-date-from-title",
      "field": "date_published",
      "operation": "set",
      "current": null,
      "proposed": "1967",
      "confidence": "medium",
      "evidence": {
        "reasoning": "The title states the investigative tour took place in 1967. Year precision only; no month or day is evidenced.",
        "sources": [],
        "record_spans": ["title"]
      },
      "status": "proposed"
    }
  ]
}
```

Note the third item is `medium` and the first two are `high`. Moving a known
redistributor out of `publisher` is safe; asserting the work's date from a title is a
reading. A reviewer can take the first two and leave the third.

Note also there is no proposal to fill `publisher`. Nothing evidenced it, so nothing
is proposed - the same not-evidenced convention [ingest-format](ingest-format.md)
uses for date precision. An unproposed field is a better outcome than a guessed one.

## Fields

### Record level

| Field | Meaning |
|---|---|
| `schema` | `anomalica/housekeeping/1`. Bump on a breaking change to this shape. |
| `content_hash` | The record this describes, in full `sha256:` form. |
| `checked_at` | When the pass ran. |
| `checker_version` | **The re-check marker.** See below. |
| `usage` | Transport, model and token counts for the calls that produced this file. `transport` must be `subscription`; a sidecar recording a metered transport is a bug, not a variant. |
| `items` | The independently-decidable proposals. May be empty - an empty `items` with a current `checker_version` means "checked, nothing to propose", which is a result, not a failure. |

### Item level

| Field | Meaning |
|---|---|
| `id` | Stable within the file. The workbench addresses an approval by this. |
| `check` | Which check produced it. Lets a whole class be re-run or discounted. |
| `field` | The frontmatter key inspected. |
| `operation` | `set`, `clear`, or `move` (to `to_field`). |
| `current` | The value in the record now, or `null` if absent. |
| `proposed` | The value to write. For `move`, the value carried to `to_field`. |
| `confidence` | `high`, `medium`, `low`. Advisory to the reviewer; it does not gate anything. |
| `evidence` | Why. `reasoning` in a sentence, `sources` as URLs where research was involved, `record_spans` naming what in the record supports it. **An item with no evidence must not be emitted.** |
| `status` | `proposed` (worker) → `approved` or `rejected` (reviewer). |

## The re-check marker

A record is skipped when its sidecar's `checker_version` equals the worker's current
version. There is no separate "done" flag to drift out of sync with the checks.

Raising the worker's `checker_version` invalidates every sidecar at once, which is how
a corpus-wide re-check happens after the checks improve. A record whose sidecar is at
version 1 while the worker is at 2 is re-examined; its existing `approved` and
`rejected` items are carried into the new run so the pass does not re-propose
something already decided.

**Rejected items are kept, not deleted.** A rejection is the durable record that a
human considered this exact change and declined it. Dropping it would have the next
run propose the same thing again, and the reviewer would have to decline it forever.

## Applying an approved item

Deterministic, in the workbench's existing write path. Parse the record's frontmatter,
apply the operation, re-serialise, write.

**Then compare the body byte-for-byte with the body before the edit, and abort the
commit on any difference.** This is what makes "housekeeping never touches prose" a
property of the system rather than a promise about a model. The check is cheap and
runs on every apply, including the deterministic checks that could not have touched
the body anyway - a guarantee with exceptions is not a guarantee.

Approved items are committed **separately from the ingest commit**, so the history
shows plainly that a metadata change was made after the fact and by whom.

## What it must never do

- Write to the body. Enforced above.
- Set a field it has no evidence for. Absent beats guessed.
- Mark a record as human-reviewed. Housekeeping examines metadata; review verifies the
  body against the source. Independent states.
- Run on the metered API or OpenRouter. Subscription only, pinned at dispatch.
