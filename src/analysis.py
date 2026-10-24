"""Step 2 - every number used in charts, KPIs, dashboard and report comes from here."""
import json
import numpy as np
import pandas as pd
import config

AGE_ORDER = config.AGE_LABELS


def _ct(df, row, col):
    return pd.crosstab(df[row], df[col])


def gini(values) -> float:
    v = np.sort(np.asarray(values, dtype=float))
    if v.sum() == 0:
        return 0.0
    n = len(v)
    cum = np.cumsum(v)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def learner_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per learner with enrollment count and highest level taken."""
    lvl_rank = {l: i for i, l in enumerate(config.LEVEL_ORDER)}
    d = df.assign(_lvl=df["CourseLevel"].map(lvl_rank))
    g = d.groupby("UserID").agg(
        Age=("Age", "first"), AgeGroup=("AgeGroup", "first"), Gender=("Gender", "first"),
        Enrollments=("TransactionID", "count"), Categories=("CourseCategory", "nunique"),
        MaxLevel=("_lvl", "max"), MinLevel=("_lvl", "min"),
    ).reset_index()
    inv = {v: k for k, v in lvl_rank.items()}
    g["MaxLevelName"] = g["MaxLevel"].map(inv)
    return g


def lift_table(counts: pd.DataFrame) -> pd.DataFrame:
    """Index of preference: group share / overall share x 100 (100 = same as platform)."""
    row_share = counts.div(counts.sum(axis=1), axis=0)
    overall = counts.sum(axis=0) / counts.values.sum()
    return row_share.div(overall, axis=1) * 100


def run_analysis(df: pd.DataFrame, quality: dict | None = None) -> dict:
    R = {}
    quality = quality or {}
    L = learner_table(df)
    R["learners"] = L
    n_enr = len(df)
    n_learners = L.shape[0]
    R["n_enrollments"] = n_enr
    R["n_learners"] = n_learners
    R["n_courses"] = int(df["CourseID"].nunique())
    R["n_categories"] = int(df["CourseCategory"].nunique())
    R["n_registered"] = n_learners + int(quality.get("learners_without_enrollment", 0))
    R["date_min"], R["date_max"] = df["TransactionDate"].min(), df["TransactionDate"].max()

    # ---- age -----------------------------------------------------------------
    ages = L["Age"].dropna()
    R["age_mean"], R["age_median"] = float(ages.mean()), float(ages.median())
    R["age_min"], R["age_max"], R["age_std"] = int(ages.min()), int(ages.max()), float(ages.std())
    age_learners = L["AgeGroup"].value_counts().reindex(AGE_ORDER + ["Unknown"]).fillna(0).astype(int)
    age_enr = df["AgeGroup"].value_counts().reindex(AGE_ORDER + ["Unknown"]).fillna(0).astype(int)
    keep = [a for a in AGE_ORDER if age_learners.get(a, 0) > 0 or age_enr.get(a, 0) > 0]
    if age_learners.get("Unknown", 0) > 0:
        keep.append("Unknown")
    age_tbl = pd.DataFrame({"Learners": age_learners[keep], "Enrollments": age_enr[keep]})
    age_tbl["LearnerShare%"] = age_tbl["Learners"] / age_tbl["Learners"].sum() * 100
    age_tbl["EnrollShare%"] = age_tbl["Enrollments"] / age_tbl["Enrollments"].sum() * 100
    age_tbl["EnrollPerLearner"] = age_tbl["Enrollments"] / age_tbl["Learners"].replace(0, np.nan)
    R["age_table"] = age_tbl
    R["age_groups"] = keep

    # ---- gender --------------------------------------------------------------
    gl = L["Gender"].value_counts()
    ge = df["Gender"].value_counts()
    gtbl = pd.DataFrame({"Learners": gl, "Enrollments": ge}).fillna(0).astype(int)
    gtbl["LearnerShare%"] = gtbl["Learners"] / gtbl["Learners"].sum() * 100
    gtbl["EnrollShare%"] = gtbl["Enrollments"] / gtbl["Enrollments"].sum() * 100
    gtbl["EnrollPerLearner"] = gtbl["Enrollments"] / gtbl["Learners"]
    R["gender_table"] = gtbl.sort_values("Learners", ascending=False)
    top2 = R["gender_table"].index[:2].tolist()
    R["gender_pair"] = top2
    if len(top2) == 2:
        a, b = top2
        R["gender_ratio"] = float(gtbl.loc[a, "Learners"] / gtbl.loc[b, "Learners"])
    else:
        R["gender_ratio"] = float("nan")
    gxa = _ct(L, "AgeGroup", "Gender")
    R["gender_by_age_pct"] = gxa.reindex([a for a in keep if a in gxa.index]).pipe(
        lambda t: t.div(t.sum(axis=1), axis=0) * 100)

    # ---- enrollment distribution ---------------------------------------------
    def dist(col):
        t = df[col].value_counts().rename("Enrollments").to_frame()
        t["Share%"] = t["Enrollments"] / n_enr * 100
        return t
    R["category_table"] = dist("CourseCategory")
    ct = R["category_table"]
    ct["PopularityIndex"] = ct["Enrollments"] / ct["Enrollments"].mean() * 100
    R["type_table"] = dist("CourseType")
    lv = dist("CourseLevel")
    lv = lv.reindex([l for l in config.LEVEL_ORDER if l in lv.index] + [l for l in lv.index if l not in config.LEVEL_ORDER])
    R["level_table"] = lv
    R["top_courses"] = (df.groupby(["CourseName", "CourseCategory", "CourseLevel"]).size()
                        .rename("Enrollments").sort_values(ascending=False).head(10).reset_index())
    cpc = df.groupby("CourseCategory")["CourseID"].nunique().rename("Courses")
    ct2 = ct.join(cpc)
    ct2["EnrollPerCourse"] = ct2["Enrollments"] / ct2["Courses"]
    R["category_table"] = ct2

    # ---- demographics x preference -------------------------------------------
    d2 = df[df["AgeGroup"].isin(keep)]
    R["age_x_category"] = _ct(d2, "AgeGroup", "CourseCategory").reindex(keep)
    R["age_x_category_pct"] = R["age_x_category"].pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
    R["age_x_category_lift"] = lift_table(R["age_x_category"])
    R["age_x_level"] = _ct(d2, "AgeGroup", "CourseLevel").reindex(keep)
    lvl_cols = [l for l in config.LEVEL_ORDER if l in R["age_x_level"].columns]
    R["age_x_level"] = R["age_x_level"][lvl_cols]
    R["age_x_level_pct"] = R["age_x_level"].pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
    R["age_x_type"] = _ct(d2, "AgeGroup", "CourseType").reindex(keep)
    R["age_x_type_pct"] = R["age_x_type"].pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
    R["gender_x_category"] = _ct(df, "Gender", "CourseCategory").loc[R["gender_table"].index]
    R["gender_x_category_pct"] = R["gender_x_category"].pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
    R["gender_x_level"] = _ct(df, "Gender", "CourseLevel").loc[R["gender_table"].index][lvl_cols]
    R["gender_x_level_pct"] = R["gender_x_level"].pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
    R["gender_x_type_pct"] = _ct(df, "Gender", "CourseType").loc[R["gender_table"].index].pipe(
        lambda t: t.div(t.sum(axis=1), axis=0) * 100)

    # chi-square tests (association, not causation)
    try:
        from scipy.stats import chi2_contingency
        def chi(t):
            t = t.loc[t.sum(axis=1) > 0, t.sum(axis=0) > 0]
            c2, p, dof, _ = chi2_contingency(t)
            n = t.values.sum()
            v = float(np.sqrt(c2 / (n * (min(t.shape) - 1)))) if min(t.shape) > 1 else float("nan")
            return {"chi2": float(c2), "p": float(p), "dof": int(dof), "cramers_v": v}
        R["chi_age_category"] = chi(R["age_x_category"])
        R["chi_age_level"] = chi(R["age_x_level"])
        R["chi_gender_category"] = chi(R["gender_x_category"])
        R["chi_gender_level"] = chi(R["gender_x_level"])
    except Exception:
        pass

    # ---- behaviour -----------------------------------------------------------
    e = L["Enrollments"]
    R["avg_courses"], R["median_courses"], R["max_courses"] = float(e.mean()), float(e.median()), int(e.max())
    bins = pd.cut(e, [0, 1, 3, 5, 10_000], labels=["1 course", "2-3 courses", "4-5 courses", "6+ courses"])
    R["engagement_bands"] = bins.value_counts().reindex(["1 course", "2-3 courses", "4-5 courses", "6+ courses"]).fillna(0).astype(int)
    R["courses_per_learner_hist"] = e.value_counts().sort_index()
    srt = e.sort_values(ascending=False).values
    cum = np.cumsum(srt) / srt.sum()
    R["pareto_x"] = np.arange(1, len(srt) + 1) / len(srt) * 100
    R["pareto_y"] = cum * 100
    for pct in (10, 20):
        k = max(1, int(round(len(srt) * pct / 100)))
        R[f"top{pct}_share"] = float(srt[:k].sum() / srt.sum() * 100)
    R["gini"] = gini(e)
    R["multi_category_share"] = float((L["Categories"] > 1).mean() * 100)
    R["avg_categories"] = float(L["Categories"].mean())
    age_beh = L.groupby("AgeGroup", observed=True)["Enrollments"].agg(["mean", "median", "max"]).reindex(keep)
    R["age_behaviour"] = age_beh
    gen_beh = L.groupby("Gender")["Enrollments"].agg(["mean", "median", "max"]).loc[R["gender_table"].index]
    R["gender_behaviour"] = gen_beh

    # beginner vs advanced learner behaviour
    L2 = L.copy()
    L2["Segment"] = np.where(L2["MaxLevelName"] == "Advanced", "Reached Advanced",
                     np.where(L2["MaxLevelName"] == "Intermediate", "Up to Intermediate", "Beginner only"))
    seg_order = ["Beginner only", "Up to Intermediate", "Reached Advanced"]
    seg = L2.groupby("Segment").agg(Learners=("UserID", "count"), AvgEnrollments=("Enrollments", "mean"),
                                    AvgCategories=("Categories", "mean"), AvgAge=("Age", "mean")).reindex(seg_order)
    seg["Share%"] = seg["Learners"] / seg["Learners"].sum() * 100
    R["level_segments"] = seg
    R["learners_segmented"] = L2

    # ---- time ------------------------------------------------------------------
    m = df.dropna(subset=["TransactionDate"]).copy()
    m["Month"] = m["TransactionDate"].dt.to_period("M").dt.to_timestamp()
    R["monthly"] = m.groupby("Month").size().rename("Enrollments")
    R["monthly_new_learners"] = m.sort_values("TransactionDate").drop_duplicates("UserID").groupby("Month").size().rename("NewLearners")
    R["dow"] = m["TransactionDate"].dt.day_name().value_counts().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]).fillna(0).astype(int)
    R["yearly"] = m.groupby(m["TransactionDate"].dt.year).size()

    # ---- segment personas ------------------------------------------------------
    pers = []
    for a in keep:
        if a not in R["age_x_category"].index or R["age_x_category"].loc[a].sum() == 0:
            continue
        lift = R["age_x_category_lift"].loc[a]
        top_cat = R["age_x_category_pct"].loc[a].idxmax()
        distinct = lift.idxmax()
        lvl = R["age_x_level_pct"].loc[a].idxmax()
        pers.append({"Segment": f"Age {a}", "Learners": int(age_tbl.loc[a, "Learners"]),
                     "TopCategory": top_cat, "TopCategoryShare%": float(R["age_x_category_pct"].loc[a, top_cat]),
                     "MostDistinctive": distinct, "Lift": float(lift[distinct]),
                     "PreferredLevel": lvl, "LevelShare%": float(R["age_x_level_pct"].loc[a, lvl])})
    for g in R["gender_table"].index:
        pc = R["gender_x_category_pct"].loc[g]
        lift = lift_table(R["gender_x_category"]).loc[g]
        lvl = R["gender_x_level_pct"].loc[g].idxmax()
        pers.append({"Segment": f"Gender {g}", "Learners": int(gtbl.loc[g, "Learners"]),
                     "TopCategory": pc.idxmax(), "TopCategoryShare%": float(pc.max()),
                     "MostDistinctive": lift.idxmax(), "Lift": float(lift.max()),
                     "PreferredLevel": lvl, "LevelShare%": float(R["gender_x_level_pct"].loc[g, lvl])})
    R["personas"] = pd.DataFrame(pers)

    # ---- KPIs ------------------------------------------------------------------
    most_age = age_tbl["Enrollments"].idxmax()
    R["kpi"] = {
        "Total Enrollments": n_enr,
        "Active Learners": n_learners,
        "Avg Courses per Learner": round(R["avg_courses"], 2),
        "Top Age Group": most_age,
        "Top Age Group Share %": round(float(age_tbl.loc[most_age, "EnrollShare%"]), 1),
        "Gender Participation Ratio": (f"{R['gender_pair'][0]}:{R['gender_pair'][1]} = {R['gender_ratio']:.2f}"
                                       if len(R['gender_pair']) == 2 else "n/a"),
        "Top Category": ct2["Enrollments"].idxmax(),
        "Top Category Popularity Index": round(float(ct2["PopularityIndex"].max()), 0),
        "Top Level": lv["Enrollments"].idxmax(),
        "Top Level Share %": round(float(lv["Share%"].max()), 1),
    }
    return R


def save_tables(R: dict):
    """Write the key tables as CSV so they can be checked in Excel."""
    config.TABLES_DIR.mkdir(exist_ok=True)
    for key, val in R.items():
        if isinstance(val, (pd.DataFrame, pd.Series)) and key not in ("learners", "learners_segmented"):
            val.to_csv(config.TABLES_DIR / f"{key}.csv")
    with open(config.TABLES_DIR / "kpis.json", "w") as f:
        json.dump({k: (v.item() if hasattr(v, "item") else v) for k, v in R["kpi"].items()}, f, indent=2)
