"""
STEP 3 - Charts.
Run:  python step3_charts.py
Writes 15 PNG figures into reports/figures/
"""
import json
import config
from src.preprocessing import load_master
from src.analysis import run_analysis
from src.charts import build_all


def main():
    df = load_master()
    quality = json.load(open(config.QUALITY_JSON)) if config.QUALITY_JSON.exists() else {}
    R = run_analysis(df, quality)
    paths = build_all(R)
    for p in paths:
        print("saved", p.name)


if __name__ == "__main__":
    main()
