# Digital Communication and Public Perceptions of Diesel Emissions and Air Pollution

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
   .venv\Scripts\activate        # Windows
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
