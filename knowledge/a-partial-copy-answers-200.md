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

## The composite case: bigger than expected, and still partial

A single file has a size to compare against. A **composite** artefact - one
assembled from many fetched parts - has no such number, and its partiality is
invisible precisely because the parts that survived make it look substantial.

A frozen web page (`single-file-cli`, our `single_file` snapshot) inlines every
stylesheet, font and image into one HTML file. On every Squarespace page in the
corpus it inlined nineteen stylesheets, 138 KB of CSS, into an 895 KB file - and
dropped the one stylesheet that laid the page out. The result opened as the
article's full text in Times New Roman on a blank background, masthead blown
across the viewport. Nothing errored; nothing was empty; the file was larger than
several captures that were fine.

The mechanism is worth knowing because it is invisible from the artefact.
SingleFile cannot read a **cross-origin** stylesheet out of the CSSOM - the
browser refuses `sheet.cssRules` for it - so it re-fetches the URL instead, and
that fetch is CORS-checked. Squarespace serves a version-numbered `site.css` and
301-redirects an outdated version to the current one; the page asked for
`.../1821/site.css`, Squarespace redirected to `1822`, the CORS check failed on
the redirect, and 1.27 MB of layout CSS was discarded without a word. What
survived was Squarespace's *component* CSS - forms, cart, captcha - which is why
the capture looked styled and laid out nothing. Fixed by running the capture
browser with web security off so the CSSOM is readable (ingester `5d5fd98`).

The tell, when the artefact itself cannot be sized: **compare a fresh copy
against the stored one**, not the stored one against a threshold. Re-capturing
with the fix produced 451-505 KB of CSS where the stored captures had 138-191 KB.
No fixed idea of "enough CSS" would have worked - a plain 2001 page legitimately
has almost none, and the broken Squarespace pages still had 138 KB - but the
comparison separates them by 3x with nothing to tune. The same applies to any
composite: a fresh fetch is the only honest yardstick when the format will not
tell you what it should have contained.

## The general shape

Ask what the SOURCE claims the size is, and compare it to what arrived. Anywhere
a transfer can be capped, resumed, or interrupted, "it downloaded" is not the same
question as "all of it downloaded":

- Wayback captures, per the above.
- A composite artefact whose parts are fetched separately: a frozen page, a
  bundle, an archive built by walking references. Any one part can fail while
  the whole still opens.
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
