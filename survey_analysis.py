"""
Descriptive analysis of the questionnaire (Instrument 1)
Study: Digital communication and public perceptions of diesel emissions
       and air pollution, Capricorn District

How to use
----------
1. Put the CSV in data/raw/ (see the README).
2. Install the libraries once:   pip install -r requirements.txt
3. Run from anywhere:           python src/survey_analysis.py
4. Tables go to results/tables, charts to results/figures.

The script is split into numbered steps. Read each step, run it, and look at
what it produces before moving on.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]          # the project folder
DATA_FILE = ROOT / "data" / "raw" / "Digital_Communication_and_Public_Perceptions_of_Diesel_Emissions___Air_Pollution.csv"
TAB_DIR = ROOT / "results" / "tables"
FIG_DIR = ROOT / "results" / "figures"
TAB_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_FILE.exists():
    raise SystemExit(f"Data file not found:\n  {DATA_FILE}\nPut the CSV in data/raw/ first (see README).")

# ----------------------------------------------------------------------
# STEP 1. Load the data and look at it
# ----------------------------------------------------------------------
df = pd.read_csv(DATA_FILE)
print("Rows, columns:", df.shape)

# ----------------------------------------------------------------------
# STEP 2. Give every column a short name
# The Google Forms headers are very long. Short names are easier to work
# with. This relies on the columns being in the same order as the export.
# ----------------------------------------------------------------------
short_names = [
    "timestamp", "consent",
    "gender", "age", "education", "area", "employment",                      # Section A
    "internet_freq", "device", "platforms", "env_content_freq",              # Section B
    "aware_diesel_pollution", "aware_health_risk", "aware_pm25", "aware_local_info",   # C1
    "first_learned",                                                         # C2
    "perc_serious_threat", "perc_quality_of_life", "perc_family_worry",
    "perc_govt_enough", "perc_industry_responsible", "perc_individual_action",         # Perceptions
    "role_increased_awareness", "role_changed_thinking", "role_trust_social",
    "role_trust_govt_sites", "role_news_helped", "role_shared_content",
    "role_easy_discussion", "role_misinformation_common",                    # Role of digital
    "framing_main",                                                          # F1
    "frame_health", "frame_blame", "frame_practical", "frame_balanced",
    "frame_emotional_share",                                                 # Framing battery
    "act_discussed", "act_contacted_govt", "act_community_initiative",
    "act_digital_motivated",                                                 # Community action
    "open_comment",                                                          # G2
]
assert len(short_names) == df.shape[1], "Column count has changed - check the export."

# Keep the original long headers so you can still quote the exact question wording
codebook = pd.DataFrame({"short_name": short_names, "original_question": df.columns})
df.columns = short_names

# ----------------------------------------------------------------------
# STEP 3. Clean the data
# ----------------------------------------------------------------------
# 3a. Consent: keep only people who said Yes
print("\nConsent values:\n", df["consent"].value_counts(dropna=False))
df = df[df["consent"].str.strip().str.lower().str.startswith("yes")].copy()
assert len(df) > 0, "No respondents left after the consent filter - check the consent wording above."

# 3b. Strip stray spaces from every text answer
for c in df.columns:
    if not pd.api.types.is_numeric_dtype(df[c]):
        df[c] = df[c].astype("string").str.strip()

# 3c. Fix typos in the response labels (add more here if you spot others)
df = df.replace({"Strongly Diagree": "Strongly Disagree"})

# 3d. Set the order of the Likert categories so tables do not sort alphabetically
agree_order = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
aware_order = ["Not Aware", "Somewhat aware", "Aware"]

agree_cols = [c for c in df.columns if c.startswith(("perc_", "role_", "frame_", "act_"))]
aware_cols = [c for c in df.columns if c.startswith("aware_")]

for c in agree_cols:
    df[c] = pd.Categorical(df[c], categories=agree_order, ordered=True)
for c in aware_cols:
    df[c] = pd.Categorical(df[c], categories=aware_order, ordered=True)

# 3e. Check for anything unexpected: a value outside the expected categories
#     becomes NaN above, so any NaN here (except the open comment) needs a look.
missing = df.drop(columns=["open_comment"]).isna().sum()
print("\nMissing values (should all be 0):\n", missing[missing > 0])

N = len(df)
print("\nValid respondents (N):", N)

# ----------------------------------------------------------------------
# STEP 4. A helper that makes a frequency table (count and percent)
# ----------------------------------------------------------------------
def freq(series, order=None):
    counts = series.value_counts(dropna=False)
    if order is not None:
        counts = counts.reindex(order, fill_value=0)
    out = pd.DataFrame({"n": counts.astype(int)})
    out["%"] = (out["n"] / len(series) * 100).round(1)
    return out

# ----------------------------------------------------------------------
# STEP 5. Section 4.2  Sample profile (single-select items)
# ----------------------------------------------------------------------
tables = {}
for c in ["gender", "age", "education", "area", "employment"]:
    tables[f"4.2_{c}"] = freq(df[c])

# ----------------------------------------------------------------------
# STEP 6. Section 4.3  Platforms and content (Objective 1)
# ----------------------------------------------------------------------
for c in ["internet_freq", "device", "env_content_freq", "first_learned"]:
    tables[f"4.3_{c}"] = freq(df[c])

# Platforms is a "tick all that apply" question. Answers are separated by
# semicolons, so split them first. Percent is of RESPONDENTS, so it adds to
# more than 100.
platforms = df["platforms"].dropna().str.split(";").explode().str.strip()
plat = platforms.value_counts().to_frame("n")
plat["% of respondents"] = (plat["n"] / N * 100).round(1)
tables["4.3_platforms"] = plat

# ----------------------------------------------------------------------
# STEP 7. Section 4.4  Perceived risk and the role of digital communication
# (Objective 2)
# ----------------------------------------------------------------------
for c in aware_cols:
    tables[f"4.4_{c}"] = freq(df[c], aware_order)

for c in [x for x in agree_cols if x.startswith(("perc_", "role_"))]:
    tables[f"4.4_{c}"] = freq(df[c], agree_order)

tables["4.4_framing_main"] = freq(df["framing_main"])
for c in [x for x in agree_cols if x.startswith("frame_")]:
    tables[f"4.4_{c}"] = freq(df[c], agree_order)

# ----------------------------------------------------------------------
# STEP 8. Section 4.5  Behavioural and attitudinal responses (Objective 3)
# ----------------------------------------------------------------------
for c in [x for x in agree_cols if x.startswith("act_")]:
    tables[f"4.5_{c}"] = freq(df[c], agree_order)

# ----------------------------------------------------------------------
# STEP 9. Summary scores (optional, but useful for the Likert batteries)
# Convert to 1-5, then report mean and standard deviation per item.
# Note: Likert items are ordinal, so report these alongside the percentages,
# not instead of them.
# ----------------------------------------------------------------------
def to_score(series, order):
    return series.cat.codes.replace(-1, pd.NA).astype("float") + 1

rows = []
for c in agree_cols:
    s = to_score(df[c], agree_order)
    rows.append({"item": c, "mean": round(s.mean(), 2), "sd": round(s.std(), 2),
                 "median": s.median(),
                 "% agree + strongly agree": round(df[c].isin(["Agree", "Strongly Agree"]).mean() * 100, 1),
                 "% disagree + strongly disagree": round(df[c].isin(["Disagree", "Strongly Disagree"]).mean() * 100, 1)})
tables["4.4_4.5_likert_summary"] = pd.DataFrame(rows).set_index("item")

# ----------------------------------------------------------------------
# STEP 10. Cross-tabulations (ONE demographic variable at a time, as stated
# in Chapter 3). With N = 50, small cells make percentages unstable, so
# always read the counts, not just the percentages.
# Change the two names below to explore other pairs.
# ----------------------------------------------------------------------
def crosstab(row_var, col_var):
    ct = pd.crosstab(df[row_var], df[col_var], margins=True)
    pct = (pd.crosstab(df[row_var], df[col_var], normalize="index") * 100).round(1)
    return ct, pct

ct_n, ct_pct = crosstab("age", "env_content_freq")
tables["X_age_by_env_content_n"] = ct_n
tables["X_age_by_env_content_pct"] = ct_pct

# Example linking digital communication to action (relevant to RQ3):
ct_n, ct_pct = crosstab("role_increased_awareness", "act_digital_motivated")
tables["X_role_awareness_by_motivated_n"] = ct_n
tables["X_role_awareness_by_motivated_pct"] = ct_pct

# ----------------------------------------------------------------------
# STEP 11. Save all tables to one Excel workbook
# ----------------------------------------------------------------------
with pd.ExcelWriter(TAB_DIR / "survey_tables.xlsx") as writer:
    codebook.to_excel(writer, sheet_name="codebook", index=False)
    for name, tab in tables.items():
        tab.to_excel(writer, sheet_name=name[:31])      # Excel sheet names max 31 chars

# ----------------------------------------------------------------------
# STEP 12. Charts for Chapter 4
# ----------------------------------------------------------------------
def bar_chart(table, title, filename, col="%"):
    ax = table[col].sort_values().plot(kind="barh", figsize=(7, 4), color="#2E5C8A")
    ax.set_xlabel(f"% of respondents (N = {N})")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(FIG_DIR / filename, dpi=200)
    plt.close()

def likert_chart(cols, labels, order, title, filename, colors):
    data = pd.DataFrame({lab: freq(df[c], order)["%"] for lab, c in zip(labels, cols)}).T
    ax = data.plot(kind="barh", stacked=True, figsize=(9, 4.5), color=colors)
    ax.set_xlabel(f"% of respondents (N = {N})")
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=len(order), frameon=False)
    plt.tight_layout()
    plt.savefig(FIG_DIR / filename, dpi=200)
    plt.close()

five_colors = ["#C0392B", "#E67E22", "#BDBDBD", "#7FB3D5", "#2E5C8A"]
three_colors = ["#C0392B", "#F0AD4E", "#2E7D32"]

bar_chart(plat, "Social media platforms used regularly", "fig_platforms.png", col="% of respondents")
bar_chart(tables["4.4_framing_main"], "How diesel emission content is framed online", "fig_framing_main.png")

likert_chart(aware_cols, aware_cols, aware_order, "General awareness", "fig_awareness.png", three_colors)
likert_chart([c for c in agree_cols if c.startswith("perc_")],
             [c for c in agree_cols if c.startswith("perc_")],
             agree_order, "Perceptions of diesel emissions", "fig_perceptions.png", five_colors)
likert_chart([c for c in agree_cols if c.startswith("role_")],
             [c for c in agree_cols if c.startswith("role_")],
             agree_order, "Role of digital communication", "fig_role_digital.png", five_colors)
likert_chart([c for c in agree_cols if c.startswith("frame_")],
             [c for c in agree_cols if c.startswith("frame_")],
             agree_order, "Framing of messages", "fig_framing_battery.png", five_colors)
likert_chart([c for c in agree_cols if c.startswith("act_")],
             [c for c in agree_cols if c.startswith("act_")],
             agree_order, "Community awareness and action", "fig_action.png", five_colors)

# ----------------------------------------------------------------------
# STEP 13. Template for coding the open-ended comments (G2)
# This creates a spreadsheet with one row per comment and empty columns for
# YOUR coding against the Section 3.6 categories. Fill it in by hand; the
# interpretation is the part that has to be yours.
# ----------------------------------------------------------------------
comments = df.loc[df["open_comment"].notna(), ["open_comment"]].reset_index(drop=True)
comments.insert(0, "id", ["G2-" + str(i + 1).zfill(2) for i in range(len(comments))])
for col in ["problem_definition", "causal_interpretation", "moral_evaluation",
            "treatment_recommendation",                 # Entman
            "access_participation", "communicative_vs_strategic",
            "deliberative_quality",                     # Habermas
            "other_theme", "notes"]:
    comments[col] = ""
comments.to_excel(TAB_DIR / "G2_coding_template.xlsx", index=False)

print("\nDone. Open the 'results' folder for the tables, charts and coding template.")
