from pathlib import Path
import re
import textwrap

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# 1. PROJECT PATHS
# ---------------------------------------------------------
ROOT = Path.cwd()
RAW_DIR = ROOT / "data" / "raw"
TABLE_DIR = ROOT / "results" / "tables"
FIGURE_DIR = ROOT / "results" / "figures"
REPORT_DIR = ROOT / "results"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

files = list(RAW_DIR.glob("*.xlsx"))
files = [f for f in files if not f.name.startswith("~$")]

if len(files) != 1:
    raise FileNotFoundError(
        f"Expected exactly one Excel file in {RAW_DIR}, "
        f"but found {len(files)}. Check the raw-data folder."
    )

source_file = files[0]
df = pd.read_excel(source_file)
df.columns = [str(c).strip() for c in df.columns]

print("=" * 65)
print("CHAPTER 4: DESCRIPTIVE ANALYSIS")
print("=" * 65)
print(f"Source: {source_file.name}")
print(f"Respondents/rows: {len(df)}")
print(f"Variables: {len(df.columns)}")


# ---------------------------------------------------------
# 2. IDENTIFY VARIABLES
# ---------------------------------------------------------
def find_column(prefix):
    matches = [c for c in df.columns if c.startswith(prefix)]
    return matches[0] if matches else None


profile_prefixes = ["A1.", "A2.", "A3.", "A4.", "A5."]
profile_columns = [
    find_column(prefix) for prefix in profile_prefixes
]
profile_columns = [c for c in profile_columns if c is not None]

consent_column = next(
    (c for c in df.columns if "consent" in c.lower()), None
)

b3_column = next(
    (c for c in df.columns if c.startswith("B3.")), None
)

g2_column = next(
    (c for c in df.columns if c.startswith("G2.")), None
)

timestamp_column = next(
    (c for c in df.columns if c.lower() == "timestamp"), None
)


# ---------------------------------------------------------
# 3. REUSABLE FREQUENCY TABLE
# ---------------------------------------------------------
def frequency_table(series, variable_name):
    values = series.dropna().astype(str).str.strip()
    values = values[values.ne("")]

    counts = values.value_counts()
    valid_n = len(values)

    if valid_n == 0:
        return pd.DataFrame(columns=[
            "variable", "response", "count",
            "percent", "valid_n", "missing_count"
        ])

    result = pd.DataFrame({
        "variable": variable_name,
        "response": counts.index,
        "count": counts.values,
        "percent": (counts.values / valid_n * 100).round(1),
        "valid_n": valid_n,
        "missing_count": len(series) - valid_n
    })

    return result


# ---------------------------------------------------------
# 4. PROFILE ANALYSIS: A1-A5
# ---------------------------------------------------------
profile_tables = []

for col in profile_columns:
    table = frequency_table(df[col], col)
    profile_tables.append(table)

if profile_tables:
    profile_results = pd.concat(profile_tables, ignore_index=True)
else:
    profile_results = pd.DataFrame()

profile_results.to_csv(
    TABLE_DIR / "chapter4_respondent_profile.csv",
    index=False
)

print("\nRESPONDENT PROFILE")
print("-" * 65)

for col in profile_columns:
    table = frequency_table(df[col], col)
    print(f"\n{col}")
    if not table.empty:
        print(table[["response", "count", "percent"]].to_string(index=False))
    else:
        print("No valid responses found.")


# ---------------------------------------------------------
# 5. DESCRIPTIVE FREQUENCIES FOR QUESTIONNAIRE VARIABLES
# ---------------------------------------------------------
excluded_columns = {
    c for c in [timestamp_column, g2_column, b3_column]
    if c is not None
}

all_frequency_tables = []

for col in df.columns:
    if col in excluded_columns:
        continue

    # Keep open-ended text out of automatic frequency analysis.
    non_missing = df[col].dropna()
    if len(non_missing) == 0:
        continue

    # Do not create frequency tables for free-text columns.
    if non_missing.astype(str).str.len().median() > 150:
        continue

    table = frequency_table(df[col], col)

    if not table.empty:
        all_frequency_tables.append(table)

if all_frequency_tables:
    descriptive_results = pd.concat(
        all_frequency_tables, ignore_index=True
    )
else:
    descriptive_results = pd.DataFrame()

descriptive_results.to_csv(
    TABLE_DIR / "chapter4_all_descriptive_frequencies.csv",
    index=False
)


# ---------------------------------------------------------
# 6. MISSING-DATA SUMMARY
# ---------------------------------------------------------
missing_summary = pd.DataFrame({
    "variable": df.columns,
    "missing_count": df.isna().sum().values,
    "missing_percent": (
        df.isna().mean().values * 100
    ).round(1)
})

missing_summary.to_csv(
    TABLE_DIR / "chapter4_missing_data_summary.csv",
    index=False
)


# ---------------------------------------------------------
# 7. MULTIPLE-RESPONSE ANALYSIS: B3 PLATFORMS
# ---------------------------------------------------------
if b3_column:
    selections = (
        df[b3_column]
        .dropna()
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
    )

    selections = selections[selections.ne("")]
    platform_counts = selections.value_counts()

    valid_respondents = (
        df[b3_column].dropna().astype(str).str.strip().ne("").sum()
    )

    platform_results = pd.DataFrame({
        "platform": platform_counts.index,
        "selection_count": platform_counts.values
    })

    platform_results["percent_of_respondents"] = (
        platform_results["selection_count"] / len(df) * 100
    ).round(1)

    total_selections = platform_results["selection_count"].sum()

    platform_results["percent_of_all_selections"] = (
        platform_results["selection_count"] / total_selections * 100
    ).round(1)

    platform_results["total_sample_size"] = len(df)
    platform_results["respondents_answering_B3"] = int(valid_respondents)

    platform_results.to_csv(
        TABLE_DIR / "chapter4_platform_use.csv",
        index=False
    )


