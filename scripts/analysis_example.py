"""Worked analysis for the cise-cohort-writer example (SIMULATED data).

Usage:  python analysis_example.py <dataset.csv> <output_dir>

Produces every number cited in examples/example_manuscript.md:
  results.json, table1..table5 (.csv), fig1_flow.png, fig2_spline_ases.png, fig3_fracture_risk.png
Each block is labelled with the STROBE item it serves.
Requires: numpy, pandas, scipy, statsmodels, matplotlib.
"""
import sys, json, os
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.imputation import mice
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(2026)
np.random.seed(2026)  # MICEData uses the global NumPy RNG
d = pd.read_csv(SRC)
R = {}

# ---------------------------------------------------------------- helpers
def rcs_basis(x, knots):
    """Harrell restricted cubic spline: returns k-2 nonlinear terms (linear term added separately)."""
    k = np.asarray(knots, float); t = len(k); x = np.asarray(x, float)
    norm = (k[-1] - k[0]) ** 2
    pos = lambda u: np.maximum(u, 0) ** 3
    cols = []
    for j in range(t - 2):
        cols.append((pos(x - k[j]) - pos(x - k[t-2]) * (k[t-1] - k[j]) / (k[t-1] - k[t-2])
                     + pos(x - k[t-1]) * (k[t-2] - k[j]) / (k[t-1] - k[t-2])) / norm)
    return np.column_stack(cols)

KN = {v: np.percentile(d[v], [5, 35, 65, 95]) for v in ["dsa", "lsa"]}
def add_rcs(df, v, src=None):
    b = rcs_basis(df[src or v], KN[v])
    for j in range(b.shape[1]):
        df[f"{v}_nl{j+1}"] = b[:, j]
    if src:
        df[v] = df[src]
    return df

def icc21(a, b):
    X = np.c_[a, b]; n, k = X.shape; gm = X.mean()
    msr = k * ((X.mean(1) - gm) ** 2).sum() / (n - 1)
    msc = n * ((X.mean(0) - gm) ** 2).sum() / (k - 1)
    mse = ((X - X.mean(1, keepdims=True) - X.mean(0) + gm) ** 2).sum() / ((n - 1) * (k - 1))
    return (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)

def fmt(x, nd=1): return f"{x:.{nd}f}"
def pfmt(p): return "<0.001" if p < 0.001 else f"{p:.3f}"

COV = "age + C(sex) + bmi + C(diagnosis) + C(implant_design) + preop_ases + C(center)"
SPL = "dsa + dsa_nl1 + dsa_nl2 + lsa + lsa_nl1 + lsa_nl2"
F_ASES = f"ases_2y ~ {SPL} + {COV}"

# ---------------------------------------------------------------- STROBE 13a/13b: flow
flow = dict(screened=300, excluded=60,
            reasons={"Revision arthroplasty": 17, "No adequate postoperative Grashey radiograph": 16,
                     "Acute proximal humerus fracture (<3 weeks)": 13, "Age <50 years": 6,
                     "Infection/staged procedure": 5, "Tumor resection": 3},
            included=len(d), completed_24mo=int((d.lost_to_followup == 0).sum()),
            lost=int(d.lost_to_followup.sum()))
R["flow"] = flow

# ---------------------------------------------------------------- STROBE 14a/14b/14c: Table 1
d["dsa_tertile"] = pd.qcut(d.dsa, 3, labels=["T1", "T2", "T3"])
R["dsa_tertile_bounds"] = [round(x, 1) for x in d.dsa.quantile([0, 1/3, 2/3, 1])]
rows = []
def cont(v, lab):
    r = {"Characteristic": lab}
    for g, s in [("Overall", d)] + [(t, d[d.dsa_tertile == t]) for t in ["T1", "T2", "T3"]]:
        r[g] = f"{s[v].mean():.1f}±{s[v].std():.1f}"
    r["Missing, n"] = int(d[v].isna().sum()); rows.append(r)
def cat(v, lab, codes):
    for c, cl in codes.items():
        r = {"Characteristic": f"{lab}: {cl}"}
        for g, s in [("Overall", d)] + [(t, d[d.dsa_tertile == t]) for t in ["T1", "T2", "T3"]]:
            n = int((s[v] == c).sum()); r[g] = f"{n} ({100*n/len(s):.1f})"
        r["Missing, n"] = int(d[v].isna().sum()) if c == list(codes)[0] else ""
        rows.append(r)
