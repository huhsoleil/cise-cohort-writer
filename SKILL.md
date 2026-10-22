---
name: cise-cohort-writer
description: Writes a cohort-study manuscript for Clinics in Shoulder and Elbow (CiSE) from the author's own dataset and codebook, following STROBE (cohort) and the CiSE cohort template. Use when an author with shoulder/elbow cohort data asks to analyze it and draft, check, or revise an original article for CiSE.
---

# CiSE cohort manuscript writer

Turns an author's cohort dataset (+ codebook) into a complete CiSE original article that satisfies every applicable STROBE cohort item, with reproducible analysis code, tables, figures, and a completed STROBE checklist.

Scope: **cohort studies only** (prospective or retrospective, single-center, multicenter, registry or database). For case-control or cross-sectional designs, say so and stop; for RCTs use CONSORT, for systematic reviews PRISMA.

## Bundled files (read when present)

| File | Use |
|---|---|
| `references/strobe_cohort_checklist.md` | STROBE cohort checklist (22 items, sub-items a-e) |
| `references/cise_cohort_template.md` | CiSE section-by-section template the manuscript must follow |
| `references/cise_journal_profile.md` | CiSE 2026 design mix, the STROBE items CiSE cohort papers most often miss, formal requirements |
| `examples/dataset.csv`, `examples/code_book.csv` | **Simulated** multicenter RTSA cohort (240 patients, 38 variables) |
| `scripts/analysis_example.py` | Worked analysis: ICC, restricted cubic splines, multivariable models, multiple imputation, sensitivity analyses, flow diagram |
| `examples/output/` | Tables, figures, `results.json` produced by the script |
| `examples/example_manuscript.md` | Finished example manuscript in the CiSE template, annotated with STROBE item numbers |
| `scripts/simulate_example_data.py`, `scripts/build_example_codebook.py` | Regenerate the simulated dataset and codebook (seed 20261022) |

If the bundled files are unavailable, the essential content is summarized in this file and the workflow still applies.

## Non-negotiable rules

