"""
TESTING ONLY - builds a synthetic workbook so you can try the pipeline before
using the real file. Never use its numbers in your submission.
Run:  python tools/make_sample_data.py   (writes data/raw/SAMPLE_EduPro.xlsx)
Then copy/rename it to EduPro_Online_Platform.xlsx to test.
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(7)
out = Path(__file__).resolve().parents[1] / "data" / "raw" / "SAMPLE_EduPro.xlsx"

n_users = 3000
age = np.clip(rng.normal(29, 9, n_users).round(), 15, 62).astype(int)
gender = rng.choice(["Male", "Female", "Other"], n_users, p=[0.52, 0.45, 0.03])
users = pd.DataFrame({"UserID": [f"U{i:04d}" for i in range(1, n_users + 1)],
                      "UserName": [f"Learner {i}" for i in range(1, n_users + 1)],
                      "Age": age, "Gender": gender})

cats = {"Programming": 14, "Data Science": 12, "Business": 10, "Design": 8, "Marketing": 8,
        "Languages": 6, "Personal Development": 6}
rows, cid = [], 1
for cat, n in cats.items():
    for _ in range(n):
        rows.append({"CourseID": f"C{cid:03d}", "CourseName": f"{cat} Course {cid}",
                     "CourseCategory": cat, "CourseType": rng.choice(["Paid", "Free"], p=[0.7, 0.3]),
                     "CourseLevel": rng.choice(["Beginner", "Intermediate", "Advanced"], p=[0.45, 0.35, 0.2])})
        cid += 1
courses = pd.DataFrame(rows)

pref = {"Programming": [0.8, 1.9, 1.3, 0.8, 0.4], "Data Science": [0.6, 1.4, 1.5, 1.0, 0.6],
        "Business": [0.3, 0.8, 1.3, 1.5, 1.3], "Design": [1.2, 1.2, 0.9, 0.7, 0.6],
        "Marketing": [0.5, 1.0, 1.2, 1.2, 1.0], "Languages": [1.0, 0.9, 0.9, 1.0, 1.4],
        "Personal Development": [0.7, 0.8, 1.0, 1.3, 1.6]}
groups = pd.cut(users["Age"], [0, 17, 25, 35, 45, 200], labels=range(5)).astype(int)
tx = []
tid = 1
dates = pd.date_range("2023-01-01", "2025-06-30")
for _, u in users.iterrows():
    g = groups[_]
    k = rng.choice([0, 1, 2, 3, 4, 5, 6, 8], p=[0.08, 0.28, 0.24, 0.16, 0.1, 0.07, 0.04, 0.03])
    w = np.array([pref[c][g] * (1.15 if (u.Gender == "Female" and c in ("Design", "Marketing", "Languages")) else 1.0)
                  for c in courses.CourseCategory])
    if k:
        picks = rng.choice(len(courses), size=min(k, len(courses)), replace=False, p=w / w.sum())
        for p in picks:
            tx.append({"TransactionID": f"T{tid:06d}", "UserID": u.UserID, "CourseID": courses.CourseID[p],
                       "TransactionDate": rng.choice(dates)})
            tid += 1
tx = pd.DataFrame(tx)
with pd.ExcelWriter(out) as xw:
    users.to_excel(xw, sheet_name="Users", index=False)
    courses.to_excel(xw, sheet_name="Courses", index=False)
    tx.to_excel(xw, sheet_name="Transactions", index=False)
print("wrote", out, len(users), len(courses), len(tx))
