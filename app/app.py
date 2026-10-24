"""
EduPro Learner Lens - live Streamlit dashboard.
Run from the project root:   streamlit run app/app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from src.preprocessing import load_master
from src.analysis import gini, lift_table

P = config.PALETTE
st.set_page_config(page_title="EduPro Learner Lens", page_icon="🎓", layout="wide")

st.markdown(f"""
<style>
.block-container {{padding-top: 1.2rem;}}
.hero {{background: linear-gradient(120deg,{P['ink']} 0%,{P['primary']} 100%); padding: 22px 28px; border-radius: 14px; color: white; margin-bottom: 14px;}}
.hero h1 {{margin: 0; font-size: 1.9rem; color: white;}}
.hero p {{margin: 4px 0 0 0; color: #C9CCF0;}}
.kpi {{background: {P['mist']}; border-left: 6px solid {P['primary']}; border-radius: 8px; padding: 12px 16px;}}
.kpi .l {{font-size: .78rem; color: {P['muted']}; text-transform: uppercase; letter-spacing: .04em;}}
.kpi .v {{font-size: 1.55rem; font-weight: 700; color: {P['ink']};}}
.kpi .s {{font-size: .78rem; color: {P['muted']};}}
</style>
""", unsafe_allow_html=True)

LEVEL_ORDER = config.LEVEL_ORDER
SEQ = [[0, "#F4F5FB"], [.5, "#6C6AC2"], [1, P["ink"]]]


@st.cache_data
def get_data():
    return load_master()


try:
    df = get_data()
except FileNotFoundError:
    st.error("merged_data.csv not found. Run `python step1_merge.py` first.")
    st.stop()

st.markdown(f"""<div class="hero"><h1>🎓 {config.PROJECT_NAME}</h1>
<p>{config.PROJECT_TAGLINE} &nbsp;|&nbsp; Learner demographics and course enrollment behaviour on EduPro</p></div>""",
            unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar filters
sb = st.sidebar
sb.header("Filters")
ages = [a for a in config.AGE_LABELS + ["Unknown"] if a in df["AgeGroup"].astype(str).unique()]
sel_age = sb.multiselect("Age group", ages, default=ages)
genders = sorted(df["Gender"].unique())
sel_gen = sb.multiselect("Gender", genders, default=genders)
cats = sorted(df["CourseCategory"].unique())
sel_cat = sb.multiselect("Course category", cats, default=cats)
lvls = [l for l in LEVEL_ORDER if l in df["CourseLevel"].unique()] + [l for l in df["CourseLevel"].unique() if l not in LEVEL_ORDER]
sel_lvl = sb.multiselect("Course level", lvls, default=lvls)
types = sorted(df["CourseType"].unique())
sel_type = sb.multiselect("Course type", types, default=types)
dmin, dmax = df["TransactionDate"].min().date(), df["TransactionDate"].max().date()
rng = sb.date_input("Enrollment dates", (dmin, dmax), min_value=dmin, max_value=dmax)
sb.caption("Every chart, KPI and table on this page follows these filters.")

f = df[df["AgeGroup"].astype(str).isin(sel_age) & df["Gender"].isin(sel_gen) & df["CourseCategory"].isin(sel_cat)
       & df["CourseLevel"].isin(sel_lvl) & df["CourseType"].isin(sel_type)]
if isinstance(rng, tuple) and len(rng) == 2:
    f = f[(f["TransactionDate"].dt.date >= rng[0]) & (f["TransactionDate"].dt.date <= rng[1])]
if f.empty:
    st.warning("No enrollments match these filters. Widen the selection in the sidebar.")
    st.stop()

# ------------------------------------------------------------------ KPIs
n_enr, n_lrn = len(f), f["UserID"].nunique()
age_enr = f["AgeGroup"].astype(str).value_counts()
cat_enr = f["CourseCategory"].value_counts()
lvl_enr = f["CourseLevel"].value_counts()
gl = f.drop_duplicates("UserID")["Gender"].value_counts()
g_ratio = (f"{gl.index[0]}:{gl.index[1]} = {gl.iloc[0] / gl.iloc[1]:.2f}" if len(gl) > 1 else f"{gl.index[0]} only")
cpi = cat_enr / cat_enr.mean() * 100


def kpi(col, label, value, sub=""):
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div><div class="s">{sub}</div></div>',
                 unsafe_allow_html=True)


c = st.columns(5)
kpi(c[0], "Total enrollments", f"{n_enr:,}", f"{n_lrn:,} learners, {n_enr / n_lrn:.2f} courses each")
kpi(c[1], "Top age group", age_enr.idxmax(), f"{age_enr.max() / n_enr * 100:.1f}% of enrollments")
kpi(c[2], "Gender participation ratio", g_ratio, "learners, largest to second")
kpi(c[3], "Top category (popularity index)", cat_enr.idxmax(), f"index {cpi.max():.0f} (100 = average)")
kpi(c[4], "Top level", lvl_enr.idxmax(), f"{lvl_enr.max() / n_enr * 100:.1f}% of enrollments")
st.write("")

GCOL = config.GENDER_COLORS
tabs = st.tabs(["Learner overview", "Age-wise enrollment", "Gender preferences", "Category popularity",
                "Heatmaps", "Behaviour", "Data"])


def layout(fig, h=380):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=50, b=10), plot_bgcolor="white",
                      font=dict(color=P["ink"]), title_font=dict(size=15))
    fig.update_xaxes(gridcolor=P["grid"]); fig.update_yaxes(gridcolor=P["grid"])
    return fig


learners = f.drop_duplicates("UserID")
with tabs[0]:
    a, b = st.columns(2)
    fig = px.histogram(learners.dropna(subset=["Age"]), x="Age", nbins=30, color_discrete_sequence=[P["primary"]],
                       title="Age distribution of learners")
    a.plotly_chart(layout(fig), width="stretch")
    g = learners["Gender"].value_counts().reset_index()
    g.columns = ["Gender", "Learners"]
    fig = px.pie(g, names="Gender", values="Learners", hole=.55, color="Gender", color_discrete_map=GCOL,
                 title="Learners by gender")
    b.plotly_chart(layout(fig), width="stretch")
    ag = learners["AgeGroup"].astype(str).value_counts().reindex(ages).dropna().reset_index()
    ag.columns = ["AgeGroup", "Learners"]
    fig = px.bar(ag, x="AgeGroup", y="Learners", text="Learners", color_discrete_sequence=[P["teal"]], title="Learners per age group")
    st.plotly_chart(layout(fig, 320), width="stretch")

with tabs[1]:
    ae = f["AgeGroup"].astype(str).value_counts().reindex(ages).dropna()
    al = learners["AgeGroup"].astype(str).value_counts().reindex(ae.index)
    t = pd.DataFrame({"Enrollments": ae, "Learners": al})
    t["Courses per learner"] = t["Enrollments"] / t["Learners"]
    a, b = st.columns([3, 2])
    fig = go.Figure()
    fig.add_bar(x=t.index, y=t["Learners"], name="Learners", marker_color=P["primary"])
    fig.add_bar(x=t.index, y=t["Enrollments"], name="Enrollments", marker_color=P["amber"])
    fig.update_layout(barmode="group", title="Reach by age group")
    a.plotly_chart(layout(fig), width="stretch")
    fig = px.line(t.reset_index(), x="AgeGroup", y="Courses per learner", markers=True, title="Courses per learner",
                  color_discrete_sequence=[P["coral"]])
    fig.update_xaxes(title="")
    b.plotly_chart(layout(fig), width="stretch")
    lv = pd.crosstab(f["AgeGroup"].astype(str), f["CourseLevel"]).reindex(ages).dropna(how="all")
    lv = lv[[l for l in lvls if l in lv.columns]]
    lvp = lv.div(lv.sum(axis=1), axis=0) * 100
    fig = px.bar(lvp, barmode="stack", color_discrete_map=config.LEVEL_COLORS, title="Level preference within each age group (%)")
    fig.update_layout(xaxis_title="Age group", yaxis_title="% of enrollments", legend_title="Level")
    st.plotly_chart(layout(fig, 340), width="stretch")

with tabs[2]:
    gc = pd.crosstab(f["Gender"], f["CourseCategory"])
    gcp = gc.div(gc.sum(axis=1), axis=0) * 100
    fig = px.bar(gcp.T, barmode="group", color_discrete_map=GCOL, title="Category choice by gender (% of each gender's enrollments)")
    fig.update_layout(xaxis_title="", yaxis_title="%", legend_title="Gender")
    st.plotly_chart(layout(fig, 400), width="stretch")
    a, b = st.columns(2)
    gl_ = pd.crosstab(f["Gender"], f["CourseLevel"])
    gl_ = gl_[[l for l in lvls if l in gl_.columns]]
    fig = px.bar(gl_.div(gl_.sum(axis=1), axis=0).mul(100), barmode="group", title="Level by gender (%)",
                 color_discrete_sequence=[config.LEVEL_COLORS.get(l, P["muted"]) for l in gl_.columns])
    fig.update_layout(xaxis_title="", yaxis_title="%", legend_title="Level")
    a.plotly_chart(layout(fig, 340), width="stretch")
    gt_ = pd.crosstab(f["Gender"], f["CourseType"])
    fig = px.bar(gt_.div(gt_.sum(axis=1), axis=0).mul(100), barmode="stack", title="Course type by gender (%)",
                 color_discrete_sequence=config.CATEGORICAL[2:])
    fig.update_layout(xaxis_title="", yaxis_title="%", legend_title="Type")
    b.plotly_chart(layout(fig, 340), width="stretch")

with tabs[3]:
    a, b = st.columns([3, 2])
    d = cat_enr.sort_values().reset_index()
    d.columns = ["Category", "Enrollments"]
    d["Popularity index"] = (d["Enrollments"] / d["Enrollments"].mean() * 100).round(0)
    fig = px.bar(d, x="Enrollments", y="Category", orientation="h", color="Popularity index",
                 color_continuous_scale=SEQ, text="Enrollments", title="Category popularity (colour = popularity index)")
    a.plotly_chart(layout(fig, 420), width="stretch")
    ty = f["CourseType"].value_counts().reset_index(); ty.columns = ["Type", "Enrollments"]
    fig = px.pie(ty, names="Type", values="Enrollments", hole=.5, color_discrete_sequence=config.CATEGORICAL, title="By course type")
    b.plotly_chart(layout(fig, 210), width="stretch")
    lv_ = lvl_enr.reindex([l for l in lvls if l in lvl_enr.index]).reset_index(); lv_.columns = ["Level", "Enrollments"]
    fig = px.bar(lv_, x="Level", y="Enrollments", color="Level", color_discrete_map=config.LEVEL_COLORS, title="By course level")
    fig.update_layout(showlegend=False)
    b.plotly_chart(layout(fig, 210), width="stretch")
    st.markdown("**Top 10 courses**")
    st.dataframe(f.groupby(["CourseName", "CourseCategory", "CourseLevel"]).size().rename("Enrollments")
                 .sort_values(ascending=False).head(10).reset_index(), width="stretch", hide_index=True)

with tabs[4]:
    ax = pd.crosstab(f["AgeGroup"].astype(str), f["CourseCategory"]).reindex(ages).dropna(how="all")
    mode = st.radio("Show", ["Share of age group (%)", "Preference index (100 = average)", "Raw enrollments"], horizontal=True)
    if mode.startswith("Share"):
        z, scale, mid = ax.div(ax.sum(axis=1), axis=0) * 100, SEQ, None
    elif mode.startswith("Preference"):
        z, scale, mid = lift_table(ax), [[0, P["coral"]], [.5, "#F4F5FB"], [1, P["primary"]]], 100
    else:
        z, scale, mid = ax, SEQ, None
    fig = px.imshow(z.round(0), text_auto=True, aspect="auto", color_continuous_scale=scale, color_continuous_midpoint=mid,
                    title=f"Age group x course category: {mode.lower()}")
    st.plotly_chart(layout(fig, 430), width="stretch")
    gx = pd.crosstab(f["Gender"], f["CourseLevel"])
    gx = gx[[l for l in lvls if l in gx.columns]]
    fig = px.imshow((gx.div(gx.sum(axis=1), axis=0) * 100).round(1), text_auto=True, aspect="auto",
                    color_continuous_scale=SEQ, title="Gender x course level (% of gender's enrollments)")
    st.plotly_chart(layout(fig, 260), width="stretch")

with tabs[5]:
    per = f.groupby("UserID").size()
    srt = np.sort(per.values)[::-1]
    top20 = srt[:max(1, int(round(len(srt) * .2)))].sum() / srt.sum() * 100
    top10 = srt[:max(1, int(round(len(srt) * .1)))].sum() / srt.sum() * 100
    c = st.columns(4)
    kpi(c[0], "Avg courses per learner", f"{per.mean():.2f}", f"median {per.median():.0f}, max {per.max()}")
    kpi(c[1], "Top 10% of learners", f"{top10:.0f}%", "share of enrollments")
    kpi(c[2], "Top 20% of learners", f"{top20:.0f}%", "share of enrollments")
    kpi(c[3], "Gini coefficient", f"{gini(per.values):.2f}", "0 = equal, 1 = concentrated")
    st.write("")
    a, b = st.columns(2)
    h = per.clip(upper=10).value_counts().sort_index().reset_index(); h.columns = ["Courses", "Learners"]
    h["Courses"] = h["Courses"].astype(str).replace({"10": "10+"})
    fig = px.bar(h, x="Courses", y="Learners", color_discrete_sequence=[P["teal"]], title="Courses taken per learner")
    a.plotly_chart(layout(fig, 340), width="stretch")
    cum = np.cumsum(srt) / srt.sum() * 100
    xx = np.arange(1, len(srt) + 1) / len(srt) * 100
    fig = go.Figure()
    fig.add_scatter(x=np.r_[0, xx], y=np.r_[0, cum], fill="tozeroy", line=dict(color=P["primary"], width=3), name="Actual",
                    fillcolor="rgba(61,59,142,.12)")
    fig.add_scatter(x=[0, 100], y=[0, 100], line=dict(color=P["muted"], dash="dash"), name="Equality")
    fig.update_layout(title="Enrollment concentration", xaxis_title="% of learners (most active first)", yaxis_title="% of enrollments")
    b.plotly_chart(layout(fig, 340), width="stretch")
    mo = f.dropna(subset=["TransactionDate"]).copy()
    mo["Month"] = mo["TransactionDate"].dt.to_period("M").dt.to_timestamp()
    m = mo.groupby("Month").size().reset_index(name="Enrollments")
    fig = px.area(m, x="Month", y="Enrollments", color_discrete_sequence=[P["primary"]], title="Monthly enrollments")
    st.plotly_chart(layout(fig, 300), width="stretch")

with tabs[6]:
    st.caption(f"{len(f):,} filtered enrollments")
    st.dataframe(f.head(1000), width="stretch", hide_index=True)
    st.download_button("Download filtered data (CSV)", f.to_csv(index=False).encode(), "edupro_filtered.csv", "text/csv")
