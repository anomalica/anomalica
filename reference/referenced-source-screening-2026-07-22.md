# Credible-source screening - round one (2026-07-22)

Round one of the credible-source intake capability. Input: the assimilator's citation-ranked referenced-but-not-held list (`assimilator reports/referenced-not-held-sources-2026-07-22.md`, commit `fe1f043`), top 40 of 145. Rank is raw distinct-claim citation count (demonstrated relevance, not credibility).

**Screening bar** (founding principles): a source PASSES intake if it is a real, attributable, acquirable source worth holding as a reference - not whether its claims are true (algorithmic evidence scoring, not editorial taste, decides confidence, so a contested-but-real primary source is HELD and scored low, not excluded). Screened jurisdiction-neutrally: a US hearing and a Canadian or contactee source clear the same *is-it-a-real-source* bar. FAIL/UNSURE is reserved for non-sources (fiction cited culturally), procedural artefacts, duplicates, or cases where credibility or copyright can't be judged from the row.

**Copyright lens** (source-types-and-copyright tiers): US-government works -> `public_domain`, free to serve; web/YouTube/podcasts -> `publicly_accessible`; commercial books, documentaries, paywalled papers -> `restricted` (gated), and usually a purchase or access question -> Mark.

## Summary

- **25 PASS -> acquire** (I decide): public-domain government records + publicly-accessible sources. -> scheduler intake stubs.
- **5 FOR MARK**: credible but `restricted` - a purchase and/or gating decision that is Mark's.
- **2 HELD** (off-list, extraction gap, not acquisition): #3, #39. -> flagged to the assimilator.
- **8 UNSURE / FAIL** (off-list, reason recorded).

## A. Held already - extraction gap, NOT acquisition (verified against the ingests)

| # | Source | Finding |
|--:|---|---|
| 3 | Elizondo AATIP resignation letter(s) | Held verbatim inside FOIA `18-F-0324` (the letter text is reproduced; Tabs B and C). The graph node is a duplicate of held content - fix is extraction/node-linking, not intake. |
| 39 | Grusch 2023 congressional testimony | Held inside the 2023-07-26 "UAP implications on national security" hearing record - Grusch was a witness (102 "Mr. GRUSCH" testimony turns). A standalone-doc duplicate of held content. |

## B. PASS - acquire (public_domain / publicly_accessible; scheduler stubs)

| # | Source | Tier | Note |
|--:|---|---|---|
| 1 | Pentagon/Navy UAP videos (FLIR1, Gimbal, Go Fast) | public_domain | Official DoD release 2020-04-27, US-gov work. Highest citation load (85). |
| 2 | Wilson-Davis Memo | publicly_accessible | Leaked Wilson/Davis notes, circulate freely. AUTHENTICITY CONTESTED (both named men deny) - hold and score low, tag contested; copyright of leaked notes is gray, default the record to restricted until reviewed. |
| 4 | Condon Report (1968) | public_domain | Landmark Univ. Colorado / USAF study. |
| 5 | ODNI Preliminary Assessment: UAP (Jun 2021) | public_domain | Official ODNI release. |
| 6 | NDAA FY2023 | public_domain | Public law. |
| 8 | Billy Meier contact reports | publicly_accessible | Contactee corpus, circulates freely. CONTESTED tier (not official) - held and scored low. FIGU asserts copyright on formal publications; the freely-circulating reports are acquirable, flag if a formal edition is needed. |
| 10 | Harry Reid -> Lynn AATIP SAP memo (2009) | public_domain | Government correspondence, released. |
| 11 | Grusch ICIG whistleblower complaint (2022) | public_domain | Acquire the publicly released version; portions may be withheld/redacted at source. |
| 12 | Book of Enoch | public_domain | Ancient text, public domain. Cited in the ancient-astronaut discourse; the text is a legitimate historical source, contested only in application. |
| 13 | Estimate of the Situation (1948) | public_domain | Historical USAF. |
| 15 | DoD Form 1910 | public_domain | Government form. |
| 17 | Walter Haut Roswell Affidavit (2002) | publicly_accessible | Real dated published document; content contested (deathbed Roswell affidavit) - hold and score, tag contested. |
| 19 | Executive Order 12333 | public_domain | Public EO. |
| 20 | The Roswell Report: Case Closed (1997) | public_domain | USAF report. |
| 24 | To the Stars Academy YouTube video ft. Elizondo (2017) | publicly_accessible | YouTube; TTSA-promotional, tag as such. |
| 25 | NDAA FY2022 | public_domain | Public law. |
| 26 | Wilbert Smith Canada Memo (1950) | public_domain | Canadian government, historical - jurisdiction-neutral, same bar as US gov. |
| 27 | Nathan Twining Flying Disc Letter (1947) | public_domain | Foundational USAF document. |
| 29 | AATIP DoD Threat Scenario Slides | public_domain | Government document; verify a public copy exists at intake (FOIA-released?). |
| 31 | The Durant Report (1953, Robertson Panel) | public_domain | Government. |
| 32 | NAS Assessment of the Condon Report | public_domain | National Academy of Sciences / government. |
| 33 | GAO Roswell Report (1995) | public_domain | Public GAO report. |
| 34 | 2022 Annual Report on UAP (ODNI) | public_domain | Official ODNI. |
| 35 | USAF/AFRL Teleportation Study (2004) | public_domain | DIA-commissioned (Eric Davis), released. |
| 38 | Elizondo/Tipton AATIP Transfer Email | public_domain | Government email; verify a public copy at intake (likely FOIA-released). |

