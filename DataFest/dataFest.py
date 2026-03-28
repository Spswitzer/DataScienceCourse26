# Locate 'development.csv' in the current workspace and read the first match into df_development.
import pandas as pd
import plotnine as ggplot

#import data from csv files ---- 
df_departments = pd.read_csv('departments.csv')
df_diagnosis = pd.read_csv('diagnosis.csv')
df_encounters = pd.read_csv('encounters.csv')
df_patients = pd.read_csv('patients.csv')
df_providers = pd.read_csv('providers.csv')
df_social_determinants = pd.read_csv('social_determinants.csv')
df_census_codes = pd.read_csv('tigercensuscodes.csv')

# Create cohort  ---- 
# ── 1. Kansas census blocks (state FIPS = "20") ──────────────────────────────
ks_census = df_census_codes.copy()
ks_census["GEOID"] = ks_census["GEOID"].astype(str)
ks_census = ks_census[ks_census["GEOID"].str.startswith("20")]
print(f"Kansas census block groups: {len(ks_census):,}")

# ── 2. Kansas patients ────────────────────────────────────────────────────────
patients = df_patients.copy()
patients["CensusBlockGroupFipsCode"] = patients["CensusBlockGroupFipsCode"].astype(str)

ks_patients = patients.merge(
    ks_census[["GEOID", "CENTLAT", "CENTLON", "PopulationValue"]],
    left_on="CensusBlockGroupFipsCode",
    right_on="GEOID",
    how="inner",
)
print(f"Kansas patients: {len(ks_patients):,}")

# ── 3. Kansas encounters ──────────────────────────────────────────────────────
ks_patients["DurableKey"] = ks_patients["DurableKey"].astype("Int64")
df_encounters["PatientDurableKey"] = df_encounters["PatientDurableKey"].astype("Int64")

ks_encounters = df_encounters.merge(
    ks_patients[["DurableKey"]],
    left_on="PatientDurableKey",
    right_on="DurableKey",
    how="inner",
)
print(f"Kansas encounters: {len(ks_encounters):,}")

# ── 4. Diagnosis lookup ───────────────────────────────────────────────────────
ks_diagnosis = df_diagnosis.rename(columns={
    "DiagnosisName": "PrimaryDiagnosisName",
    "GroupName":     "DiagnosisGroupName",
    "GroupCode":     "DiagnosisGroupCode",
    "DiagnosisValue":"DiagnosisICD",
})
ks_diagnosis["DiagnosisKey"] = ks_diagnosis["DiagnosisKey"].astype("Int64")
ks_encounters["PrimaryDiagnosisKey"] = ks_encounters["PrimaryDiagnosisKey"].astype("Int64")

# ── 5. Join encounters → diagnosis ───────────────────────────────────────────
ks_cohort = ks_encounters.merge(
    ks_diagnosis[["DiagnosisKey", "PrimaryDiagnosisName",
                  "DiagnosisGroupName", "DiagnosisGroupCode", "DiagnosisICD"]],
    left_on="PrimaryDiagnosisKey",
    right_on="DiagnosisKey",
    how="left",
)

# ── 6. Join encounters → patient demographics ─────────────────────────────────
ks_cohort = ks_cohort.merge(
    ks_patients[[
        "DurableKey", "SexAssignedAtBirth", "OmbRace", "OmbEthnicity",
        "MaritalStatus", "SmokingStatus", "VitalStatus",
        "PatientBirthYearBin", "CENTLAT", "CENTLON",
    ]],
    left_on="PatientDurableKey",
    right_on="DurableKey",
    how="left",
)

print(f"\nFull Kansas cohort: {len(ks_cohort):,} rows x {ks_cohort.shape[1]} cols")
print(f"Columns: {list(ks_cohort.columns)}")


# Social Determinents of Health----

# ── 1. Filter SDOH to Kansas patients only, drop nulls/unspecified ────────────
ks_patient_ids = set(ks_cohort["PatientDurableKey"].dropna().astype("Int64").unique())

sdoh_ks = (
    df_social_determinants
    .copy()
    .assign(PatientDurableKey=lambda d: d["PatientDurableKey"].astype("Int64"))
    .query("PatientDurableKey in @ks_patient_ids")
    .dropna(subset=["Domain"])                    # drop unspecified domain
    .query("Domain != '*Unspecified'")
    .query("AnswerText not in ['Unknown', '*Unspecified']")
)



# ── 2. Patient-level outcomes from ks_cohort ─────────────────────────────────
# Outcome = had at least one ED visit or inpatient admission (acute care flag)
patient_outcomes = (
    ks_cohort
    .groupby("PatientDurableKey", as_index=False)
    .agg(
        TotalEncounters   = ("EncounterKey",              "count"),
        AnyED             = ("IsEdVisit",                 "max"),
        AnyInpatient      = ("IsInpatientAdmission",      "max"),
        VitalStatus       = ("VitalStatus",               "first"),
    )
    .assign(
        AcuteOutcome=lambda d: ((d["AnyED"] == 1) | (d["AnyInpatient"] == 1)).astype(int)
    )
)


# ── 3. One SDOH flag per patient per domain (any positive screen) ─────────────
# Map answer text to a positive/negative screen per domain
# Strategy: flag presence of a known risk answer per domain
risk_answers = {
    "Food insecurity":          ["Sometimes true", "Often true"],
    "Transportation Needs":     ["Yes"],
    "Financial Resource Strain":["Hard", "Very hard"],
    "Housing Stability":        ["Yes"],
    "Utilities":                ["Yes"],
    "stress":                   ["Yes"],
    "Depression":               ["Yes", "Several days", "More than half the days",
                                  "Nearly every day"],
    "intimate partner violance":["Yes"],
    "Alcohol Use":              ["Monthly or less", "2-4 times a month",
                                  "2-3 times a week", "4 or more times a week"],
    "social connections":       ["Rarely", "Never"],
    "physical activity":        ["0"],
}