# ---------------------------------------------------------
# 8. GENERATE FIGURES
# ---------------------------------------------------------
def safe_filename(text):
    name = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return name[:90]


def make_bar_chart(table, label_col, value_col, title, filename):
    if table.empty:
        return

    chart_data = table.sort_values(value_col, ascending=True)

    fig_height = max(4, 0.45 * len(chart_data) + 1)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    bars = ax.barh(
        chart_data[label_col].astype(str),
        chart_data[value_col]
    )

    ax.set_title(textwrap.fill(title, 65))
    ax.set_xlabel("Number of respondents")
    ax.set_ylabel("")
    ax.bar_label(bars, padding=3, fmt="%.0f")
    ax.set_xlim(left=0, right=max(chart_data[value_col]) * 1.18)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    plt.tight_layout()
    fig.savefig(FIGURE_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close(fig)


# Demographic figures
for col in profile_columns:
    table = frequency_table(df[col], col)

    if not table.empty:
        make_bar_chart(
            table,
            "response",
            "count",
            col,
            safe_filename(col) + "_chapter4.png"
        )


# Figures for other categorical/ordinal questions.
# Excludes timestamp, consent, B3 and G2.
for col in df.columns:
    if col in excluded_columns or col == consent_column:
        continue

    series = df[col].dropna().astype(str).str.strip()
    series = series[series.ne("")]

    if series.empty:
        continue

    # Skip free-text answers and columns with too many unique values.
    if series.nunique() > 15 or series.str.len().median() > 150:
        continue

    table = frequency_table(df[col], col)

    if not table.empty:
        make_bar_chart(
            table,
            "response",
            "count",
            col,
            safe_filename(col) + "_chapter4.png"
        )


# Dedicated platform-use figure
if b3_column and (TABLE_DIR / "chapter4_platform_use.csv").exists():
    platform_results = pd.read_csv(
        TABLE_DIR / "chapter4_platform_use.csv"
    )

    make_bar_chart(
        platform_results,
        "platform",
        "selection_count",
        "Regular social media platform use (multiple responses allowed)",
        "chapter4_platform_use.png"
    )


# ---------------------------------------------------------
# 9. EXPORT A MARKDOWN RESULTS REPORT
# ---------------------------------------------------------
report_path = REPORT_DIR / "chapter4_descriptive_results.md"

with report_path.open("w", encoding="utf-8") as report:
    report.write("# Chapter 4: Descriptive Analysis Results\n\n")
    report.write(f"**Source file:** {source_file.name}\n\n")
    report.write(f"**Number of rows:** {len(df)}\n\n")
    report.write(f"**Number of variables:** {len(df.columns)}\n\n")

    report.write("## 4.2.2 Respondent Profile Analysis\n\n")
    report.write(
        "The following tables show respondent counts and percentages "
        "for the demographic profile variables. Percentages are based "
        "on valid responses for each variable.\n\n"
    )

    for col in profile_columns:
        table = frequency_table(df[col], col)
        report.write(f"### {col}\n\n")

        if table.empty:
            report.write("No valid responses.\n\n")
        else:
            report.write(
                table[["response", "count", "percent"]]
                .to_markdown(index=False)
            )
            report.write("\n\n")

    report.write("## Descriptive Results for Questionnaire Variables\n\n")

    for col in df.columns:
        if col in excluded_columns or col == consent_column:
            continue

        series = df[col].dropna().astype(str).str.strip()
        series = series[series.ne("")]

        if series.empty or series.nunique() > 30:
            continue

        table = frequency_table(df[col], col)

        report.write(f"### {col}\n\n")
        report.write(
            table[["response", "count", "percent"]]
            .to_markdown(index=False)
        )
        report.write("\n\n")

    if b3_column and (TABLE_DIR / "chapter4_platform_use.csv").exists():
        platform_results = pd.read_csv(
            TABLE_DIR / "chapter4_platform_use.csv"
        )

        report.write("## Social Media Platform Use (Multiple Responses)\n\n")
        report.write(
            platform_results[
                ["platform", "selection_count", "percent_of_respondents"]
            ].to_markdown(index=False)
        )
        report.write("\n\n")

    report.write("## Missing Data\n\n")
    report.write(
        missing_summary.to_markdown(index=False)
    )
    report.write("\n\n")

    report.write(
        "**Interpretation note:** These are descriptive results. "
        "They do not by themselves establish causation or population "
        "representativeness. Verify eligibility, duplicate submissions, "
        "variable coding, and multiple-response separators before "
        "finalising the dissertation.\n"
    )

print("\n" + "=" * 65)
print("CHAPTER 4 ANALYSIS COMPLETED")
print("=" * 65)
print(f"Profile table: {TABLE_DIR / 'chapter4_respondent_profile.csv'}")
print(f"All frequencies: {TABLE_DIR / 'chapter4_all_descriptive_frequencies.csv'}")
print(f"Missing data: {TABLE_DIR / 'chapter4_missing_data_summary.csv'}")
print(f"Markdown report: {report_path}")
print(f"Figures folder: {FIGURE_DIR}")
