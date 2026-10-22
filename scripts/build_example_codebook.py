# Builds examples/code_book.csv. Usage: python simulate_example_data.py <dir> ; python build_example_codebook.py <dir>
import pandas as pd, csv, sys
D = sys.argv[1]
d = pd.read_csv(D + "/dataset.csv")
V = [
# name, label, role, type, unit, codes, analysis_use, notes
("patient_id","Study participant identifier","Identifier","String","-","S001-S240","Linkage only",""),
("center","Participating center","Confounder (cluster)","Categorical (nominal)","-","1=Center A; 2=Center B; 3=Center C; 4=Center D","Fixed effect or random intercept; cluster-robust SE",""),
("surgery_year","Year of index RTSA","Confounder / period","Discrete","year","2016-2022","Sensitivity analysis (period effect)",""),
("age","Age at surgery","Confounder","Continuous","years","","Multivariable model; restricted to >=50 by eligibility",""),
("sex","Sex","Confounder","Categorical (nominal)","-","1=male; 2=female","Multivariable model",""),
("bmi","Body mass index","Confounder","Continuous","kg/m2","","Multivariable model; imputed in MI","Missing ~5%"),
("diagnosis","Primary indication for RTSA","Confounder","Categorical (nominal)","-","1=cuff tear arthropathy; 2=massive irreparable rotator cuff tear without arthritis; 3=primary osteoarthritis with cuff deficiency; 4=fracture sequelae","Multivariable model; sensitivity analysis excluding 4",""),
("implant_design","Humeral component design","Confounder","Categorical (nominal)","-","1=inlay; 2=onlay","Multivariable model; effect-modification check","Onlay associated with greater distalization"),
("dominant_side","Operated side is dominant","Confounder","Binary","-","0=no; 1=yes","Descriptive / optional covariate",""),
("smoking","Current smoker","Confounder","Binary","-","0=no; 1=yes","Multivariable model",""),
("diabetes","Diabetes mellitus","Confounder","Binary","-","0=no; 1=yes","Multivariable model",""),
("asa_class","ASA physical status","Confounder / auxiliary","Categorical (ordinal)","-","1=ASA I; 2=ASA II; 3=ASA III","Multivariable model; predictor of loss to follow-up (MAR)",""),
("osteoporosis_dx","Osteoporosis diagnosis in chart","Confounder","Binary","-","0=no; 1=yes","Fracture model; auxiliary for imputing dxa_tscore","Complete; imperfect proxy of T-score"),
("dxa_tscore","Lowest DXA T-score within 2 years before surgery","Confounder","Continuous","SD","","Fracture model; imputed in MI","Missing ~28% (DXA not performed); MAR on osteoporosis_dx and center"),
("preop_ases","Preoperative ASES score","Confounder","Continuous","points (0-100)","","Baseline adjustment","Missing ~5%"),
("preop_fe","Preoperative active forward elevation","Confounder","Continuous","degrees","","Baseline adjustment for fe_2y",""),
("dsa_r1","Distalization shoulder angle, rater 1","Exposure (measurement)","Continuous","degrees","","Inter-rater reliability ICC(2,1)","Postoperative Grashey view; raters blinded to outcomes and to each other"),
("dsa_r2","Distalization shoulder angle, rater 2","Exposure (measurement)","Continuous","degrees","","Inter-rater reliability ICC(2,1); sensitivity analysis using single rater",""),
("lsa_r1","Lateralization shoulder angle, rater 1","Exposure (measurement)","Continuous","degrees","","Inter-rater reliability ICC(2,1)",""),
("lsa_r2","Lateralization shoulder angle, rater 2","Exposure (measurement)","Continuous","degrees","","Inter-rater reliability ICC(2,1); sensitivity analysis",""),
("agtd_r1","Acromion-greater tuberosity distance, rater 1","Exposure (measurement)","Continuous","mm","","Inter-rater reliability ICC(2,1)",""),
("agtd_r2","Acromion-greater tuberosity distance, rater 2","Exposure (measurement)","Continuous","mm","","Inter-rater reliability ICC(2,1)",""),
("ahi_mm","Acromiohumeral interval (postoperative)","Exposure (component)","Continuous","mm","","Component of DLI",""),
("aho_mm","Acromiohumeral offset (postoperative)","Exposure (component)","Continuous","mm","","Component of DLI",""),
("dsa","Distalization shoulder angle, mean of 2 raters","Primary exposure","Continuous","degrees","","Restricted cubic spline (3-4 knots) in outcome models","= (dsa_r1+dsa_r2)/2"),
("lsa","Lateralization shoulder angle, mean of 2 raters","Primary exposure","Continuous","degrees","","Restricted cubic spline (3-4 knots) in outcome models","= (lsa_r1+lsa_r2)/2"),
("agtd","Acromion-greater tuberosity distance, mean of 2 raters","Secondary exposure","Continuous","mm","","Restricted cubic spline","= (agtd_r1+agtd_r2)/2"),
("dli","Distalization-lateralization index","Secondary exposure","Continuous","mm","","Restricted cubic spline","= sqrt(ahi_mm^2 + aho_mm^2)"),
("ases_2y","ASES score at 2 years","Primary outcome 1","Continuous","points (0-100)","","Linear regression with splines; MI for missing","Missing when lost to follow-up (MAR on age, ASA, center)"),
("ases_mcid","Achieved ASES MCID at 2 years","Secondary outcome","Binary","-","0=no; 1=yes (ases_2y - preop_ases >= 20.9)","Logistic regression","Missing if ases_2y or preop_ases missing; derive after imputation"),
("fe_2y","Active forward elevation at 2 years","Secondary outcome","Continuous","degrees","","Linear regression",""),
("er_2y","Active external rotation at side at 2 years","Secondary outcome","Continuous","degrees","","Linear regression","Additional ~5% sporadic missing"),
("stress_fracture","Acromial or scapular spine stress fracture during follow-up","Primary outcome 2","Binary","-","0=no; 1=yes","Logistic or Cox model with spline for dsa","Events ~7%; limit model df (events per variable)"),
("levy_type","Levy classification of stress fracture","Outcome detail","Categorical (ordinal)","-","1=type I; 2=type II; 3=type III","Descriptive","Not applicable (blank) if stress_fracture=0"),
("time_to_fracture_mo","Time from surgery to stress fracture diagnosis","Outcome (time)","Continuous","months","","Time-to-event analysis","Not applicable (blank) if stress_fracture=0; censor others at followup_mo"),
("reoperation","Any reoperation on index shoulder","Secondary outcome","Binary","-","0=no; 1=yes","Descriptive","Few events"),
("followup_mo","Duration of follow-up","Follow-up","Continuous","months","","Report mean/median (STROBE 14c); censoring time",""),
("lost_to_followup","Lost to follow-up before 24 months","Follow-up / missingness indicator","Binary","-","0=no; 1=yes","Compare retained vs lost (STROBE 12d, 13b); MI diagnostics",""),
]
assert [v[0] for v in V] == list(d.columns)
rows = []
for i, (nm, lab, role, typ, unit, codes, use, note) in enumerate(V, 1):
    s = d[nm]; nv = int(s.notna().sum()); nm_ = int(s.isna().sum())
    if typ.startswith(("Continuous", "Discrete")) and nm != "surgery_year":
        obs = f"mean {s.mean():.1f}; SD {s.std():.1f}; median {s.median():.1f}; min {s.min():g}; max {s.max():g}"
    elif nm == "patient_id":
        obs = "240 unique"
    else:
        obs = "; ".join(f"{int(k)}: n={c}" for k, c in s.value_counts().sort_index().items())
    rows.append(dict(section="variable", var_no=i, variable=nm, label=lab, role=role, type=typ, unit=unit,
                     value_codes=codes, missing_code="blank cell = missing / not applicable",
                     n_valid=nv, n_missing=nm_, observed_summary=obs, analysis_use=use, notes=note))
