"""
Central settings for the EduPro Learner Lens project.
Change a value here and every step (merge, charts, report, dashboard) follows.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ---- paths -----------------------------------------------------------------
RAW_EXCEL = ROOT / "data" / "raw" / "EduPro_Online_Platform.xlsx"
MERGED_CSV = ROOT / "data" / "processed" / "merged_data.csv"
MERGED_XLSX = ROOT / "data" / "processed" / "merged_data.xlsx"
QUALITY_JSON = ROOT / "data" / "processed" / "data_quality_report.json"
TABLES_DIR = ROOT / "outputs_tables"
FIG_DIR = ROOT / "reports" / "figures"
REPORT_PDF = ROOT / "reports" / "EduPro_Research_Paper.pdf"
SUMMARY_PDF = ROOT / "reports" / "EduPro_Executive_Summary.pdf"

# ---- sheet names (matched case-insensitively) --------------------------------
SHEET_USERS = "Users"
SHEET_COURSES = "Courses"
SHEET_TX = "Transactions"

# ---- age bands -------------------------------------------------------------
# The brief lists "36-45" and "45+", which overlap at 45, so the last band
# here starts at 46.
AGE_BINS = [0, 17, 25, 35, 45, 200]
AGE_LABELS = ["<18", "18-25", "26-35", "36-45", "46+"]

# ---- project identity (used in charts, report, dashboard) -------------------
PROJECT_NAME = "EduPro Learner Lens"
PROJECT_TAGLINE = "Who learns, what they choose, and why it matters"
AUTHOR = "Vaishnavi Sarodey"
ORG = "Unified Mentor"

# ---- visual identity: "Indigo Ledger" palette --------------------------------
PALETTE = {
    "ink": "#1B1F3B",      # deep indigo, titles and text
    "primary": "#3D3B8E",  # indigo
    "teal": "#1F9E89",
    "amber": "#F2A541",
    "coral": "#E4572E",
    "sky": "#6CB4EE",
    "mist": "#EEF0F8",     # light background
    "grid": "#D7DAEA",
    "muted": "#6B7090",
}
CATEGORICAL = ["#3D3B8E", "#1F9E89", "#F2A541", "#E4572E", "#6CB4EE", "#9B5DE5", "#8D99AE", "#2A9D8F"]
GENDER_COLORS = {"Female": "#E4572E", "Male": "#3D3B8E", "Other": "#1F9E89"}
LEVEL_ORDER = ["Beginner", "Intermediate", "Advanced"]
LEVEL_COLORS = {"Beginner": "#6CB4EE", "Intermediate": "#F2A541", "Advanced": "#3D3B8E"}
