# GEIPAN as prior art for evidence scoring

A reading brief, not a data source. Attach to the evidence-scoring work;
read before designing a strangeness or confidence measure.

## What exists

France's GEIPAN publishes its database **data dictionary** - the schema
documentation, distinct from the case export:

- `Description_des_tables_et_champs_de_donnees_de_la_base_du_geipan_2019-01-07.xlsx`
- `2019-02-26_Historique_des_bases_au_GEIPAN.pdf`

Both under `https://www.cnes-geipan.fr/sites/default/files/` (fetchable,
verified 2026-07-25).

The schema reportedly carries `cas_etrangete` (strangeness),
`cas_etrangete_calc` (**computed** strangeness), a consistency measure,
`cas_temoins_nb` (witness count) and `cas_nb_PAN`. The current public case
export does **not** expose these - its columns are ID, Titre, Details,
Annee, Identification, Classification, departement, date, document, lat,
lng, Phenomene, Region, Temoignage associe, Type de cas. So the scoring
fields live in the schema documentation, not in the published data.

The **2021 legacy CSV export** carries the scoring fields the current XLSX
export drops, and is the only public artefact that does: cases and
testimonies, semicolon-delimited, **LATIN-1 not UTF-8**, 35 columns, frozen
2021-02-19 - 2,768 cases 1937-2018 (A 595 / B 1,108 / C 942 / D 87 / D1 36)
and 4,590 testimonies, under the same `sites/default/files/` path.

Its columns answer part of this brief before it is read. GEIPAN modelled at
least **four** axes where this project has been discussing three:

| Field | Axis |
|---|---|
| `cas_etrangete` | Strangeness of the phenomenon |
| `cas_fiabilite` | Reliability - how much the account is trusted |
| `cas_consistance` | Internal consistency |
| `cas_qte_information` | Quantity of information available |

`cas_qte_information` sitting **alongside** `cas_fiabilite` is the
orthogonality question answered in their own schema: "how much do we know"
and "how much do we trust it" are separate fields, not one blended score.
That is the C-versus-D distinction operationalised, and it is the strongest
single argument for reading this before designing ours.

## Read it; do not ingest it

**CNES prohibits reproduction, adaptation, translation, and derivative
works.** This is prior art to be read, not a source to hold. It does not go
through ingestion, it is not a record, and nothing derived from it is
redistributed. The distinction was theoretical while the artefact was
hypothetical; it is concrete now that the file is unauthenticated and
trivially fetchable.

What may be taken from it is what one takes from any schema: an
understanding of the choices someone else made. Their *values* are theirs.

## Why this is not the thing we rejected

Calibrating our scorer against GEIPAN's **conclusions** was considered and
rejected: their verdicts carry their institutional priors, and an official
adjudication is something this project holds and compares against the
declassified record, never something it treats as ground truth (see
[record-format.md](../architecture/record-format.md#audience-and-disclosure)).

Reading how they **operationalised** a measurement is a different act.
Studying an existing schema before designing one does not inherit its
data. The failure it guards against is designing strangeness scoring in
ignorance of the one serious prior attempt and rediscovering its problems
at our own expense.

## What to ask the dictionary

1. **Is strangeness computed from structured observables** (duration,
   witness count, distance, phenomenon type) **or from an assessor's
   judgement?** That is precisely the choice we face, and the field name
   `cas_etrangete_calc` suggests they made it explicitly.

2. **How is strangeness kept orthogonal to evidence quality?** Their
   classification separates C (insufficient data) from D (unexplained
   despite adequate data) - the same distinction our model must not
   collapse. A strange case with poor evidence and an ordinary case with
   excellent evidence are different things, and one number cannot carry
   both.

3. **Is strangeness computed before or after identification?** This is the
   circularity test. If a case's strangeness is recomputed once it
   resolves to a lantern, then "high strangeness correlates with
   unexplained" is a tautology and the field cannot predict anything. A
   measure worth copying is one fixed at report time from what the witness
   described, independent of the outcome.

4. **Does strangeness gate investigation?** If strange cases are the ones
   investigated, the investigated set is selected on the variable being
   measured, and any relationship between strangeness and outcome is
   partly an artefact of that selection - the same defect that makes a
   100%-resolution corpus useless for calibration.

5. **Does the scheme separate strangeness of the PHENOMENON from richness
   of the REPORT?** An articulate witness describing a lantern in vivid
   detail and a hesitant witness describing something genuinely anomalous
   produce dossiers of similar size. Adjacent to the C/D distinction but
   not the same: C/D is about data sufficiency, this is about narrative
   quality passing itself off as either strangeness or evidence.

## The failure class these share

**A signal that measures how well something is told is not a signal of
whether it happened.** Every caution below is an instance, and each one
looks like common sense in the moment of adoption.

- **Witness count is not a reliability proxy.** A large count means the
  stimulus was widely visible, which correlates with mundane,
  high-altitude, long-duration causes - satellite re-entries, planets,
  balloons. More witnesses biases a scorer toward the ordinary.
- **Vividness, detail, and specificity measure narrative skill.** This
  bites hardest on our own corpus, which is roughly two-thirds podcast and
  interview material. A practised storyteller produces richer, more
  specific, more internally consistent claims than a hesitant first-hand
  witness, and the trap is worse than GEIPAN's because these are precisely
  the properties an extraction model measures well.
- **Internal coherence improves with retelling.** A story told across
  fifty shows becomes smoother, not truer. Rehearsal removes the
  hesitations, contradictions, and gaps that a genuine recollection
  carries, so coherence scores rise as the account moves further from the
  event.
- **Detail accretion inverts the reliability ordering.** Repeated
  testimony tends to *gain* specifics over time. A scorer rewarding
  specificity therefore ranks the latest telling highest - the version
  most distant from the event and most contaminated by every retelling in
  between. Where several records carry one person's account, recency is a
  penalty, not a bonus.

The repetition cautions have a second edge: many records of one person
repeating one account are not corroboration. The claim-provenance chain
([0044](../decisions/0044-claim-provenance-chain-is-required.md)) exists to
stop that being counted as independent attestation, and any narrative
quality signal must be read against it rather than alongside it.

## Related correction

**COMETA is not a government report.** The only CNES-connected
participant, Velasco, contributed externally - listed among those who
"accepte de temoigner ou de contribuer", not as a member. Both the English
and French Wikipedia entries have this wrong. Relevant wherever French
official activity is described, and it strengthens rather than weakens the
finding that France's official programme is GEIPAN alone.