cont("age", "Age (yr)"); cat("sex", "Sex", {2: "female"}); cont("bmi", "BMI (kg/m2)")
cat("diagnosis", "Diagnosis", {1: "cuff tear arthropathy", 2: "massive irreparable cuff tear",
                                3: "osteoarthritis with cuff deficiency", 4: "fracture sequelae"})
cat("implant_design", "Implant", {2: "onlay"}); cat("smoking", "Current smoker", {1: "yes"})
cat("diabetes", "Diabetes", {1: "yes"}); cat("asa_class", "ASA class", {3: "III"})
cat("osteoporosis_dx", "Osteoporosis (chart)", {1: "yes"}); cont("dxa_tscore", "DXA T-score")
cont("preop_ases", "Preoperative ASES"); cont("dsa", "DSA (°)"); cont("lsa", "LSA (°)")
cont("agtd", "AGTD (mm)"); cont("followup_mo", "Follow-up (mo)")
t1 = pd.DataFrame(rows)
t1.columns = ["Characteristic", f"Overall (n={len(d)})"] + \
    [f"DSA {t} (n={(d.dsa_tertile==t).sum()})" for t in ["T1", "T2", "T3"]] + ["Missing, n"]
t1.to_csv(f"{OUT}/table1_characteristics.csv", index=False)
R["followup"] = dict(median=round(d.followup_mo.median(), 1),
                     iqr=[round(x, 1) for x in d.followup_mo.quantile([.25, .75])],
                     total_person_years=round(d.followup_mo.sum() / 12, 1))
R["missing"] = {k: int(v) for k, v in d.isna().sum().items() if v and k not in ("levy_type", "time_to_fracture_mo")}

# ---------------------------------------------------------------- STROBE 12d: lost vs retained
lt = {}
for v in ["age", "preop_ases", "dsa", "lsa"]:
    a, b = d.loc[d.lost_to_followup == 1, v].dropna(), d.loc[d.lost_to_followup == 0, v].dropna()
    lt[v] = dict(lost=round(a.mean(), 1), retained=round(b.mean(), 1), p=pfmt(stats.ttest_ind(a, b).pvalue))
for v, c in [("asa_class", 3), ("center", 4)]:
    tab = pd.crosstab(d.lost_to_followup, d[v] == c)
    lt[f"{v}=={c}"] = dict(lost_pct=round(100 * tab.loc[1, True] / tab.loc[1].sum(), 1),
                           retained_pct=round(100 * tab.loc[0, True] / tab.loc[0].sum(), 1),
                           p=pfmt(stats.chi2_contingency(tab)[1]))
R["lost_vs_retained"] = lt

# ---------------------------------------------------------------- STROBE 8/9: inter-rater ICC
t2 = []
for v, lab in [("dsa", "DSA (°)"), ("lsa", "LSA (°)"), ("agtd", "AGTD (mm)")]:
    a, b = d[f"{v}_r1"].values, d[f"{v}_r2"].values
    est = icc21(a, b)
    bs = [icc21(a[i], b[i]) for i in (rng.integers(0, len(a), len(a)) for _ in range(2000))]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    diff = b - a
    t2.append({"Measurement": lab, "Rater 1": f"{a.mean():.1f}±{a.std(ddof=1):.1f}",
               "Rater 2": f"{b.mean():.1f}±{b.std(ddof=1):.1f}",
               "ICC(2,1) (95% CI)": f"{est:.3f} ({lo:.3f}-{hi:.3f})",
               "Mean difference (95% LoA)": f"{diff.mean():.2f} ({diff.mean()-1.96*diff.std(ddof=1):.2f} to {diff.mean()+1.96*diff.std(ddof=1):.2f})"})
pd.DataFrame(t2).to_csv(f"{OUT}/table2_icc.csv", index=False)
R["icc"] = t2

# ---------------------------------------------------------------- STROBE 12a/16a: ASES models
def prep(df, dsa_src=None, lsa_src=None):
    df = df.copy(); df = add_rcs(df, "dsa", dsa_src); df = add_rcs(df, "lsa", lsa_src); return df

GRID = {v: np.round(np.percentile(d[v], [10, 25, 50, 75, 90]), 1) for v in ["dsa", "lsa"]}
def contrasts(res_params, res_cov, v):
    """Adjusted difference in outcome at grid values vs. median (spline terms only)."""
    names = [v, f"{v}_nl1", f"{v}_nl2"]
    ref = np.r_[np.median(d[v]), rcs_basis([np.median(d[v])], KN[v])[0]]
    out = []
    for g in GRID[v]:
        xg = np.r_[g, rcs_basis([g], KN[v])[0]] - ref
        est = float(xg @ res_params[names]); se = float(np.sqrt(xg @ res_cov.loc[names, names].values @ xg))
        out.append((g, est, est - 1.96 * se, est + 1.96 * se))
    return out
