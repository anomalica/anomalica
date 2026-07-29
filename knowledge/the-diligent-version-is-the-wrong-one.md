# The diligent version is the wrong one

Internal method knowledge (a reference note). When a check enumerates "everything
of a kind", the instinct that reads as thorough - glob wider, recurse deeper,
include more - is frequently the version that produces confident garbage. The
narrow scan is not lazy and the wide one is not careful; what matters is whether
the input set is **authoritative**, and a directory tree is not.

## The worked example (2026-07-29): scanning for duplicate records

The assimilator needed every near-duplicate record in the ingests store, because
a work present twice counts as two independent sources and inverts the guards
that exist to catch single-source pages.

The scan globbed `store/*.md`. Non-recursive, and written that way for no
principled reason - the author did not know what else was under `store/`. It
returned two pairs, one of them the known Communion duplicate, and the result was
reported as "all 181 records in the store".

Then `store/v1/` turned up: **211 more records**, schema `anomalica/record/1`, of
which **133 share a `source_url` with a live record** - they are superseded
re-ingests from a schema migration, retained on purpose.

So the recursive glob - the version that looks more thorough, and the one a
reviewer would ask for - would have reported roughly 133 false duplicates, every
one of them a correct detection by the detector's own lights and useless to the
operator. Four sessions would have chased them. The narrow glob was right by
accident.

The fix was not to widen or narrow the glob. It was to stop deriving the set from
the filesystem at all:

```python
# ingests/records/ holds one symlink per live record, none pointing into an
# archive tier. The live set by construction, not by directory convention.
records_dir = ingests_dir / "records"
return sorted(p for p in records_dir.glob("*.md") if p.resolve().is_file())
```

`records/` is maintained as the live set. A tier added under `store/` next month
cannot break a scan that reads it, and no one has to remember the archive
directories.

## The same shape, twice more in one evening

- **The scheduler** enumerated store records with `store/*.md` and scheduled
  digestion from it. Narrow again, so the archive tier was invisible again - but a
  *superseded* record sitting in the store ROOT was enumerated as live, and would
  have been re-digested against text the pipeline had already replaced. Silently:
  the body resolves, the digest succeeds, the output looks fine. Fixed by
  excluding records that declare `superseded_by`.
- **A retained record is not a live record**, and the retention is deliberate:
  the digester's redigest resolver looks bodies up by `content_hash`, so deleting
  a superseded record turns a stale read into a silently dropped one. Two
  consumers need opposite things from the same marker - one to EXCLUDE it, one to
  REDIRECT through it - and a scan that only knows about files can do neither.

## The rule

1. **Derive the set from something that is maintained as the set** - a manifest,
   a symlink directory, an index - not from a directory listing that happens to
   contain it today. If no such thing exists, that is the thing to build.
2. **Ask what ELSE is in the tree before widening a glob.** "Recursive" is a
   claim that everything below is the same kind of thing, and it is usually
   unchecked. Here it was false by 133 records.
3. **Retained is not live.** Archives, superseded copies and versioned tiers are
   kept on purpose and must be excluded on purpose. An enumeration that cannot
   express "kept but not current" will get this wrong in whichever direction its
   glob happens to point.
4. **Say when you got the right answer for the wrong reason.** The scan was
   correct and the reasoning behind it was not; reporting only the correct result
   would have left the next person to widen the glob and be confidently wrong.

Related: [match the family, not its current members](match-the-family-not-its-members.md),
[measuring tells you what is, not what survives](measuring-tells-you-what-is-not-what-survives.md),
[which layer is authoritative](which-layer-is-authoritative.md).