excl = pd.read_csv(D + "/_exclusions.tmp")
flow = "Screened 300 consecutive primary RTSA (4 centers, 2016-2022); excluded 60: " + \
       "; ".join(f"{r.iloc[0]} n={r.iloc[1]}" for _, r in excl.iterrows()) + \
       f"; included 240; completed >=24-month follow-up {int((d.lost_to_followup==0).sum())}; lost {int(d.lost_to_followup.sum())}"
info = [
 ("SIMULATED DATA","All records are synthetic, generated by computer (seed 20261022) for teaching STROBE-based manuscript writing; they do not describe real patients and must not be reported as real study results."),
 ("Design","Multicenter retrospective cohort study; exposure = postoperative radiographic distalization/lateralization after RTSA"),
 ("Study flow (STROBE 13a/13b)", flow),
 ("Built-in data features","Nonlinear (inverted-U) association of lsa and dsa with ases_2y; monotone increasing fracture risk with dsa, lower T-score, female sex; center effects; MAR missingness in outcomes and dxa_tscore; two independent raters for dsa/lsa/agtd"),
 ("Suggested analyses","ICC(2,1) for rater pairs; restricted cubic splines (3-4 knots) for dsa/lsa/agtd/dli; multivariable linear (ases_2y, fe_2y, er_2y) and logistic/Cox (stress_fracture) models; multiple imputation by chained equations (m>=20) including auxiliary variables (asa_class, center, osteoporosis_dx); sensitivity analyses: complete-case vs MI, single-rater exposure, excluding fracture sequelae (diagnosis=4), center as random effect"),
]
for k, (lab, note) in enumerate(info, 1):
    rows.append(dict(section="study_info", var_no=f"I{k}", variable="", label=lab, role="", type="", unit="",
                     value_codes="", missing_code="", n_valid="", n_missing="", observed_summary="", analysis_use="", notes=note))
with open(D + "/code_book.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows)); print(flow)