## C. FOR MARK - credible, but acquisition and/or gating is Mark's call (restricted)

| # | Source | Tier | Why Mark |
|--:|---|---|---|
| 30 | Skinwalkers at the Pentagon (Lacatski/Kelleher/Knapp) | restricted | Commercial book. HIGH credibility - Lacatski ran AAWSAP, this is a primary insider account. Worth acquiring; needs a purchase + gating decision. |
| 9 | Unidentified: Inside America's UFO Investigation (History Channel, 2019) | restricted | Commercial documentary carrying primary testimony (Elizondo et al.). Purchase/licence + gating. |
| 7 | Talmud of Jmmanuel (Meier corpus) | restricted | Published contactee book (copyrighted). CONTESTED tier. Purchase + gating. |
| 21 | Angst in the Shadows (Erik Nanstiel) | restricted | Independent book; credibility of author to assess. Purchase + gating. |
| 40 | A Blood Covenant (Erik Nanstiel) | restricted | Same author/basis as #21. |

## D. Unsure / fail - off-list, reason recorded

| # | Source | Verdict | Reason |
|--:|---|---|---|
| 22 | Close Encounters of the Third Kind (1977 film) | FAIL | Fiction, cited as a cultural reference, not a source of factual claims. Not acquisition-worthy as a source. |
| 36 | Star Trek (TV show) | FAIL | Fiction / cultural reference, not a factual source. |
| 37 | Unidentified (TV show) | UNSURE | Ambiguous - possibly a duplicate of #9 (the History Channel documentary) under a shortened name, or a different show. Disambiguate at the graph before any intake. |
| 23 | Greenewald FOIA Request 18-F-0324 (2017) | FAIL | The procedural REQUEST, not its substance - the response (18-F-0324) is already held. A request letter carries no claim content worth acquiring. |
| 14 | Predator Drone Nuclear Facility UAP Video | UNSURE | Provenance and copyright both unclear from the row; a "predator drone" clip needs its actual source and rights determined before intake. |
| 16 | Billy Meier photograph analysis report | UNSURE | Contested tier; authorship and copyright unclear, value marginal. Needs a locator before it can be judged. |
| 18 | Art's Parts Letters | UNSURE | Roswell-metal provenance correspondence; contested, private-letter copyright unclear. Low priority; needs a source. |
| 28 | Skinwalker Ranch Sherman Family Reports | UNSURE | Source form unclear (published account vs interviews vs secondary retelling); contested-anecdotal; copyright undetermined. Clarify what the artefact is. |

## Notes for the next round

- **Identifiers are a digest-time data gap.** Only 19/178 document nodes carry any metadata and almost none a DOI/ISBN/URL, so most PASS rows have no locator and the intake step must do a lookup. Worth closing on the digester/extraction side so round two arrives with locators.
- **No provenance-chain signal yet** (all origins null): document nodes are the only referenced-source signal today. When chains land, anonymous/relayed origins give a second axis to screen.
- Held-checks (#3, #39) suggest a graph pass to detect held-within-a-larger-record duplicates before ranking, so extraction gaps don't surface as acquisition candidates.
