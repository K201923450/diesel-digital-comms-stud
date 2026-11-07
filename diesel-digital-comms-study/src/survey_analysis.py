from pathlib import Path
import re
import textwrap
import warnings

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --------------------------------------------------
# 1. Project paths and settings
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
FIGURES_DIR = PROJECT_DIR / "results" / "figures"
TABLES_DIR = PROJECT_DIR / "results" / "tables"

for folder in (PROCESSED_DIR, FIGURES_DIR, TABLES_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# Review this setting against the original Excel cells.
# Google Forms multiple-selection answers commonly use commas.
PLATFORM_SEPARATOR_PATTERN = r"\s*,\s*"

LIKERT_ORDER = [
    "Strongly disagree",
    "Disagree",
    "Neither agree nor disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]

# --------------------------------------------------
# 2. Load the survey
# --------------------------------------------------
files = sorted(
    list(RAW_DIR.glob("*.xlsx")) + list(RAW_DIR.glob("*.xls"))
)

if len(files) == 0:
    raise FileNotFoundError(f"No Excel file found in {RAW_DIR}")

if len(files) > 1:
    raise RuntimeError(
        f"Found {len(files)} Excel files in {RAW_DIR}. "
        "Keep the survey file there or specify the correct file explicitly."
    )

source_file = files[0]
df = pd.read_excel(source_file)
df.columns = [str(c).strip() for c in df.columns]

print("=" * 60)
print("DIESEL EMISSIONS SURVEY ANALYSIS")
print("=" * 60)
print(f"Source file: {source_file.name}")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

# Preserve original data; save a working copy.
df.to_csv(PROCESSED_DIR / "survey_responses.csv", index=False)

# --------------------------------------------------
# 3. Identify key survey columns
# --------------------------------------------------
def find_columns(prefix):
    return [c for c in df.columns if c.startswith(prefix)]

consent_columns = find_columns(
    "Do you consent to participate in this study?"
)
g2_columns = find_columns("G2.")
b3_columns = find_columns("B3.")
timestamp_columns = find_columns("Timestamp")

# --------------------------------------------------
# 4. Missing-data report
# --------------------------------------------------
missing = pd.DataFrame({
    "variable": df.columns,
    "missing_count": df.isna().sum().values,
    "missing_percent": (df.isna().mean().values * 100).round(1),
})

missing.to_csv(TABLES_DIR / "missing_data_summary.csv", index=False)

print("\nMissing-data report saved.")

# --------------------------------------------------
# 5. Consent audit: flag, do not silently exclude
# --------------------------------------------------
if consent_columns:
    consent_col = consent_columns[0]
    consent_audit = (
        df[consent_col]
        .fillna("[Blank]")
        .astype(str)
        .value_counts(dropna=False)
        .rename_axis("consent_response")
        .reset_index(name="count")
    )
    consent_audit.to_csv(
        TABLES_DIR / "consent_audit.csv", index=False
    )
    print("\nConsent responses:")
    print(consent_audit.to_string(index=False))
    print(
        "IMPORTANT: Verify consent and eligibility before finalising "
        "the analysis sample. No rows have been automatically excluded."
    )
else:
    print("\nWARNING: Consent column not found. Check the questionnaire.")

# --------------------------------------------------
# 6. G2: preserve for separate thematic analysis
# --------------------------------------------------
if g2_columns:
    g2_col = g2_columns[0]
    g2 = df[[g2_col]].copy()
    g2.columns = ["response"]
    g2["response"] = g2["response"].astype("string").str.strip()
    g2 = g2[g2["response"].notna() & g2["response"].ne("")]
    g2.insert(0, "response_id", range(1, len(g2) + 1))

    g2.to_csv(
        PROCESSED_DIR / "g2_open_ended_responses.csv",
        index=False
    )
    print(f"\nUsable nonblank G2 responses: {len(g2)}")
    print("G2 is excluded from automatic charts and frequency tables.")
else:
    print("\nG2 column not found. Check the questionnaire heading.")

# --------------------------------------------------
# 7. Research-objective classification
# --------------------------------------------------
def objective_for(column):
    if column.startswith(("B1.", "B2.", "B3.", "B4.", "C2.", "F1.")):
        return "Objective 1 - Digital channels and content"

    if column.startswith((
        "C1.",
        "Perceptions of Diesel Emissions",
        "Role of Digital Communication",
        "Framing of Diesel Emission",
    )):
        return "Objective 2 - Awareness and perceptions"

    if column.startswith("Community Awareness and Action"):
        return "Objective 3 - Behaviour and action"

    return None

def safe_name(text):
    name = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return name.strip("_")[:70] or "variable"

# --------------------------------------------------
# 8. Frequency tables and selected charts
# --------------------------------------------------
for column in df.columns:
    if (
        column in timestamp_columns
        or column in consent_columns
        or column in g2_columns
        or column in b3_columns
    ):
        continue

    values = df[column].dropna().astype(str).str.strip()
    values = values[values.ne("")]

    if values.empty:
        continue

    # Avoid interpreting long free text or identifiers as categories.
    if values.nunique() > 20:
        continue

    counts = values.value_counts()
    table = counts.rename_axis("response").reset_index(name="count")
    valid_n = int(table["count"].sum())
    table["percent_of_valid_responses"] = (
        table["count"] / valid_n * 100
    ).round(1)
    table["valid_responses_n"] = valid_n

    objective = objective_for(column)
    table.insert(0, "research_objective", objective or "Respondent profile")

    filename = safe_name(column)
    table.to_csv(
        TABLES_DIR / f"{filename}_frequencies.csv",
        index=False
    )

    # Only create charts for research-objective variables.
    if objective is None:
        continue

    # Preserve the intended order of common Likert responses.
    observed = list(counts.index)
    ordered = [x for x in LIKERT_ORDER if x in observed]
    ordered += [x for x in observed if x not in ordered]
    plot_counts = counts.reindex(ordered).sort_values()

    fig_height = max(4.5, 0.42 * len(plot_counts))
    fig, ax = plt.subplots(figsize=(11, fig_height))

    plot_counts.plot(kind="barh", ax=ax)

    ax.set_title(
        textwrap.fill(column, width=72),
        fontsize=10,
        pad=12
    )
    ax.set_xlabel("Number of valid responses")
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)

    fig.tight_layout(pad=2.0)
    fig.savefig(
        FIGURES_DIR / f"{filename}_bar.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close(fig)

# --------------------------------------------------
# 9. B3: multiple-response platform analysis
# --------------------------------------------------
if b3_columns:
    platform_col = b3_columns[0]
    raw_platform_values = (
        df[platform_col].dropna().astype(str).str.strip()
    )
    raw_platform_values = raw_platform_values[
        raw_platform_values.ne("")
    ]

    # Check actual Excel formatting if platform names contain
    # commas or the answers are not comma-separated.
    selections = raw_platform_values.str.split(
        PLATFORM_SEPARATOR_PATTERN
    ).explode().str.strip()
    selections = selections[selections.ne("")]

    platform_counts = (
        selections.value_counts()
        .rename_axis("platform")
        .reset_index(name="selection_count")
    )

    denominator = len(raw_platform_values)
    platform_counts["respondents_with_platform_selection"] = denominator
    platform_counts["percent_of_respondents"] = (
        platform_counts["selection_count"] / len(df) * 100
    ).round(1)
    platform_counts["percent_of_all_selections"] = (
        platform_counts["selection_count"]
        / max(int(platform_counts["selection_count"].sum()), 1)
        * 100
    ).round(1)

    platform_counts.to_csv(
        TABLES_DIR / "B3_platform_use_multiple_response.csv",
        index=False
    )

    if not platform_counts.empty:
        plot_data = platform_counts.sort_values("selection_count")
        fig, ax = plt.subplots(
            figsize=(10, max(4.5, 0.45 * len(plot_data)))
        )
        ax.barh(plot_data["platform"], plot_data["selection_count"])
        ax.set_title("Regularly Used Social Media Platforms")
        ax.set_xlabel("Number of selections")
        ax.set_ylabel("")
        fig.tight_layout(pad=2)
        fig.savefig(
            FIGURES_DIR / "B3_platform_use.png",
            dpi=300,
            bbox_inches="tight"
        )
        plt.close(fig)

    print("\nB3 platform table saved.")
    print(
        "Check that commas separate platforms in the original Excel "
        "responses before reporting these counts."
    )
else:
    print("\nB3 platform question not found.")

# --------------------------------------------------
# 10. Final report
# --------------------------------------------------
print("\n" + "=" * 60)
print("ANALYSIS COMPLETED")
print("=" * 60)
print(f"Processed data: {PROCESSED_DIR}")
print(f"Tables: {TABLES_DIR}")
print(f"Figures: {FIGURES_DIR}")
print("\nReview consent, duplicate submissions, coding and B3 separators.")
print("No inferential tests or causal claims have been generated.")

