"""Simulated (synthetic) multicenter retrospective cohort: RTSA distalization/lateralization.
NOT real patient data. Seeded for reproducibility."""
import numpy as np, pandas as pd, sys, csv
rng = np.random.default_rng(20261022)
OUT = sys.argv[1]

# ---------- screening: 300 -> 240 ----------
N_SCREEN = 300
excl = (["Revision arthroplasty"]*17 + ["Acute proximal humerus fracture (<3 weeks)"]*13 +
        ["Tumor resection"]*3 + ["No adequate postoperative Grashey radiograph"]*16 +
        ["Infection/staged procedure"]*5 + ["Age <50 years"]*6)
assert len(excl) == 60
n = N_SCREEN - len(excl)  # 240

center = rng.choice([1, 2, 3, 4], size=n, p=[0.32, 0.28, 0.22, 0.18])
center_eff = {1: 0.0, 2: -3.0, 3: 2.0, 4: -1.5}
year = rng.integers(2016, 2023, size=n)  # surgery 2016-2022
age = np.clip(rng.normal(72, 7, n), 52, 90).round(0)
female = rng.random(n) < 0.62
sex = np.where(female, 2, 1)
bmi = np.clip(rng.normal(27.5, 4.5, n), 17, 45).round(1)
diag = rng.choice([1, 2, 3, 4], size=n, p=[0.55, 0.20, 0.17, 0.08])
implant = rng.choice([1, 2], size=n, p=[0.45, 0.55])           # 1 inlay, 2 onlay
dominant = (rng.random(n) < 0.64).astype(int)                  # 1 dominant side operated
smoker = (rng.random(n) < 0.12).astype(int)
diabetes = (rng.random(n) < 0.22).astype(int)
asa = rng.choice([1, 2, 3], size=n, p=[0.12, 0.58, 0.30])
# bone density: DXA T-score (latent, partly missing) and chart osteoporosis diagnosis (complete)
tscore_true = np.clip(rng.normal(-1.6 - 0.6*female - 0.03*(age-72), 1.0), -4.5, 1.5)
osteo_dx = ((tscore_true <= -2.5) & (rng.random(n) < 0.85)) | ((tscore_true > -2.5) & (rng.random(n) < 0.05))
osteo_dx = osteo_dx.astype(int)
preop_ases = np.clip(rng.normal(36, 14, n) - 3*(diag == 4), 3, 80).round(1)
preop_fe = np.clip(rng.normal(85, 30, n), 20, 170).round(0)    # forward elevation, degrees

# ---------- exposures (radiographic, postoperative Grashey) ----------
# onlay designs -> more distalization; lateralized glenosphere correlated with implant
dsa_true = np.clip(rng.normal(46 + 3*(implant == 2), 9.5, n), 20, 78)
lsa_true = np.clip(rng.normal(88 - 2*(implant == 2), 8.5, n), 65, 112)
ahi = np.clip(rng.normal(30 + 0.35*(dsa_true-46), 6, n), 12, 52)     # mm
aho = np.clip(rng.normal(19 - 0.25*(lsa_true-88), 5.5, n), 3, 36)    # mm
agtd = np.clip(rng.normal(45 + 0.30*(dsa_true-46), 6.5, n), 25, 68)  # mm
def rater(x, sd):  # independent measurement error
    return (x + rng.normal(0, sd, len(x))).round(1)
dsa_r1, dsa_r2 = rater(dsa_true, 2.0), rater(dsa_true, 2.4)
lsa_r1, lsa_r2 = rater(lsa_true, 2.2), rater(lsa_true, 2.6)
agtd_r1, agtd_r2 = rater(agtd, 1.5), rater(agtd, 1.8)
ahi_mm, aho_mm = ahi.round(1), aho.round(1)
dli = np.sqrt(ahi_mm**2 + aho_mm**2).round(1)
dsa_mean = ((dsa_r1 + dsa_r2)/2).round(2); lsa_mean = ((lsa_r1 + lsa_r2)/2).round(2)
agtd_mean = ((agtd_r1 + agtd_r2)/2).round(2)

# ---------- outcomes ----------
diag_eff = {1: 0.0, 2: -4.0, 3: 3.0, 4: -9.0}
lin = (79 + np.vectorize(center_eff.get)(center) + np.vectorize(diag_eff.get)(diag)
       + 0.22*(preop_ases-36) - 0.18*(age-72) - 0.25*(bmi-27.5) - 4*smoker - 3*(asa == 3)
       - 0.030*(lsa_true-89)**2 - 0.022*(dsa_true-52)**2 + 1.5*(implant == 2))
