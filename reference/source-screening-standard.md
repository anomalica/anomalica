# Source screening standard

The bar a referenced-but-not-held source must clear to be acquired. Applies
to every screening round; the dated round reports record decisions against
it, not the standard itself.

## The bar

A source PASSES if it is a **real, attributable, acquirable source worth
holding as a reference** - not if its claims are true. Algorithmic evidence
scoring decides confidence, not editorial taste, so a contested-but-real
primary source is held and scored low rather than excluded.

Screened jurisdiction-neutrally: a US hearing, a Canadian memo, and a
contactee corpus clear the same *is-it-a-real-source* bar.

FAIL or UNSURE is reserved for non-sources (fiction cited culturally),
procedural artefacts, duplicates of held content, and cases where
credibility or copyright cannot be judged from the available information.

## Affiliation is not endorsement

Where a source's value depends on **institutional weight**, ask what the
institution actually did: endorse the work, or merely employ its authors.

This is a distinct failure mode from the ones above. There the publisher's
credibility is in question; here the institution is credible and the item
still fails, because it was never the institution's output.

**An institution's disowning of a work is itself a citable fact, and it
outranks the institutional affiliation of the authors.**

Two worked examples, both routinely miscited as official:

- **Ukraine 2022 "government UAP report"** (Zhilyaev, Petukhov, Reshetnyk,
  *Unidentified Aerial Phenomena I/II*). An arXiv **preprint**. The Main
  Astronomical Observatory's own Scientific Council publicly stated it was
  premature and did not meet the requirements for publication. A naive
  screen matching "national observatory + UAP + 2022" passes it; it should
  fail.
- **COMETA**. Not a government report. The only CNES-connected
  participant, Velasco, contributed externally - listed among those who
  "accepte de temoigner ou de contribuer", not as a member. Both the
  English and French Wikipedia entries have this wrong.

Note what the rule does *not* say. Neither item is excluded for being
wrong, and a repudiated preprint may still be worth holding as what it
actually is - a preprint by named researchers. What fails is the claim to
institutional authority, and with it any weighting that rested on it.

## Three failures, not one

A cited source can fail in three distinct ways, and they need different
evidence:

| | Failure | Settled by |
|---|---|---|
| a | A real document whose **significance** is inflated | Reading it |
| b | A real document whose **institutional backing** is overstated | The institution's own position (above) |
| c | A cited document with **no artefact behind it** | A negative search against a demonstrated instrument |

Only (c) can be established by finding nothing, and only under the
condition below.

## A negative result is evidence only when the instrument is proven

"We searched and found nothing" is worthless on its own: it is
indistinguishable from a search that could never have succeeded - wrong
index, title-only matching, an archive that excludes the class of document
entirely.

**Demonstrate the instrument's reach before relying on its silence.** The
cheap, reusable test: find a hit that matches on *interior text* - a
document whose title and reference contain neither search term. That
proves the index reads full text rather than metadata, and only then does
a zero-result query mean anything.

Worked example (2026-07-25). NATO's archive index was shown to read PDF
full text by exactly that test. Against it: `"unidentified aerial"` = 0
results, `"unidentified flying"` = 1, `MAINBRACE` = 70 of which none are
UFO-related (Swedish fishing-equipment damage claims, lessons-learned
reports). So the widely-cited **1954 Exercise Mainbrace UFO report** and
the **Robert Dean "Assessment"** have no document behind them in NATO's own
full-text-indexed archive.

**State the finding at the strength the evidence supports.** The
established claim is *absence from a named, tested archive* - not
non-existence, and not fabrication. Absence is consistent with fabrication,
but equally with misattribution to NATO, with destruction, or with the
document sitting in another holding. "No document behind this citation in
NATO's archive" is defensible, reproducible, and already fatal to its use
as a NATO document; "fabricated" claims more than the search can carry.
Working posture - treat as unsupported unless a reference code is produced -
is right; the wording of the published finding is what must stay narrow.

A documented absence is a genuine result, not a failed search. An
evidence-graded platform stating "this frequently-cited document does not
appear in the archive it is attributed to, and here is the search that
establishes it" is doing the job the project exists for. Related: the
Platov & Sokolov account of the Soviet Setka programme (*Вестник РАН* 70:6,
2000, free full text) is a primary-participant source whose authors
explicitly repudiate the circulating "secret KGB files" material - the same
shape, where the valuable content is what is shown to be absent.

**Model gap.** A document node for a cited-but-absent source is currently
indistinguishable from one merely not yet acquired - the same
absence-conflated-with-observation failure recorded in
[absence-is-not-a-verdict](../knowledge/absence-is-not-a-verdict.md).
Expressing a searched-and-absent determination - archive, queries,
instrument test, date, and its falsifier - is carded with the
external-determination shape, and reuses that machinery rather than a
parallel one.

## Held-within-a-container check

Before treating a referenced source as an acquisition candidate, check
whether the corpus already holds it *inside* a larger record. Round one
found two: an Elizondo resignation letter reproduced verbatim inside a
FOIA release, and Grusch testimony inside the hearing record he testified
at. Both were extraction gaps surfacing as intake candidates, not missing
sources.