# For domains without a clear risk mapping, use "any response" as a screen flag
sdoh_patient_domain = (
    sdoh_ks
    .assign(
        RiskFlag=lambda d: d.apply(
            lambda r: 1 if r["AnswerText"] in risk_answers.get(r["Domain"], []) else 0,
            axis=1,
        )
    )
    .groupby(["PatientDurableKey", "Domain"], as_index=False)
    .agg(AnyRisk=("RiskFlag", "max"))
)

# Merge with outcomes
sdoh_outcomes = sdoh_patient_domain.merge(
    patient_outcomes[["PatientDurableKey", "AcuteOutcome", "TotalEncounters", "VitalStatus"]],
    on="PatientDurableKey",
    how="inner",
)

sdoh_outcomes.head(6)


# ── Chart 2: Risk gap (At Risk minus Not at Risk) — sorted by impact ──────────
risk_gap = (
    domain_summary
    .pivot_table(
        index="DomainLabel",
        columns="RiskLabel",
        values="AcuteRate",
    )
    .reset_index()
    .assign(RiskGap=lambda d: d["At Risk"] - d["Not at Risk"])
    .dropna(subset=["RiskGap"])
    .sort_values("RiskGap", ascending=True)
)

#Plot Risk gap with mathplotlib ----
import matplotlib.pyplot as plt
plt.figure(figsize=(8, 6))
plt.barh(risk_gap["DomainLabel"], risk_gap["RiskGap"], color="#2ca02c")
plt.xlabel("Risk Gap (At Risk - Not at Risk)", fontsize=12)
plt.title("Difference in Acute Outcome Rates by SDOH Risk Status", fontsize=14, fontweight="bold", pad=16)
plt.axvline(0, color="#cccccc", linewidth=0.8)
risk_gap.plot(y="RiskGap", x="DomainLabel", kind="barh", color="#2ca02c", legend=False)
# end for)
#Ridgeline plot ----


from scipy.stats import gaussian_kde
import numpy as np

# ── Prep: cap at 95th pct to avoid long tails squashing densities ─────────────
CAP = 200

domains_ordered = [
    "social connections",
    "physical activity",
    "Alcohol Use",
    "stress",
    "Depression",
    "Utilities",
    "Financial Resource Strain",
    "Food insecurity",
    "Transportation Needs",
    "Housing Stability",
    "intimate partner violance",
]
domain_labels = {
    "social connections":         "Social Connections",
    "physical activity":          "Physical Activity",
    "Alcohol Use":                "Alcohol Use",
    "stress":                     "Stress",
    "Depression":                 "Depression",
    "Utilities":                  "Utilities",
    "Financial Resource Strain":  "Financial Strain",
    "Food insecurity":            "Food Insecurity",
    "Transportation Needs":       "Transportation Needs",
    "Housing Stability":          "Housing Stability",
    "intimate partner violance":  "Intimate Partner Violence",
}

risk_colors  = {"At Risk": "#d73027", "Not at Risk": "#4575b4"}
x_grid = np.linspace(0, CAP, 500)

# ── Build KDEs ────────────────────────────────────────────────────────────────
kde_data = {}
for domain in domains_ordered:
    kde_data[domain] = {}
    for risk_val, label in [(1, "At Risk"), (0, "Not at Risk")]:
        vals = (
            sdoh_outcomes
            .query("Domain == @domain and AnyRisk == @risk_val")
            ["TotalEncounters"]
            .clip(upper=CAP)
            .dropna()
            .values
        )
        if len(vals) > 10:
            kde = gaussian_kde(vals, bw_method=0.3)
            kde_data[domain][label] = kde(x_grid)
        else:
            kde_data[domain][label] = np.zeros_like(x_grid)

# ── Plot ──────────────────────────────────────────────────────────────────────
import seaborn as sns
sns.set_style("white")

n = len(domains_ordered)
overlap = 2.2          # how much ridges overlap
fig_height = 1.5 * n
fig, ax = plt.subplots(figsize=(11, fig_height))

ax.set_xlim(0, CAP)
ax.set_ylim(-0.5, n * overlap)
ax.set_xlabel("Total Encounters per Patient (capped at 200)", fontsize=12)
ax.set_title(
    "Distribution of Patient Encounter Volume by SDOH Risk Area",
    fontsize=14, fontweight="bold", pad=16,
)

for i, domain in enumerate(domains_ordered):
    y_base = i * overlap
    label  = domain_labels[domain]

    for risk_label, color in risk_colors.items():
        density = kde_data[domain].get(risk_label, np.zeros_like(x_grid))
        # scale so max height ~ 1 unit
        scale = density.max() if density.max() > 0 else 1
        y_vals = y_base + (density / scale) * (overlap * 0.85)

        ax.fill_between(x_grid, y_base, y_vals,
                        alpha=0.45, color=color, linewidth=0)
        ax.plot(x_grid, y_vals,
                color=color, linewidth=1.2, alpha=0.9,
                label=risk_label if i == 0 else "_nolegend_")

    # Domain label on the left
    ax.text(-3, y_base + 0.1, label,
            ha="right", va="bottom", fontsize=9.5, color="black")

# Baseline rules
for i in range(n):
    ax.axhline(i * overlap, color="white", linewidth=0.8, zorder=0)

ax.set_yticks([])
ax.spines[["left","right","top"]].set_visible(False)
ax.spines["bottom"].set_color("#cccccc")


plt.tight_layout()
plt.show()
