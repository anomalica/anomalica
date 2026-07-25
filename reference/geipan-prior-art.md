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

One modelling caution to carry in: **witness count is not a reliability
proxy.** A large count means the stimulus was widely visible, which
correlates with mundane, high-altitude, long-duration causes - satellite
re-entries, planets, balloons. Treating more witnesses as stronger
evidence will bias a scorer toward exactly the cases most likely to be
ordinary.

## Related correction

**COMETA is not a government report.** The only CNES-connected
participant, Velasco, contributed externally - listed among those who
"accepte de temoigner ou de contribuer", not as a member. Both the English
and French Wikipedia entries have this wrong. Relevant wherever French
official activity is described, and it strengthens rather than weakens the
finding that France's official programme is GEIPAN alone.
