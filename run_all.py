"""Run steps 1-4 in one go:  python run_all.py   (add --demo only for synthetic test data)"""
import subprocess, sys

demo = ["--demo"] if "--demo" in sys.argv else []
for script, extra in [("step1_merge.py", []), ("step2_analysis.py", []), ("step3_charts.py", []), ("step4_report.py", demo)]:
    print(f"\n>>> {script}")
    if subprocess.call([sys.executable, script, *extra]) != 0:
        sys.exit(f"Stopped: {script} failed")
print("\nAll done. PDFs are in reports/. Dashboard: streamlit run app/app.py")
