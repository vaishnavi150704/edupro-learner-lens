"""
STEP 1 - Data integration.
Run:  python step1_merge.py
Reads  data/raw/EduPro_Online_Platform.xlsx
Writes data/processed/merged_data.csv, merged_data.xlsx, data_quality_report.json
"""
from src.data_loader import load_raw
from src.preprocessing import build_master, save_outputs


def main():
    users, courses, tx = load_raw()
    master, _, _, log = build_master(users, courses, tx)
    save_outputs(master, log)
    print("=== Data quality report ===")
    for k, v in log.items():
        print(f"{k:34s}: {v}")
    print("\nMerged file preview:")
    print(master.head(8).to_string(index=False))
    print("\nDone -> data/processed/merged_data.csv")


if __name__ == "__main__":
    main()
