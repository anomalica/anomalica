# A partial copy answers 200

**A truncated artefact does not arrive as an error. It arrives as a success with
fewer bytes in it**, and every check that asks "did the fetch work?" says yes.
The status is 200, the Content-Type is right, and a partial PDF or media file
usually opens far enough to look real - so it is ingested as a complete record of
a document whose second half does not exist.

Nothing downstream can recover this. The extractor sees a shorter document and
extracts it faithfully; the record looks finished; the missing half is
indistinguishable from a paper that was simply that long.

## The observed case

The Wayback Machine caps some captures. Carlotto 2005 (STS-80) is a 2,617,753-byte
PDF; the September 2023 capture stores **exactly 1,048,576 bytes** - one mebibyte,
to the byte - and serves it as `200 application/pdf`. `pdftotext` returns text.
The file has no `%%EOF` and a broken xref, but only if you look.

The evidence is in the response already:

```
Content-Length: 1048576
x-archive-orig-x-crawler-content-length: 2617753
```

The capture reports the length of the original it was made from. When the stored
body is materially shorter, the capture is a prefix. Other snapshots of the same
URL were intact (Jan 2021, 2,617,753 bytes), so the fix was to take a different
capture, not to give up on the source.

Detected and refused in the ingester's wayback fetcher (`_truncated_capture`),
with tests fixed on these real numbers. The CDX listing shows stored sizes per
snapshot, which is the quickest way to pick a good one by hand:

```
/cdx/search/cdx?url=<url>&output=json&fl=timestamp,statuscode,length&collapse=digest
```

## The general shape

Ask what the SOURCE claims the size is, and compare it to what arrived. Anywhere
a transfer can be capped, resumed, or interrupted, "it downloaded" is not the same
question as "all of it downloaded":

- Wayback captures, per the above.
- A range request or a resumed download that silently returns a partial body.
- A proxy or CDN with a response-size limit between us and the origin.
- A container or disk that filled part-way through a write.

Where the source states a length, check it. Where it does not, an integrity check
of the artefact itself (`%%EOF` for PDF, a container probe for media) is the
fallback - weaker, because it only catches damage the format happens to make
visible.

Related in shape: [absence-is-not-a-verdict](absence-is-not-a-verdict.md) - both
are cases where the failure presents as an ordinary, healthy-looking result, and
the only thing that separates them is a comparison nobody thought to make.
