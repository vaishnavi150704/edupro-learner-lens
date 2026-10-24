"""Step 1b - clean, validate and merge the three tables into one master table."""
import json
import numpy as np
import pandas as pd
import config


def _tidy_text(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def clean_users(users: pd.DataFrame, log: dict) -> pd.DataFrame:
    u = users.copy()
    log["users_raw_rows"] = len(u)
    log["users_duplicate_ids"] = int(u["UserID"].duplicated().sum())
    u = u.drop_duplicates("UserID", keep="first")
    u["UserName"] = _tidy_text(u["UserName"])
    u["Gender"] = _tidy_text(u["Gender"]).str.title()
    u["Gender"] = u["Gender"].replace({"M": "Male", "F": "Female", "Woman": "Female", "Man": "Male"})
    u["Age"] = pd.to_numeric(u["Age"], errors="coerce")
    bad_age = u["Age"].isna() | (u["Age"] < 5) | (u["Age"] > 100)
    log["users_invalid_age_rows"] = int(bad_age.sum())
    u.loc[bad_age, "Age"] = np.nan
    log["users_missing_gender"] = int(u["Gender"].isna().sum())
    u["Gender"] = u["Gender"].fillna("Not Specified")
    u["AgeGroup"] = pd.cut(u["Age"], bins=config.AGE_BINS, labels=config.AGE_LABELS)
    u["AgeGroup"] = u["AgeGroup"].astype("object").where(u["Age"].notna(), "Unknown")
    return u


def clean_courses(courses: pd.DataFrame, log: dict) -> pd.DataFrame:
    c = courses.copy()
    log["courses_raw_rows"] = len(c)
    log["courses_duplicate_ids"] = int(c["CourseID"].duplicated().sum())
    c = c.drop_duplicates("CourseID", keep="first")
    for col in ["CourseName", "CourseCategory", "CourseType", "CourseLevel"]:
        c[col] = _tidy_text(c[col]).str.title().fillna("Unknown")
    return c


def clean_transactions(tx: pd.DataFrame, log: dict) -> pd.DataFrame:
    t = tx.copy()
    log["transactions_raw_rows"] = len(t)
    log["transactions_duplicate_ids"] = int(t["TransactionID"].duplicated().sum())
    t = t.drop_duplicates("TransactionID", keep="first")
    t["TransactionDate"] = pd.to_datetime(t["TransactionDate"], errors="coerce")
    log["transactions_bad_dates"] = int(t["TransactionDate"].isna().sum())
    return t


def build_master(users, courses, tx):
    """Join Users <-> Transactions <-> Courses and report referential integrity."""
    log = {}
    u = clean_users(users, log)
    c = clean_courses(courses, log)
    t = clean_transactions(tx, log)

    orphan_users = ~t["UserID"].isin(u["UserID"])
    orphan_courses = ~t["CourseID"].isin(c["CourseID"])
    log["transactions_with_unknown_user"] = int(orphan_users.sum())
    log["transactions_with_unknown_course"] = int(orphan_courses.sum())
    t = t[~orphan_users & ~orphan_courses]

    dup_pairs = t.duplicated(["UserID", "CourseID"]).sum()
    log["repeat_user_course_pairs"] = int(dup_pairs)

    m = t.merge(u, on="UserID", how="left", validate="m:1").merge(
        c, on="CourseID", how="left", validate="m:1"
    )
    m["EnrollYear"] = m["TransactionDate"].dt.year
    m["EnrollMonth"] = m["TransactionDate"].dt.to_period("M").astype("string")
    cols = [
        "TransactionID", "TransactionDate", "EnrollYear", "EnrollMonth",
        "UserID", "UserName", "Age", "AgeGroup", "Gender",
        "CourseID", "CourseName", "CourseCategory", "CourseType", "CourseLevel",
    ]
    m = m[cols].sort_values("TransactionDate").reset_index(drop=True)
    log["merged_rows"] = len(m)
    log["merged_unique_learners"] = int(m["UserID"].nunique())
    log["merged_unique_courses"] = int(m["CourseID"].nunique())
    log["learners_without_enrollment"] = int((~u["UserID"].isin(m["UserID"])).sum())
    return m, u, c, log


def save_outputs(master: pd.DataFrame, log: dict):
    config.MERGED_CSV.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(config.MERGED_CSV, index=False)
    master.to_excel(config.MERGED_XLSX, index=False)
    with open(config.QUALITY_JSON, "w") as f:
        json.dump(log, f, indent=2)


def load_master() -> pd.DataFrame:
    """Load the merged file for later steps, restoring dtypes and category order."""
    df = pd.read_csv(config.MERGED_CSV, parse_dates=["TransactionDate"])
    order = config.AGE_LABELS + ["Unknown"]
    df["AgeGroup"] = pd.Categorical(df["AgeGroup"], categories=order, ordered=True)
    return df
