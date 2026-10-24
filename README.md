# EduPro Learner Lens

Learner Demographics and Course Enrollment Behaviour Analysis on EduPro (Unified Mentor project).

Descriptive analytics only: who the learners are (age, gender) and what they choose (category, type, level).

## Folder structure

```
edupro-learner-lens/
├── data/
│   ├── raw/            <- PUT EduPro_Online_Platform.xlsx HERE
│   └── processed/      merged_data.csv / .xlsx and data_quality_report.json (made by step 1)
├── src/
│   ├── data_loader.py  read the 3 sheets
│   ├── preprocessing.py clean, validate, merge
│   ├── analysis.py     every number: age, gender, category, heatmaps, behaviour, KPIs
│   ├── theme.py        "Indigo Ledger" chart style
│   ├── charts.py       15 figures
│   ├── report_helpers.py / report_pdf.py   15-page research paper
│   └── summary_pdf.py  2-page executive summary
├── app/app.py          Streamlit dashboard
├── outputs_tables/     CSV tables (check numbers in Excel)
├── reports/            figures/ + the two PDFs
├── tools/make_sample_data.py   fake data for testing ONLY
├── step1_merge.py  step2_analysis.py  step3_charts.py  step4_report.py
├── run_all.py          runs steps 1-4
├── config.py           paths, age bands, colours, author name
└── requirements.txt
```

## Setup in VS Code

1. Open the folder: File > Open Folder > `edupro-learner-lens`.
2. Terminal > New Terminal, then:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Windows)      source .venv/bin/activate   (Mac/Linux)
   pip install -r requirements.txt
   ```
3. Copy `EduPro_Online_Platform.xlsx` into `data/raw/`.
   Sheets must be named Users, Courses, Transactions with the columns in the project brief.

## Run one by one

| Step | Command | What you get |
|---|---|---|
| 1 | `python step1_merge.py` | `data/processed/merged_data.csv` + data quality report |
| 2 | `python step2_analysis.py` | KPIs printed, tables in `outputs_tables/` |
| 3 | `python step3_charts.py` | 15 PNG charts in `reports/figures/` |
| 4 | `python step4_report.py` | `reports/EduPro_Research_Paper.pdf` (15 pages) and `EduPro_Executive_Summary.pdf` |
| 5 | `streamlit run app/app.py` | Live dashboard with age, gender, category, level and date filters |

Or run steps 1-4 together: `python run_all.py`.

## Before you submit

- Delete any file named `SAMPLE_*` in `data/raw/` and make sure the PDFs have no "DEMO" banner. The banner only appears if you pass `--demo`.
- Open the PDFs and read them once. All numbers and sentences are filled in from your data, but you should check that each statement matches what you see in the charts.
- Put your own name and organisation in `config.py` (AUTHOR, ORG).
- Age bands are <18, 18-25, 26-35, 36-45, 46+ (the brief's "45+" overlaps "36-45").

## Making it your own

Change `PALETTE` and `PROJECT_NAME` in `config.py`; add sections in `src/report_pdf.py`; add dashboard tabs in `app/app.py`.
