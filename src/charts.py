"""Step 3 - build every figure used in the research paper (PNG, 200 dpi)."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import config
from src import theme

P = config.PALETTE


def _gcol(g):
    return config.GENDER_COLORS.get(g, P["teal"])


def bar_labels(ax, fmt="{:,.0f}", horizontal=False, pad=3, size=8):
    for c in ax.containers:
        labels = [fmt.format(v) for v in c.datavalues]
        ax.bar_label(c, labels=labels, padding=pad, fontsize=size, color=P["ink"])


def fig_age_hist(R):
    L = R["learners"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ages = L["Age"].dropna()
    ax.hist(ages, bins=range(int(ages.min()), int(ages.max()) + 2), color=P["primary"], alpha=.9, edgecolor="white")
    for edge in config.AGE_BINS[1:-1]:
        ax.axvline(edge + .5, color=P["amber"], ls="--", lw=1)
    ax.axvline(R["age_median"], color=P["coral"], lw=2)
    ax.text(R["age_median"] + .4, ax.get_ylim()[1] * .92, f"median {R['age_median']:.0f}", color=P["coral"], fontsize=9, fontweight="bold")
    ax.set_xlabel("Age (years)"); ax.set_ylabel("Learners")
    ax.set_title("Age distribution of active learners", pad=16); theme.tag(ax, "dashed lines mark the age-band boundaries")
    return theme.save(fig, "f01_age_distribution")


def fig_age_groups(R):
    t = R["age_table"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))
    x = np.arange(len(t))
    axes[0].bar(x - .2, t["Learners"], .4, label="Learners", color=P["primary"])
    axes[0].bar(x + .2, t["Enrollments"], .4, label="Enrollments", color=P["amber"])
    axes[0].set_xticks(x); axes[0].set_xticklabels(t.index); axes[0].legend(fontsize=8)
    axes[0].set_title("Reach by age group"); axes[0].set_ylabel("Count")
    axes[1].plot(t.index, t["EnrollPerLearner"], marker="o", color=P["coral"], lw=2.2)
    for xi, v in zip(t.index, t["EnrollPerLearner"]):
        axes[1].annotate(f"{v:.2f}", (xi, v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    axes[1].set_title("Courses per learner"); axes[1].set_ylim(0, t["EnrollPerLearner"].max() * 1.3)
    fig.tight_layout()
    return theme.save(fig, "f02_age_groups")


def fig_gender(R):
    t = R["gender_table"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))
    cols = [_gcol(g) for g in t.index]
    w, _, at = axes[0].pie(t["Learners"], labels=t.index, colors=cols, startangle=90, autopct="%1.1f%%",
                           pctdistance=.78, wedgeprops=dict(width=.42, edgecolor="white"), textprops=dict(fontsize=9))
    for a in at: a.set_color("white"); a.set_fontsize(8); a.set_fontweight("bold")
    axes[0].text(0, 0, f"{int(t['Learners'].sum()):,}\nlearners", ha="center", va="center", fontsize=10, fontweight="bold", color=P["ink"])
    axes[0].set_title("Learner base by gender")
    x = np.arange(len(t))
    axes[1].bar(x - .2, t["LearnerShare%"], .4, color=P["primary"], label="Share of learners")
    axes[1].bar(x + .2, t["EnrollShare%"], .4, color=P["amber"], label="Share of enrollments")
    axes[1].set_xticks(x); axes[1].set_xticklabels(t.index); axes[1].set_ylabel("%"); axes[1].legend(fontsize=8)
    axes[1].set_title("Participation vs enrollment share")
    fig.tight_layout()
    return theme.save(fig, "f03_gender_overview")


def fig_gender_by_age(R):
    t = R["gender_by_age_pct"]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    bottom = np.zeros(len(t))
    for g in t.columns:
        ax.bar(t.index.astype(str), t[g], bottom=bottom, color=_gcol(g), label=g, edgecolor="white")
        for i, v in enumerate(t[g]):
            if v > 6: ax.text(i, bottom[i] + v / 2, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
        bottom += t[g].values
    ax.set_ylabel("% of learners in age group"); ax.set_ylim(0, 100)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, -.12), fontsize=8)
    ax.set_title("Gender mix inside each age group")
    return theme.save(fig, "f04_gender_by_age")


def fig_categories(R):
    t = R["category_table"].sort_values("Enrollments")
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    cols = [P["primary"] if v >= 100 else P["sky"] for v in t["PopularityIndex"]]
    ax.barh(t.index, t["Enrollments"], color=cols)
    for i, (v, pi) in enumerate(zip(t["Enrollments"], t["PopularityIndex"])):
        ax.text(v + t["Enrollments"].max() * .01, i, f"{v:,}  (index {pi:.0f})", va="center", fontsize=8)
    ax.set_xlim(0, t["Enrollments"].max() * 1.25); ax.set_xlabel("Enrollments")
    ax.set_title("Course category popularity", pad=16); theme.tag(ax, "index 100 = average category; indigo bars are above average")
    return theme.save(fig, "f05_category_popularity")


def fig_type_level(R):
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3))
    t = R["type_table"]
    axes[0].bar(t.index, t["Enrollments"], color=config.CATEGORICAL[:len(t)])
    bar_labels(axes[0]); axes[0].set_title("By course type")
    axes[0].set_ylim(0, t["Enrollments"].max() * 1.15)
    l = R["level_table"]
    axes[1].bar(l.index, l["Enrollments"], color=[config.LEVEL_COLORS.get(i, P["muted"]) for i in l.index])
    for i, (v, s) in enumerate(zip(l["Enrollments"], l["Share%"])):
        axes[1].text(i, v + l["Enrollments"].max() * .02, f"{v:,}\n{s:.1f}%", ha="center", fontsize=8)
    axes[1].set_title("By course level"); axes[1].set_ylim(0, l["Enrollments"].max() * 1.25)
    fig.tight_layout()
    return theme.save(fig, "f06_type_level")


def fig_heat_age_cat(R):
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.7), gridspec_kw={"wspace": .08})
    p = R["age_x_category_pct"]
    sns.heatmap(p, annot=True, fmt=".0f", cmap=theme.HEAT, ax=axes[0], cbar=False, linewidths=1, linecolor="white",
                annot_kws={"fontsize": 8})
    axes[0].set_title("Mix of categories (% of group)"); axes[0].set_xlabel(""); axes[0].set_ylabel("Age group")
    lift = R["age_x_category_lift"]
    sns.heatmap(lift, annot=True, fmt=".0f", cmap=theme.DIVERGE, center=100, ax=axes[1], cbar=False,
                linewidths=1, linecolor="white", annot_kws={"fontsize": 8}, yticklabels=False)
    axes[1].set_title("Preference index (100 = platform avg)"); axes[1].set_xlabel(""); axes[1].set_ylabel("")
    for ax in axes:
        ax.grid(False); ax.tick_params(axis="x", rotation=40, labelsize=8)
        for lab in ax.get_xticklabels(): lab.set_ha("right")
    return theme.save(fig, "f07_heatmap_age_category")


def fig_gender_cat(R):
    t = R["gender_x_category_pct"]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    x = np.arange(t.shape[1]); n = t.shape[0]; w = .8 / n
    for i, g in enumerate(t.index):
        ax.bar(x + (i - (n - 1) / 2) * w, t.loc[g], w, label=g, color=_gcol(g))
    ax.set_xticks(x); ax.set_xticklabels(t.columns, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("% of that gender's enrollments"); ax.legend(fontsize=8)
    ax.set_title("Category choice by gender")
    return theme.save(fig, "f08_gender_category")


def fig_gender_level(R):
    t = R["gender_x_level_pct"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={"width_ratios": [1.3, 1]})
    x = np.arange(t.shape[1]); n = t.shape[0]; w = .8 / n
    for i, g in enumerate(t.index):
        axes[0].bar(x + (i - (n - 1) / 2) * w, t.loc[g], w, label=g, color=_gcol(g))
    axes[0].set_xticks(x); axes[0].set_xticklabels(t.columns); axes[0].set_ylabel("% of enrollments")
    axes[0].legend(fontsize=8); axes[0].set_title("Level choice by gender")
    ty = R["gender_x_type_pct"]
    bottom = np.zeros(len(ty))
    for j, c in enumerate(ty.columns):
        axes[1].bar(ty.index, ty[c], bottom=bottom, label=c, color=config.CATEGORICAL[j + 2], edgecolor="white")
        bottom += ty[c].values
    axes[1].set_ylim(0, 100); axes[1].legend(fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(.5, -.1))
    axes[1].set_title("Course type by gender")
    fig.tight_layout()
    return theme.save(fig, "f09_gender_level_type")


def fig_age_level(R):
    t = R["age_x_level_pct"]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    left = np.zeros(len(t))
    for l in t.columns:
        ax.barh(t.index.astype(str), t[l], left=left, color=config.LEVEL_COLORS.get(l, P["muted"]), label=l, edgecolor="white")
        for i, v in enumerate(t[l]):
            if v > 7: ax.text(left[i] + v / 2, i, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
        left += t[l].values
    ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("% of the age group's enrollments")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, -.2), fontsize=8)
    ax.set_title("Course level preference by age group")
    return theme.save(fig, "f10_age_level")


def fig_courses_per_learner(R):
    h = R["courses_per_learner_hist"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3))
    cap = 10
    hh = h.copy(); over = hh[hh.index > cap].sum(); hh = hh[hh.index <= cap]
    if over: hh.loc[cap + 1] = over
    labels = [str(i) if i <= cap else f"{cap+1}+" for i in hh.index]
    axes[0].bar(labels, hh.values, color=P["teal"]); axes[0].set_xlabel("Courses taken"); axes[0].set_ylabel("Learners")
    axes[0].set_title("How many courses do learners take?")
    b = R["engagement_bands"]
    axes[1].bar(b.index, b.values / b.sum() * 100, color=[P["sky"], P["primary"], P["amber"], P["coral"]])
    for i, v in enumerate(b.values / b.sum() * 100): axes[1].text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=8)
    axes[1].set_ylabel("% of learners"); axes[1].tick_params(axis="x", labelsize=8)
    axes[1].set_title("Engagement bands"); axes[1].set_ylim(0, (b.values / b.sum() * 100).max() * 1.2)
    fig.tight_layout()
    return theme.save(fig, "f11_courses_per_learner")


def fig_pareto(R):
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    x, y = np.r_[0, R["pareto_x"]], np.r_[0, R["pareto_y"]]
    ax.fill_between(x, x, y, color=P["primary"], alpha=.18)
    ax.plot(x, y, color=P["primary"], lw=2.4, label="Actual")
    ax.plot([0, 100], [0, 100], color=P["muted"], ls="--", lw=1, label="Perfect equality")
    for pct, c in ((10, P["coral"]), (20, P["amber"])):
        v = R[f"top{pct}_share"]
        ax.scatter([pct], [v], color=c, zorder=5, s=45)
        ax.annotate(f"top {pct}% learners\n= {v:.0f}% of enrollments", (pct, v), textcoords="offset points",
                    xytext=(18, -34 if pct == 10 else -26), fontsize=8, color=c, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=c, lw=.8))
    ax.set_xlabel("Cumulative % of learners (most active first)"); ax.set_ylabel("Cumulative % of enrollments")
    ax.set_title(f"Enrollment concentration (Gini {R['gini']:.2f})"); ax.legend(fontsize=8, loc="lower right")
    return theme.save(fig, "f12_concentration")


def fig_monthly(R):
    m = R["monthly"]; nl = R["monthly_new_learners"].reindex(m.index).fillna(0)
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    ax.fill_between(m.index, m.values, color=P["primary"], alpha=.15)
    ax.plot(m.index, m.values, color=P["primary"], lw=2, label="Enrollments")
    ax.plot(nl.index, nl.values, color=P["amber"], lw=1.8, label="First-time learners")
    roll = m.rolling(3, min_periods=1).mean()
    ax.plot(roll.index, roll.values, color=P["coral"], lw=1.4, ls="--", label="3-month average")
    ax.set_ylim(0, m.max() * 1.3)
    ax.set_ylabel("Count per month"); ax.legend(fontsize=8, ncol=3, loc="upper left")
    ax.set_title("Monthly enrollment rhythm")
    fig.autofmt_xdate()
    return theme.save(fig, "f13_monthly_trend")


def fig_level_segments(R):
    s = R["level_segments"].dropna(how="all")
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.0))
    for ax, col, ttl, c in zip(axes, ["Share%", "AvgEnrollments", "AvgCategories"],
                               ["Share of learners (%)", "Avg courses taken", "Avg categories explored"],
                               [P["sky"], P["primary"], P["teal"]]):
        ax.bar(range(len(s)), s[col], color=c)
        ax.set_xticks(range(len(s))); ax.set_xticklabels([i.replace(" ", "\n") for i in s.index], fontsize=7)
        for i, v in enumerate(s[col]): ax.text(i, v * 1.02, f"{v:.1f}", ha="center", fontsize=8)
        ax.set_title(ttl, fontsize=9.5); ax.set_ylim(0, s[col].max() * 1.2)
    fig.tight_layout()
    return theme.save(fig, "f14_level_segments")


def fig_kpi_panel(R):
    k = R["kpi"]
    cards = [("Total Enrollments", f"{k['Total Enrollments']:,}", P["primary"]),
             ("Active Learners", f"{k['Active Learners']:,}", P["teal"]),
             ("Courses / Learner", f"{k['Avg Courses per Learner']}", P["amber"]),
             ("Top Age Group", f"{k['Top Age Group']}", P["coral"]),
             ("Top Category", f"{k['Top Category']}", P["primary"]),
             ("Top Level", f"{k['Top Level']}", P["teal"])]
    fig, axes = plt.subplots(2, 3, figsize=(7.4, 3.2))
    for ax, (name, val, c) in zip(axes.ravel(), cards):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.add_patch(plt.Rectangle((0, .05), 1, .9, color=theme.P["mist"], zorder=0))
        ax.add_patch(plt.Rectangle((0, .05), .035, .9, color=c, zorder=1))
        ax.text(.1, .66, name, fontsize=8.5, color=P["muted"])
        ax.text(.1, .27, val, fontsize=15 if len(val) < 11 else 11, fontweight="bold", color=P["ink"])
    fig.tight_layout()
    return theme.save(fig, "f15_kpi_panel")


def build_all(R):
    theme.apply()
    fns = [fig_age_hist, fig_age_groups, fig_gender, fig_gender_by_age, fig_categories, fig_type_level,
           fig_heat_age_cat, fig_gender_cat, fig_gender_level, fig_age_level, fig_courses_per_learner,
           fig_pareto, fig_monthly, fig_level_segments, fig_kpi_panel]
    return [f(R) for f in fns]