1. **Every number in the manuscript must come from code run on the author's data in this session** and be traceable to a saved output (`results.json`, table CSV). Never estimate, round-trip from memory, or "illustrate" with invented values.
2. **Never fabricate references.** Find each reference in PubMed (or the publisher's site), confirm authors, title, journal, year, volume, pages, then format in CiSE style. If a citation cannot be verified, leave `[citation needed]`.
3. **Cite recent literature.** Prefer references published within the last 5 years (counted from the current year). Exclude references older than 5 years unless they are essential to the conclusions or are the original source of a method, definition, classification, measurement instrument, or reporting guideline used in the study (e.g., STROBE, the original definition of an angle or scale). When a recent paper covers the same point, cite the recent one instead of the older one.
4. **Do not pad the reference list.** CiSE allows up to 30 references for an Original Article; this is a maximum, not a target. Cite only references that directly support a statement. If few relevant recent papers exist, a shorter list (for example, 10-20) is acceptable.
5. **Never invent administrative facts** (IRB numbers, dates, funding, author names, ORCID, consent procedures). Use bracketed placeholders and list them for the author.
6. **Raw data stay untouched.** Work on a copy; record every recode in the analysis script.
7. **Patient data must be de-identified** before analysis. If direct identifiers (names, registration numbers, exact birth dates, addresses) appear, stop and ask the author to remove them.
8. **The bundled example is simulated.** It may be used only to demonstrate the workflow; never present its results as real findings or cite them.
9. Use association language for observational results ("was associated with"), not causal claims, unless a causal design is justified explicitly.
10. Write in formal academic English with sentence case headings and titles, following the template.

## Workflow

### Step 1. Intake (ask only for what is missing)
Collect: dataset file; codebook (create one in Step 3 if absent); study question; centers, setting and dates; eligibility criteria and screening counts (needed for the flow diagram); IRB approval/waiver; funding; author list. If the author cannot provide screening counts, state that item 13a will be incomplete.

### Step 2. Confirm the design is a cohort
Cohort = participants selected by **exposure status or from a defined population, then followed for outcomes**. If participants were sampled by outcome (cases vs controls), it is case-control; if exposure and outcome were measured at one time point, cross-sectional; a single treated group with before-after outcomes and no comparison is a case series. Use the correct term in the title (STROBE 1a). In CiSE 2026, a paper titled "case-control" was in fact a matched cohort; avoid this error.

### Step 3. Data audit (write `data_audit.md`)
- Read the codebook; if none exists, build one (variable, label, role, type, unit, codes, missing codes, n valid, n missing, observed range/frequencies, notes).
- Detect non-standard missing codes (e.g., "n.b.", "nnb", 999, "."), blank structural cells (e.g., complication type when no complication), empty trailing rows/columns, out-of-range values, inconsistent derived variables (e.g., BMI present when height missing), duplicated IDs.
- Report how the dataset reproduces any counts the author already knows; investigate discrepancies before analysis.

### Step 4. Analysis plan mapped to STROBE (agree with the author before running)
| STROBE | Decide and write down |
|---|---|
| 7 | Exposure(s), primary and secondary outcomes, confounders (choose a priori from clinical reasoning or a DAG, not by P-value screening), effect modifiers |
| 8 | Measurement source of each variable; reliability (ICC with 95% CI) when an exposure is measured on images |
| 9 | Concrete bias controls: consecutive enrollment, blinded/independent assessors, confounder adjustment, attrition analysis |
| 10 | How study size was arrived at: a priori calculation, or post hoc power/detectable effect for the primary outcome; events-per-parameter for binary outcomes |
| 11 | Continuous exposures kept continuous; nonlinearity with restricted cubic splines (3-5 knots at Harrell percentiles); if categorized, give boundaries and rationale |
| 12a | Model for each outcome; confounding control (multivariable, propensity score with balance diagnostics, stratification, cluster/center handling) |
| 12b | Subgroups/interactions, or state that none were performed and why |
| 12c | Missing data: amount per variable; mechanism assumed; multiple imputation (m≥20, include outcome and auxiliary variables, Rubin's rules) vs complete case |
| 12d | Loss to follow-up: definition, comparison of retained vs lost, handling (imputation, censoring) |
| 12e | At least 2 sensitivity analyses (e.g., complete case vs MI; alternative exposure definition or single rater; excluding a clinically distinct subgroup; center as random effect; alternative confounder set) |

### Step 5. Run the analysis
Write one reproducible script (Python or R) with a fixed random seed; save `results.json`, Table 1 (overall and by exposure group/tertile, with a missing-n column), reliability table, main-results table (unadjusted and adjusted estimates with 95% CI), outcome-events table, sensitivity table, and figures (flow diagram is mandatory; spline plots for nonlinear exposures). Use `scripts/analysis_example.py` as the pattern. Report the software name, version, and company (city, country).

### Step 6. Write the manuscript in the CiSE template order
Follow `references/cise_cohort_template.md` heading by heading:
- **Title**: sentence case; include the country for human studies; end with ": a [single-center/multicenter] [retrospective/prospective] cohort study".
- **Author block, word counts** (abstract ≤250 words; main text ≤5,000; references ≤30; tables+figures ≤10).
- **Abstract** (Purpose with hypothesis; Methods with design, population, period, measurement, statistics, data availability; Results with key estimates and 95% CI; Conclusion answering the hypothesis). Keywords: up to 6 MeSH terms (check with MeSH on Demand), including the country tag.
- **Introduction**: Background/rationale (known, unknown, why it matters); Objectives in one paragraph with hypotheses.
- **Methods**: Ethics statement; Study design; Setting; Participants; Variables; Data sources/measurement; Bias; Study size; Statistical methods (a)-(e); cite datasets in the text.
- **Results**: Participants (13a-c, with Fig. 1 flow diagram and the comparison of retained vs lost); Descriptive data (14a-c: Table 1, missing n per variable, median/IQR and total follow-up); Outcome data (15); Main results (16a unadjusted and adjusted with 95% CI and the confounders named; 16b category boundaries; 16c absolute risks or risk differences for binary outcomes); Other analyses (17). Mention "Dataset 1" in the Results.
- **Discussion**: Key results; Interpretation (cautious, consider multiplicity); Comparison with previous studies (concordance/discordance only); Limitations (state the **direction and likely magnitude** of each bias); Generalizability.
- **Suggestions; Conclusion** (answer each hypothesis; no new results).
- **Back matter**: ORCID; Authors' contributions (CRediT); Conflict of interest; Funding (with funder role, or "None"); Data availability (Dataset 1 ...); Acknowledgments; generative-AI use statement (tool, model, version, manufacturer, role); Supplementary materials.
- **References** in CiSE style: [1] numbering by first citation; ≤6 authors listed, otherwise 3 + "et al."; NLM abbreviations; "2018;27:1226-34".
- **Reference selection**: search PubMed with a publication-date filter for the last 5 years first; keep an older reference only if it is essential to the conclusions or is the original source of a method, definition, classification, instrument, or reporting guideline. Keep the list as short as the content requires (≤30; no padding).
- Tables with self-explanatory titles, abbreviation footnotes, a)/b)/c) symbols; P as capital roman "P"; figure legends after the tables.