def wald_nl(params, cov, v):
    names = [f"{v}_nl1", f"{v}_nl2"]; b = params[names].values; V = cov.loc[names, names].values
    w = float(b @ np.linalg.solve(V, b)); return stats.chi2.sf(w, 2)

# (i) complete case
cc = smf.ols(F_ASES, prep(d)).fit()
R["ases_cc"] = dict(n=int(cc.nobs), p_nonlin_dsa=pfmt(wald_nl(cc.params, cc.cov_params(), "dsa")),
                    p_nonlin_lsa=pfmt(wald_nl(cc.params, cc.cov_params(), "lsa")))
# unadjusted (spline only)
un = smf.ols(f"ases_2y ~ {SPL}", prep(d)).fit()

# (ii) multiple imputation (m=20), Rubin's rules
M = 20
imp_cols = ["ases_2y", "fe_2y", "er_2y", "bmi", "preop_ases", "dxa_tscore", "age", "sex", "diagnosis",
            "implant_design", "asa_class", "osteoporosis_dx", "dsa", "lsa", "stress_fracture", "smoking"]
base = d[imp_cols].copy()
for c in [2, 3, 4]: base[f"center{c}"] = (d.center == c).astype(float)
md = mice.MICEData(base, rng=np.random.default_rng(2026))
imps = []
for m in range(M):
    md.update_all(10 if m == 0 else 5)
    x = md.data.copy(); x["center"] = d.center.values; imps.append(x)
def pool(fits):
    Q = pd.concat([f.params for f in fits], axis=1); U = [f.cov_params() for f in fits]
    qbar = Q.mean(1); W = sum(U) / M; B = np.cov(Q.values); B = pd.DataFrame(B, index=Q.index, columns=Q.index)
    return qbar, W + (1 + 1/M) * B
mi_fits = [smf.ols(F_ASES, prep(x)).fit() for x in imps]
mi_b, mi_V = pool(mi_fits)
R["ases_mi"] = dict(m=M, n=len(d), p_nonlin_dsa=pfmt(wald_nl(mi_b, mi_V, "dsa")),
                    p_nonlin_lsa=pfmt(wald_nl(mi_b, mi_V, "lsa")))
t3 = []
for v, lab in [("dsa", "DSA (°)"), ("lsa", "LSA (°)")]:
    u, c_, mi_ = contrasts(un.params, un.cov_params(), v), contrasts(cc.params, cc.cov_params(), v), contrasts(mi_b, mi_V, v)
    for (g, e1, l1, h1), (_, e2, l2, h2), (_, e3, l3, h3) in zip(u, c_, mi_):
        isref = abs(g - np.median(d[v])) < 0.06
        f_ = lambda e, l, h: "0 (reference)" if isref else f"{e:.1f} ({l:.1f} to {h:.1f})"
        t3.append({"Exposure": lab, "Value (percentile)": f"{g} (P{[10,25,50,75,90][list(GRID[v]).index(g)]})",
                   "Unadjusted (CC)": f_(e1, l1, h1),
                   "Adjusted, complete case": f_(e2, l2, h2),
                   "Adjusted, multiple imputation": f_(e3, l3, h3)})
pd.DataFrame(t3).to_csv(f"{OUT}/table3_ases_spline.csv", index=False)
R["ases_mi_raw"] = {v: [[round(float(x), 3) for x in r] for r in contrasts(mi_b, mi_V, v)] for v in ["dsa", "lsa"]}
R["ases_table"] = t3
# value of exposure maximising adjusted ASES (MI)
for v in ["dsa", "lsa"]:
    xs = np.linspace(*np.percentile(d[v], [5, 95]), 200)
    b = mi_b[[v, f"{v}_nl1", f"{v}_nl2"]].values
    curve = np.array([np.r_[x, rcs_basis([x], KN[v])[0]] @ b for x in xs])
    R[f"{v}_peak"] = round(float(xs[curve.argmax()]), 1)

# ---------------------------------------------------------------- STROBE 15/16: stress fracture
ev = d.groupby("dsa_tertile", observed=True).stress_fracture.agg(["sum", "count"])
R["fracture_overall"] = dict(events=int(d.stress_fracture.sum()), n=len(d),
                             risk=round(100 * d.stress_fracture.mean(), 1),
                             median_time_mo=round(d.time_to_fracture_mo.median(), 1))
