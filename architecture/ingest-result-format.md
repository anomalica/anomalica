# Ingest result format

The post-commit wire from the ingester to the scheduler. Schema
`anomalica/ingest-result/1`.

## Transport

The scheduler supplies one canonical lowercase UUID as `--run-uuid` and an
absolute `--result-path`. Its result location is:

```
${ANOMALICA_DATA_DIR:-~/.local/share/anomalica}/ingest-results/<run_uuid>.json
```

This file is outside the ingests Git repository: putting `commit_sha` in a file
inside the commit it names would be circular.

The scheduler creates the root directory, rejects a path outside it and requires
that the result path does not already exist. The result is one compact UTF-8
JSON object with keys sorted lexically and no
insignificant whitespace. The result file contains those bytes plus one LF. The
ingester writes a temporary sibling, flushes and fsyncs it, then atomically
publishes it without replacing an existing path. After publishing the file it writes exactly one
stdout line:

```
ANOMALICA_INGEST_RESULT {"commit_sha":"...",...}
```

The bytes after the single space are exactly the result-file JSON bytes. The
scheduler requires the file and stdout objects to match and rejects a missing,
malformed or duplicate prefix line.

## Fields

| Field | Meaning |
|---|---|
| `schema` | Required. `anomalica/ingest-result/1`. |
| `run_uuid` | Required. Canonical lowercase UUID supplied by the scheduler. |
| `outcome` | Required. `committed` or `no-op`. |
| `record_path` | Required. Normalised POSIX path relative to the ingests repository. It is never absolute and contains no empty, `.` or `..` segment. It resolves to the live produced record. |
| `content_hash` | Required. `sha256:` followed by 64 lowercase hexadecimal characters. It equals the produced record's parsed `content_hash`. |
| `commit_sha` | Required. Full lowercase Git object id, 40 or 64 hexadecimal characters. Its tree contains `record_path` with the stated `content_hash`. |
| `completed_at` | Required. UTC ISO 8601 timestamp ending in `Z`, recorded after commit verification. |

No additional field is permitted. Scheduler correlation uses `run_uuid`; it
does not need or accept an inferred output identity from the intake item.

## Scheduler acceptance

The ingester's pre-emission verification does not replace consumer validation.
Before staging housekeeping, the scheduler rejects non-canonical JSON and
independently reads
`record_path` from the tree named by `commit_sha`, requires that blob to be a
live ingest record, parses its `content_hash`, and requires exact equality with
the result. A missing Git object or path, retired/non-record path, parse failure
or hash mismatch rejects the result. Git arguments are passed without shell
interpolation. No rejected or unverifiable result makes housekeeping due.

## Outcomes

`committed` means the ingester created a successful new commit and then verified
that commit's tree and record frontmatter before emission.

`no-op` means no new commit was required. The ingester's own duplicate/source
resolution identified exactly one existing live record, and `commit_sha` names
the current verified repository state containing it. This covers a duplicate
found before fresh handler output exists. An ambiguous match, missing live
record, retired-only match, hash mismatch or uncommitted file is a failure, not
a no-op.

The ingester emits no result file or prefix line on failure, partial work or
before commit verification. If it crashes after commit but before a complete
result exchange, the scheduler starts a retry with a new run UUID and absent
result path. The ingester resolves the committed record as a no-op and emits the
new result; the scheduler still does not infer a path from the intake hash.