### Step 7. Weak-item gate (CiSE-specific)
Before delivering, confirm each of these is explicitly present, because most 2026 CiSE cohort papers missed them:
- [ ] 1a design term in title **and** abstract
- [ ] 9 a Methods paragraph headed "Bias" naming concrete measures
- [ ] 10 a Methods paragraph headed "Study size" with a calculation
- [ ] 12c missing-data method and 14b missing n per variable
- [ ] 12d/13b loss to follow-up with reasons and retained-vs-lost comparison
- [ ] 12e and 17 at least two sensitivity analyses, described and reported
- [ ] 13c flow diagram (Fig. 1)
- [ ] 14c follow-up summarized (median, IQR, total person-time)
- [ ] 16a estimates with 95% CI, unadjusted and adjusted, confounders named
- [ ] 16c absolute risk or risk difference for binary outcomes
- [ ] 21 a Generalizability paragraph
- [ ] 22 funding and funder role

### Step 8. STROBE self-check and delivery
Produce a reference audit table (number, first author, year, age in years, verified in PubMed yes/no, and for any reference older than 5 years the reason it is kept: essential to conclusions or original source of method/definition/instrument/guideline). Remove older references without such a reason before delivery. Report the total number of references and the proportion published within the last 5 years.

Produce `strobe_checklist_completed` (item, recommendation, "reported on page/section", or "not applicable" with reason). Deliver: manuscript (DOCX if requested, otherwise Markdown or the user's preferred document format), tables, figures, analysis script, `results.json`, dataset + codebook (as Dataset 1 / Supplement), completed STROBE checklist, and a short list of placeholders and unresolved questions for the author.

## Worked example (simulated data)

Question: Are postoperative distalization (DSA) and lateralization (LSA) after primary reverse total shoulder arthroplasty associated with 2-year ASES score and acromial/scapular spine stress fracture?

- Data: `examples/dataset.csv` — 300 screened, 60 excluded (reasons in the codebook), 240 included at 4 centers (2016-2022), 207 completed 24-month follow-up, 33 lost. Exposures measured by 2 raters (`dsa_r1/r2`, `lsa_r1/r2`, `agtd_r1/r2`); mean used (`dsa`, `lsa`, `agtd`); `dli` derived. Outcomes `ases_2y`, `stress_fracture` (+ `levy_type`, `time_to_fracture_mo`), `fe_2y`, `er_2y`, `ases_mcid`, `reoperation`. Confounders `center`, `age`, `sex`, `bmi`, `diagnosis`, `implant_design`, `preop_ases`, `osteoporosis_dx`, `dxa_tscore` and others. Missing (MAR): `ases_2y` 33, `dxa_tscore` 73, `preop_ases` 20, `bmi` 8.
- Run: `python scripts/analysis_example.py examples/dataset.csv examples/output` (about 2 min; numpy, pandas, scipy, statsmodels, matplotlib).
- Key outputs: ICC(2,1) 0.953 (DSA), 0.937 (LSA); inverted-U spline associations with 2-year ASES (P for nonlinearity 0.005 and 0.002; maxima near 52° and 87°); stress fracture 16/240, adjusted OR per 10° DSA 4.07 (95% CI 2.07-8.00), standardized risk 1.0% at 40° vs 14.7% at 60°; 6 sensitivity analyses consistent.
- `examples/example_manuscript.md` shows every template section filled from these outputs, tagged with STROBE item numbers, including a Limitations paragraph that states the direction of each bias and the low events-per-parameter (4) for the fracture model.

Use the example to show authors what a complete CiSE cohort manuscript looks like, or to test the workflow; then apply the same steps to the author's own data.