FX = "stress_fracture ~ dsa10 + C(sex) + age + osteoporosis_dx"
dd = d.assign(dsa10=d.dsa / 10)
lu = smf.logit("stress_fracture ~ dsa10", dd).fit(disp=0)
la = smf.logit(FX, dd).fit(disp=0)
orf = lambda m: (np.exp(m.params["dsa10"]), *np.exp(m.conf_int().loc["dsa10"]))
# nonlinearity check (spline) with same covariates
ls = smf.logit("stress_fracture ~ dsa + dsa_nl1 + dsa_nl2 + C(sex) + age + osteoporosis_dx", prep(d)).fit(disp=0)
p_nl_fx = wald_nl(ls.params, ls.cov_params(), "dsa")
# standardized absolute risk at DSA 40 vs 60 (bootstrap CI)
def std_risk(model_data):
    m = smf.logit(FX, model_data).fit(disp=0)
    r40 = m.predict(model_data.assign(dsa10=4.0)).mean(); r60 = m.predict(model_data.assign(dsa10=6.0)).mean()
    return r40, r60
r40, r60 = std_risk(dd)
bs = []
for _ in range(1000):
    s = dd.iloc[rng.integers(0, len(dd), len(dd))]
    try: bs.append(std_risk(s))
    except Exception: pass
bs = np.array(bs)
t4 = [{"DSA tertile": f"{t} ({R['dsa_tertile_bounds'][i]:.1f}-{R['dsa_tertile_bounds'][i+1]:.1f}°)",
       "Events/N": f"{int(ev.loc[t,'sum'])}/{int(ev.loc[t,'count'])}",
       "Risk (%)": f"{100*ev.loc[t,'sum']/ev.loc[t,'count']:.1f}"} for i, t in enumerate(["T1", "T2", "T3"])]
pd.DataFrame(t4).to_csv(f"{OUT}/table4_fracture.csv", index=False)
R["fracture"] = dict(by_tertile=t4,
    or_unadj=[round(x, 2) for x in orf(lu)], or_adj=[round(x, 2) for x in orf(la)],
    p_adj=pfmt(la.pvalues["dsa10"]), p_nonlin=pfmt(p_nl_fx),
    risk40=round(100*r40, 1), risk60=round(100*r60, 1),
    risk40_ci=[round(100*x, 1) for x in np.percentile(bs[:, 0], [2.5, 97.5])],
    risk60_ci=[round(100*x, 1) for x in np.percentile(bs[:, 1], [2.5, 97.5])],
    rd=round(100*(r60-r40), 1), rd_ci=[round(100*x, 1) for x in np.percentile(bs[:, 1]-bs[:, 0], [2.5, 97.5])],
    events_per_parameter=round(d.stress_fracture.sum() / 4, 1))

# ---------------------------------------------------------------- STROBE 12e/17: sensitivity analyses
sens = []
def ases_row(label, b, V, n):
    c = contrasts(b, V, "lsa"); dsa_c = contrasts(b, V, "dsa")
    sens.append({"Analysis": label, "n": n,
                 "LSA 10th vs median": f"{c[0][1]:.1f} ({c[0][2]:.1f} to {c[0][3]:.1f})",
                 "LSA 90th vs median": f"{c[4][1]:.1f} ({c[4][2]:.1f} to {c[4][3]:.1f})",
                 "DSA 90th vs median": f"{dsa_c[4][1]:.1f} ({dsa_c[4][2]:.1f} to {dsa_c[4][3]:.1f})",
                 "P nonlinearity LSA": pfmt(wald_nl(b, V, "lsa"))})
ases_row("Primary: multiple imputation", mi_b, mi_V, len(d))
ases_row("Complete-case analysis", cc.params, cc.cov_params(), int(cc.nobs))
r1 = smf.ols(F_ASES, prep(d, "dsa_r1", "lsa_r1")).fit()
ases_row("Exposure measured by rater 1 only", r1.params, r1.cov_params(), int(r1.nobs))
ex4 = [smf.ols(F_ASES.replace("C(diagnosis)", "C(diagnosis)"), prep(x[d.diagnosis.values != 4])).fit() for x in imps]
b4, V4 = pool(ex4); ases_row("Excluding fracture sequelae (MI)", b4, V4, int((d.diagnosis != 4).sum()))
yr = [smf.ols(F_ASES + " + surgery_year", prep(x.assign(surgery_year=d.surgery_year.values))).fit() for x in imps]
by, Vy = pool(yr); ases_row("Adding surgery year (MI)", by, Vy, len(d))
mx = smf.mixedlm(F_ASES.replace(" + C(center)", ""), prep(d).dropna(subset=["ases_2y", "bmi", "preop_ases"]),
                 groups="center").fit()
