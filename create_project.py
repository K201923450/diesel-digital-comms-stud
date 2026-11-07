"""
create_project.py
Builds the folder structure and starter files for the research project.

Two ways to run it:

  A) On your own computer - creates a NEW folder called diesel-digital-comms-study
         python create_project.py

  B) In GitHub Codespaces (you are already inside the repository) - builds the
     structure in the CURRENT folder instead of making a sub-folder
         python create_project.py --here
"""

import sys
from pathlib import Path

HERE_MODE = "--here" in sys.argv
PROJECT = "diesel-digital-comms-study"
root = Path(".") if HERE_MODE else Path(PROJECT)

if not HERE_MODE and root.exists():
    raise SystemExit(f"'{PROJECT}' already exists here. Rename or delete it first.")

# ---- 1. Folders ------------------------------------------------------
folders = [
    "data/raw",            # the original Google Forms export (never edited)
    "data/processed",      # cleaned data, if you save any
    "src",                 # analysis code
    "results/tables",      # Excel tables
    "results/figures",     # charts for Chapter 4
    "docs",                # codebook, notes, ethics clearance reference
]
for f in folders:
    (root / f).mkdir(parents=True, exist_ok=True)
    (root / f / ".gitkeep").touch()   # lets Git track otherwise-empty folders

# ---- 2. Starter files ------------------------------------------------
files = {}

files["requirements.txt"] = """pandas>=2.0
matplotlib>=3.7
openpyxl>=3.1
"""

# Raw survey data and anything with respondents' own words stays OUT of Git.
files[".gitignore"] = """# --- Participant data: do not publish without ethics approval ---
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
results/tables/G2_coding_template.xlsx

# --- Python ---
__pycache__/
*.pyc
.venv/
venv/
.ipynb_checkpoints/

# --- System / editor ---
.DS_Store
Thumbs.db
.vscode/
"""

files["README.md"] = """# Digital Communication and Public Perceptions of Diesel Emissions and Air Pollution

Descriptive analysis code for a PGDip Science Communication research project
(University of Limpopo) on how digital communication shapes public perceptions of
diesel emissions in the Capricorn District, Polokwane, South Africa.

## Design
Explanatory sequential mixed-methods study:
- **Instrument 1:** online questionnaire (n = 50), analysed descriptively in Python.
- **Instrument 2:** written responses (n = 14), analysed thematically (done by hand).

## Project structure
```
data/raw/          original questionnaire export (NOT in this repository)
data/processed/    cleaned data (NOT in this repository)
src/               analysis code
results/tables/    Excel output tables
results/figures/   charts
docs/              codebook and notes
```

## How to reproduce
1. Clone the repository and open the folder.
2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   .venv\\Scripts\\activate        # Windows
   source .venv/bin/activate      # macOS / Linux / Codespaces
   ```
3. Install the libraries: `pip install -r requirements.txt`
4. Place the questionnaire CSV in `data/raw/`
   (`Digital_Communication_and_Public_Perceptions_of_Diesel_Emissions___Air_Pollution.csv`).
5. Run: `python src/survey_analysis.py`

Outputs appear in `results/tables/` and `results/figures/`.

## Data and ethics
The raw responses are not published here. Ethical clearance is through the
Turfloop Research Ethics Committee (TREC), University of Limpopo.
Contact the author for access subject to ethics conditions.

## Author
Add name, supervisor and year here.
"""

for name, text in files.items():
    path = root / name
    # In --here mode, keep any file that already exists, except README.md,
    # which is replaced because GitHub only creates a one-line stub there.
    if HERE_MODE and path.exists() and name == ".gitignore":
        existing = path.read_text(encoding="utf-8")
        if "data/raw/*" not in existing:       # keep GitHub's rules, ADD the data protection
            path.write_text(existing.rstrip() + "\n\n" + text, encoding="utf-8")
            print("Added the participant-data rules to the existing .gitignore")
        continue
    if HERE_MODE and path.exists() and name != "README.md":
        print(f"Kept existing {name}")
        continue
    path.write_text(text, encoding="utf-8")

print(f"Project created: {root.resolve()}")
print("Next: copy survey_analysis.py into the 'src' folder and the CSV into 'data/raw'.")
