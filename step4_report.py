"""
STEP 4 - Research paper (15 pages) and executive summary (PDF).
Run:  python step4_report.py          (real data)
      python step4_report.py --demo   (marks the PDFs as synthetic test output)
Needs step1, step2 and step3 to have run first.
"""
import json
import sys
import config
from src.preprocessing import load_master
from src.analysis import run_analysis
from src.report_pdf import build_paper


def main():
    demo = "--demo" in sys.argv
    df = load_master()
    quality = json.load(open(config.QUALITY_JSON)) if config.QUALITY_JSON.exists() else {}
    R = run_analysis(df, quality)
    out = build_paper(R, quality, demo=demo)
    print("Research paper ->", out)
    try:
        from src.summary_pdf import build_summary
        print("Executive summary ->", build_summary(R, quality, demo=demo))
    except ImportError:
        pass
    from pypdf import PdfReader
    print("Pages in paper:", len(PdfReader(str(out)).pages))


if __name__ == "__main__":
    main()
