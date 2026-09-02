# The diligent version is the wrong one

Internal method knowledge (a reference note).

> **Prefer what is authoritative BY CONSTRUCTION over what merely asserts.**
> A store record's filename IS its hash; the `content_hash` in its frontmatter is
> a copy that says so. A symlink directory maintained as the live set IS the live
> set; a directory tree that contains it is a coincidence. An explicit path list
> IS the change you are committing; `git add -A` is whatever the working tree
> happens to hold. The asserting version is always the one that reads as
> thorough, and it is the one that drifts.

The corollary is the title. When a check enumerates "everything of a kind", the
instinct that reads as diligent - glob wider, recurse deeper, include more, trust
the field that says what a thing is - is frequently the version that produces
confident garbage. The narrow scan is not lazy and the wide one is not careful;
what matters is only whether the input set is authoritative.

Four instances below, all found in one evening (2026-07-29), in four parts of the
pipeline, each discovered separately. Costs escalate from a wrong number to a
committed deletion.

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
# ingests/by-name/ holds one symlink per live record, none pointing into an
# archive tier. The live set by construction, not by directory convention.
by_name_dir = ingests_dir / "by-name"
return sorted(p for p in by_name_dir.glob("*.md") if p.resolve().is_file())
```

`by-name/` is maintained as the live set. A tier added under `store/` next month
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

## The asserting field: a frontmatter hash that names another record

`by-name/2007-06-20-web-project-serpo.md` is a legacy record predating the
store-and-symlink layout. Its frontmatter declares
`content_hash: a480652e...` - which is a **different record entirely**, an
unrelated interview. Hashing the two bodies confirms they differ (16,846 bytes
against 16,962).

The importer read a record's content hash from that field. Had a digest ever been
named for Project Serpo, every claim from it would have been stamped with the
other record's hash and every workbench deep link would have opened the wrong
document - with nothing, anywhere, reporting an error. It was armed and unsprung
only because neither loose file has been digested.

The fix is the rule at the top: a store record is ADDRESSED BY its hash, so take
the filename and treat the frontmatter as the copy it is. Exposure was then
bounded by measurement rather than assumption - all 181 store records were
checked, filename against frontmatter, and agree. The drift exists only in the
two loose files, which have no filename hash to be authoritative.

## The version that destroys data: `git add -A` in a shared repo

The three cases above produce a wrong number. This one produced a committed
deletion, and it is the same shape: the set of things acted on was taken from
whatever the working tree happened to hold, rather than stated explicitly.

`ingests` has several live writers - the scheduler's archive commits, workbench
reviews, the digester, the ingester. A `./ingest --force` re-ingest briefly left a
working-tree deletion of the old record (`6f5ea09a`) in the window before it could
be marked superseded. A concurrent scheduler process ran `git add -A && commit`,
staged that deletion along with its own unrelated work, and committed it inside
`d70b379`, "archive: They Showed Him a REAL UFO - Sedge Masters | ep. 95". The
record was a digested one, so the dangling body would have surfaced later as a
silent drop in a downstream sweep, in a commit whose message mentions nothing of
the kind. Recovered with `git show d70b379^:<path>` and restored in `59f61d5`.

`-A` reads as thorough - "commit everything" - and in a single-writer repo it is
harmless. In a shared one it means "commit whatever every other process has in
flight right now", which is not a set anyone chose. Stage explicit paths.

## The rule

0. **Ask which of the two things is the fact and which is the copy.** The
   filename or the field; the manifest or the tree; the path list or `-A`. One of
   them IS the thing by construction and the other reports it. Use the first and
   treat the second as a claim that can be checked - and where both are available,
   checking them against each other is cheap (181 store records, filename against
   frontmatter, all agree - that took seconds and bounded a whole class of doubt).
1. **Derive the set from something that is maintained as the set** - a manifest,
   a symlink directory, an index, an explicit path list - not from a directory
   listing or a working tree that happens to contain it at that instant. If no
   such thing exists, that is the thing to build.
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
5. **In a shared workspace, the blast radius is other people's in-flight work.**
   A wide glob misreports; a wide `git add`, `rm` or retry commits or destroys.
   The rule is identical, the cost is not.

Related: [match the family, not its current members](match-the-family-not-its-members.md),
[measuring tells you what is, not what survives](measuring-tells-you-what-is-not-what-survives.md),
[which layer is authoritative](which-layer-is-authoritative.md).