# acromial / scapular spine stress fracture (Levy type I-III), within follow-up
logit = (-3.3 + 0.075*(dsa_true-46) + 0.0025*np.maximum(dsa_true-55, 0)**2
         - 0.35*(tscore_true+1.6) + 0.45*female + 0.03*(lsa_true-88) + 0.4*(diag == 2))
p_frac = 1/(1+np.exp(-logit))
fracture = (rng.random(n) < p_frac).astype(int)
lin = lin - 9*fracture
ases_2y = np.clip(lin + rng.normal(0, 11, n), 5, 100).round(1)
fe_2y = np.clip(preop_fe + 50 + 1.2*(ases_2y-75) - 0.04*(lsa_true-88)**2 + rng.normal(0, 14, n), 40, 175).round(0)
er_2y = np.clip(25 + 0.35*(lsa_true-88) + 0.15*(ases_2y-75) + rng.normal(0, 10, n), -20, 70).round(0)
levy = np.where(fracture == 1, rng.choice([1, 2, 3], size=n, p=[0.30, 0.50, 0.20]), np.nan)
time_frac = np.where(fracture == 1, np.clip(rng.gamma(2.2, 3.0, n), 1, 22).round(1), np.nan)
reop = ((rng.random(n) < 0.04 + 0.10*fracture)).astype(int)

# follow-up: target >=24 months; loss to follow-up (MAR: older, ASA3, center 4)
p_lost = 1/(1+np.exp(-(-2.05 + 0.06*(age-72) + 0.7*(asa == 3) + 0.6*(center == 4))))
lost = rng.random(n) < p_lost
maxfu = np.minimum(84, (2025.9 - year - rng.uniform(0, 1, n))*12)
fu = np.where(lost, rng.uniform(3, 23.9, n), 24 + rng.uniform(0, 1, n)*(maxfu - 24)).round(1)
# events only observable before end of follow-up
fracture = np.where(lost & (time_frac > fu), 0, fracture)
time_frac = np.where(fracture == 1, time_frac, np.nan)
levy = np.where(fracture == 1, levy, np.nan)
ases_2y = np.where(lost, np.nan, ases_2y)
fe_2y = np.where(lost, np.nan, fe_2y); er_2y = np.where(lost, np.nan, er_2y)

# other MAR missingness
tscore = np.where(rng.random(n) < 1/(1+np.exp(-(-1.0 - 0.8*osteo_dx + 0.5*(center == 3)))), np.nan, tscore_true.round(1))
bmi = np.where(rng.random(n) < 0.04, np.nan, bmi)
preop_ases = np.where(rng.random(n) < 0.06, np.nan, preop_ases)
er_2y = np.where((~np.isnan(er_2y)) & (rng.random(n) < 0.05), np.nan, er_2y)

ases_mcid = np.where(np.isnan(ases_2y) | np.isnan(preop_ases), np.nan,
                     ((ases_2y - preop_ases) >= 20.9).astype(float))

df = pd.DataFrame({
 "patient_id": [f"S{i:03d}" for i in range(1, n+1)],
 "center": center, "surgery_year": year,
 "age": age.astype(int), "sex": sex, "bmi": bmi, "diagnosis": diag, "implant_design": implant,
 "dominant_side": dominant, "smoking": smoker, "diabetes": diabetes, "asa_class": asa,
 "osteoporosis_dx": osteo_dx, "dxa_tscore": tscore, "preop_ases": preop_ases, "preop_fe": preop_fe.astype(int),
 "dsa_r1": dsa_r1, "dsa_r2": dsa_r2, "lsa_r1": lsa_r1, "lsa_r2": lsa_r2,
 "agtd_r1": agtd_r1, "agtd_r2": agtd_r2, "ahi_mm": ahi_mm, "aho_mm": aho_mm,
 "dsa": dsa_mean, "lsa": lsa_mean, "agtd": agtd_mean, "dli": dli,
 "ases_2y": ases_2y, "ases_mcid": ases_mcid, "fe_2y": fe_2y, "er_2y": er_2y,
 "stress_fracture": fracture, "levy_type": levy, "time_to_fracture_mo": time_frac,
 "reoperation": reop, "followup_mo": fu, "lost_to_followup": lost.astype(int),
})
df.to_csv(OUT + "/dataset.csv", index=False, na_rep="")
pd.Series(excl).value_counts().to_csv(OUT + "/_exclusions.tmp")
print(df.shape)
