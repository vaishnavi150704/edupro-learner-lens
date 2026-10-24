"""
STEP 2 - Analysis and KPIs.
Run:  python step2_analysis.py
Reads  data/processed/merged_data.csv
Writes CSV tables into outputs_tables/ and prints the five KPIs.
"""
import json
import config
from src.preprocessing import load_master
from src.analysis import run_analysis, save_tables


def main():
    df = load_master()
    quality = json.load(open(config.QUALITY_JSON)) if config.QUALITY_JSON.exists() else {}
    R = run_analysis(df, quality)
    save_tables(R)
    print("=== KPIs ===")
    for k, v in R["kpi"].items():
        print(f"{k:32s}: {v}")
    print("\nAge table:\n", R["age_table"].round(2))
    print("\nGender table:\n", R["gender_table"].round(2))
    print("\nCategory table:\n", R["category_table"].round(2))
    print("\nTables saved in outputs_tables/")


if __name__ == "__main__":
    main()