mxb = mx.fe_params; mxV = mx.cov_params().loc[mxb.index, mxb.index]
ases_row("Center as random intercept (CC)", mxb, mxV, int(mx.nobs))
# fracture sensitivity: T-score (imputed) instead of chart osteoporosis
fx_mi = [smf.logit("stress_fracture ~ dsa10 + C(sex) + age + dxa_tscore", x.assign(dsa10=x.dsa/10)).fit(disp=0) for x in imps]
fb, fV = pool(fx_mi)
se = np.sqrt(fV.loc["dsa10", "dsa10"])
R["fracture_sens_tscore_mi"] = [round(float(np.exp(fb["dsa10"] + z*se)), 2) for z in (0, -1.96, 1.96)]
pd.DataFrame(sens).to_csv(f"{OUT}/table5_sensitivity.csv", index=False)
R["sensitivity"] = sens

# ---------------------------------------------------------------- Figures
fig, ax = plt.subplots(figsize=(8, 6.5)); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
box = dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1)
ax.text(.25, .93, f"Primary RTSA at 4 centers, 2016-2022\nscreened (n={flow['screened']})", ha="center", va="center", fontsize=9, bbox=box)
ax.text(.52, .73, "Excluded (n=60)\n" + "\n".join(f"- {k} (n={v})" for k, v in flow["reasons"].items()),
        ha="left", va="center", fontsize=7.5, bbox=box)
ax.text(.25, .53, f"Included in cohort\n(n={flow['included']})", ha="center", va="center", fontsize=9, bbox=box)
ax.text(.52, .33, f"Lost to follow-up before 24 months (n={flow['lost']})\nretained in multiple-imputation analysis", ha="left", va="center", fontsize=7.5, bbox=box)
ax.text(.25, .12, f"Completed >=24-month follow-up (n={flow['completed_24mo']})\nAnalysed: n={flow['included']} (primary, MI)", ha="center", va="center", fontsize=9, bbox=box)
arrow = dict(arrowstyle="->", lw=1)
ax.annotate("", (.25, .585), (.25, .875), arrowprops=arrow)
ax.annotate("", (.25, .175), (.25, .475), arrowprops=arrow)
ax.annotate("", (.505, .73), (.25, .73), arrowprops=arrow)
ax.annotate("", (.505, .33), (.25, .33), arrowprops=arrow)
fig.savefig(f"{OUT}/fig1_flow.png", dpi=300, bbox_inches="tight"); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(10, 4))
for ax, v, lab in [(axs[0], "lsa", "Lateralization shoulder angle (°)"), (axs[1], "dsa", "Distalization shoulder angle (°)")]:
    xs = np.linspace(*np.percentile(d[v], [5, 95]), 100); ref = np.median(d[v])
    names = [v, f"{v}_nl1", f"{v}_nl2"]; b = mi_b[names].values; V = mi_V.loc[names, names].values
    r0 = np.r_[ref, rcs_basis([ref], KN[v])[0]]
    X = np.array([np.r_[x, rcs_basis([x], KN[v])[0]] - r0 for x in xs])
    est = X @ b; se = np.sqrt(np.einsum("ij,jk,ik->i", X, V, X))
    ax.plot(xs, est, color="black"); ax.fill_between(xs, est - 1.96*se, est + 1.96*se, color="grey", alpha=.3)
    ax.axhline(0, ls=":", color="black"); ax.set_xlabel(lab); ax.set_ylabel("Adjusted difference in 2-year ASES")
    ax.plot(d[v], np.full(len(d), ax.get_ylim()[0]), "|", color="black", alpha=.4)
fig.tight_layout(); fig.savefig(f"{OUT}/fig2_spline_ases.png", dpi=300); plt.close(fig)

fig, ax = plt.subplots(figsize=(5, 4))
xs = np.linspace(*np.percentile(d.dsa, [5, 95]), 100)
pr = [la.predict(dd.assign(dsa10=x/10)).mean()*100 for x in xs]
ax.plot(xs, pr, color="black"); ax.set_xlabel("Distalization shoulder angle (°)")
ax.set_ylabel("Standardized risk of stress fracture (%)")
fig.tight_layout(); fig.savefig(f"{OUT}/fig3_fracture_risk.png", dpi=300); plt.close(fig)

json.dump(R, open(f"{OUT}/results.json", "w"), indent=1, default=str)
print(json.dumps({k: R[k] for k in ["flow", "followup", "ases_cc", "ases_mi", "dsa_peak", "lsa_peak", "fracture_overall", "fracture", "fracture_sens_tscore_mi"]}, indent=1, default=str))
