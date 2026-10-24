"""Step 4 - assemble the 15-page research paper. All numbers/sentences come from the analysis dict R."""
import numpy as np
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, PageBreak, KeepInFrame, NextPageTemplate, Spacer)
import config
from src.report_helpers import *

FIG = config.FIG_DIR
DEMO = False


def fp(name):
    return FIG / name


# ------------------------------------------------------------------ narrative facts
def facts(R, quality):
    F = {}
    at, gt, ct = R["age_table"], R["gender_table"], R["category_table"]
    F["top_age"] = at["Enrollments"].idxmax()
    F["top_age_share"] = at.loc[F["top_age"], "EnrollShare%"]
    F["top_age_learners"] = at.loc[F["top_age"], "LearnerShare%"]
    ranked = at["Enrollments"].sort_values(ascending=False)
    F["second_age"] = ranked.index[1] if len(ranked) > 1 else F["top_age"]
    F["top2_age_share"] = float(ranked.iloc[:2].sum() / ranked.sum() * 100)
    F["small_age"] = ranked.index[-1]
    F["small_age_share"] = float(ranked.iloc[-1] / ranked.sum() * 100)
    F["intense_age"] = at["EnrollPerLearner"].idxmax()
    F["intense_val"] = at["EnrollPerLearner"].max()
    F["light_age"] = at["EnrollPerLearner"].idxmin()
    F["light_val"] = at["EnrollPerLearner"].min()
    F["g1"], F["g2"] = (R["gender_pair"] + [None, None])[:2]
    F["g1_share"] = gt.loc[F["g1"], "LearnerShare%"]
    F["g2_share"] = gt.loc[F["g2"], "LearnerShare%"] if F["g2"] else float("nan")
    F["cat_top"], F["cat_bot"] = ct["Enrollments"].idxmax(), ct["Enrollments"].idxmin()
    F["cat_top_share"], F["cat_bot_share"] = ct["Share%"].max(), ct["Share%"].min()
    F["cat_top3_share"] = float(ct["Share%"].sort_values(ascending=False).iloc[:3].sum())
    F["cat_top3"] = ", ".join(ct["Enrollments"].sort_values(ascending=False).index[:3])
    F["cat_ratio"] = ct["Enrollments"].max() / max(1, ct["Enrollments"].min())
    F["cat_per_course_top"] = ct["EnrollPerCourse"].idxmax()
    F["cat_per_course_val"] = ct["EnrollPerCourse"].max()
    F["cat_most_courses"] = ct["Courses"].idxmax()
    F["type_top"] = R["type_table"]["Enrollments"].idxmax()
    F["type_top_share"] = R["type_table"]["Share%"].max()
    lv = R["level_table"]
    F["lvl_top"], F["lvl_top_share"] = lv["Enrollments"].idxmax(), lv["Share%"].max()
    F["lvl_low"], F["lvl_low_share"] = lv["Enrollments"].idxmin(), lv["Share%"].min()
    # age x category extremes
    lift = R["age_x_category_lift"]
    s = lift.stack()
    F["lift_max_age"], F["lift_max_cat"] = s.idxmax(); F["lift_max"] = s.max()
    F["lift_min_age"], F["lift_min_cat"] = s.idxmin(); F["lift_min"] = s.min()
    # gender gap in category
    if F["g2"]:
        diff = (R["gender_x_category_pct"].loc[F["g1"]] - R["gender_x_category_pct"].loc[F["g2"]])
        F["gap_cat_g1"] = diff.idxmax(); F["gap_g1"] = diff.max()
        F["gap_cat_g2"] = diff.idxmin(); F["gap_g2"] = -diff.min()
        ldiff = (R["gender_x_level_pct"].loc[F["g1"]] - R["gender_x_level_pct"].loc[F["g2"]])
        F["gap_lvl"] = ldiff.abs().idxmax(); F["gap_lvl_val"] = ldiff[F["gap_lvl"]]
    # age x level
    ap = R["age_x_level_pct"]
    adv = "Advanced" if "Advanced" in ap.columns else ap.columns[-1]
    beg = "Beginner" if "Beginner" in ap.columns else ap.columns[0]
    F["adv_col"], F["beg_col"] = adv, beg
    F["adv_hi_age"], F["adv_hi"] = ap[adv].idxmax(), ap[adv].max()
    F["adv_lo_age"], F["adv_lo"] = ap[adv].idxmin(), ap[adv].min()
    F["beg_hi_age"], F["beg_hi"] = ap[beg].idxmax(), ap[beg].max()
    F["beg_lo_age"], F["beg_lo"] = ap[beg].idxmin(), ap[beg].min()
    # time
    m = R["monthly"]
    F["peak_month"], F["peak_val"] = m.idxmax().strftime("%B %Y"), int(m.max())
    F["low_month"], F["low_val"] = m.idxmin().strftime("%B %Y"), int(m.min())
    F["month_avg"] = float(m.mean())
    half = len(m) // 2
    first, second = m.iloc[:half].mean(), m.iloc[half:].mean()
    F["half_change"] = float((second / first - 1) * 100) if first else float("nan")
    F["dow_top"] = R["dow"].idxmax()
    F["dow_low"] = R["dow"].idxmin()
    e = R["engagement_bands"]
    F["single_share"] = float(e.iloc[0] / e.sum() * 100)
    F["heavy_share"] = float(e.iloc[2:].sum() / e.sum() * 100)
    return F


def assoc_sentence(name, c):
    if not c:
        return ""
    return (f"A chi-square test of independence on {name} is {sig_text(c)}, with a Cram&eacute;r's V of "
            f"{c['cramers_v']:.2f}, which indicates a <b>{strength(c['cramers_v'])}</b> association.")


# ------------------------------------------------------------------ pages
def build_story(R, quality):
    F = facts(R, quality)
    K = R["kpi"]
    story = []
    at, gt, ct, lv, ty = R["age_table"], R["gender_table"], R["category_table"], R["level_table"], R["type_table"]
    d0, d1 = R["date_min"].strftime("%d %b %Y"), R["date_max"].strftime("%d %b %Y")
    sec_titles = [
        "Abstract and contents", "Introduction and objectives", "Data and methodology",
        "Data integration and quality", "Age profile of learners", "Gender participation",
        "Enrollment distribution", "Age and category preference", "Gender, level and type",
        "Age and course level", "Learner behaviour and concentration", "Skill progression and timing",
        "Learner segments and KPI scorecard", "Recommendations and conclusion"]

    def page(flow):
        story.append(KeepInFrame(FRAME_W, FRAME_H, flow, mode="shrink"))
        story.append(PageBreak())

    # cover page is drawn on canvas; first flowable just moves to the next template
    story += [NextPageTemplate("body"), PageBreak()]

    # ---- 2. abstract + contents
    f = section_head(1, "Overview", "Abstract and contents")
    f.append(P_(
        f"This paper profiles the learners of EduPro, an online learning platform, and explains how their age and gender "
        f"relate to the courses they choose. It joins the Users, Courses and Transactions sheets into one master table of "
        f"<b>{fmt_int(R['n_enrollments'])} enrollments</b> made by <b>{fmt_int(R['n_learners'])} active learners</b> across "
        f"<b>{R['n_courses']} courses</b> and <b>{R['n_categories']} categories</b>, recorded between {d0} and {d1}. "
        f"The work is descriptive: it answers who is learning and what they pick, not who will buy next."))
    f.append(P_(
        f"The largest age group is <b>{F['top_age']}</b>, which supplies {pct(F['top_age_share'])} of all enrollments. "
        f"Learners are {pct(F['g1_share'])} {F['g1']}" + (f" and {pct(F['g2_share'])} {F['g2']}" if F['g2'] else "") +
        f". <b>{F['cat_top']}</b> is the most enrolled category ({pct(F['cat_top_share'])}), and {F['lvl_top']} courses form "
        f"the biggest level group ({pct(F['lvl_top_share'])}). A learner takes {R['avg_courses']:.2f} courses on average, and the most "
        f"active 20% of learners account for {pct(R['top20_share'], 0)} of enrollments. The paper closes with evidence-based "
        f"recommendations for course design, marketing and inclusion."))
    f.append(P_("Contents", "h2"))
    rows = [["Page", "Section"], ["2", "Abstract and contents"]]
    for i, t in enumerate(sec_titles[1:], start=3):
        rows.append([str(i), t])
    rows.append(["", "Pages are fixed, so the table of contents is exact. Figures 1 to 15 follow the same order as the sections."])
    f.append(table(rows, [45, FRAME_W - 45]))
    f.append(Spacer(1, 8))
    f.append(callout("How to read this paper",
                     "Percentages are shares of enrollments unless stated. A <i>preference index</i> compares a group's share of a "
                     "category with the platform-wide share: 100 means the same as everyone, 150 means 50% more than average."))
    page(f)

    # ---- 3. introduction
    f = section_head(2, "Context", "Introduction and objectives")
    f.append(P_("Online learning platforms serve people of different ages, genders, goals and subject interests. For a platform such as "
                "EduPro, knowing who the learners are is the base for designing relevant courses, improving engagement, targeting "
                "outreach and making the platform inclusive and accessible. EduPro holds user and transaction data, but until now "
                "decisions on course creation and marketing have rested on intuition rather than evidence."))
    f.append(P_("Problem statement", "h2"))
    f += bullets([
        "Which age groups are most active on the platform?",
        "How do enrollment patterns differ by gender?",
        "What course categories do different learner segments prefer?",
        "Are beginner, intermediate or advanced courses more popular within particular age groups?"])
    f.append(P_("Objectives", "h2"))
    f += bullets([
        "Integrate the three data sheets with verified referential integrity.",
        "Measure the age and gender profile of active learners and their participation level.",
        "Describe enrollment by category, type and level, and name the most and least popular.",
        "Cross demographics with preferences (age by category, gender by level, age by level) to find learner segments.",
        "Quantify behaviour: courses per learner, concentration among active users, beginner versus advanced patterns.",
        "Turn the findings into practical recommendations for course creation, marketing and inclusion."])
    f.append(P_("Scope and boundaries", "h2"))
    f.append(P_("The project is <b>descriptive learner intelligence</b>. It does not predict future enrollments, model price or revenue, or "
                "claim that age or gender <i>causes</i> a choice. Differences are reported as associations, with a significance test and "
                "an effect size so the reader can judge how large a difference really is."))
    f.append(P_("Where each question is answered", "h2"))
    f.append(table([
        ["Key analytical question", "Section", "Figures"],
        ["What is the age distribution of learners?", "5 Age profile", "1, 2"],
        ["How does enrollment vary across age groups?", "5 and 8", "2, 7"],
        ["Are there gender-based differences in course selection?", "6 and 9", "3, 4, 8, 9"],
        ["Which course categories attract the most enrollments?", "7 Enrollment distribution", "5, 6"],
        ["Do beginners prefer certain course types or levels?", "10 and 12", "10, 14"]],
        [260, 150, FRAME_W - 410]))
    f.append(Spacer(1, 7))
    f.append(callout("Why descriptive analytics first",
                     "A clear picture of the present learner base is the foundation any later forecasting or personalisation depends on. "
                     "If the baseline is wrong, a model built on top of it will be wrong in a more confident way."))
    page(f)

    # ---- 4. data & methodology
    f = section_head(3, "Method", "Data and methodology")
    f.append(P_("The source is a single Excel workbook, <i>EduPro_Online_Platform.xlsx</i>, holding three linked sheets."))
    f.append(table([
        ["Sheet", "Fields used", "Role"],
        ["Users", "UserID, UserName, Age, Gender", "Who the learner is"],
        ["Courses", "CourseID, CourseName, CourseCategory, CourseType, CourseLevel", "What was offered"],
        ["Transactions", "TransactionID, UserID, CourseID, TransactionDate", "Links learner to course; one row = one enrollment"]],
        [70, 250, FRAME_W - 320]))
    f.append(Spacer(1, 6))
    f.append(P_("Analytical pipeline", "h2"))
    f.append(table([
        ["Stage", "What was done", "Output"],
        ["1. Integration", "Cleaned text, removed duplicate IDs, validated ages, joined Users-Transactions-Courses on UserID and CourseID", "Master table, one row per enrollment"],
        ["2. Demographics", f"Age bands {', '.join(config.AGE_LABELS)}; gender distribution; participation per group", "Age and gender tables"],
        ["3. Distribution", "Enrollment counts by category, type and level; Category Popularity Index", "Rankings, shares"],
        ["4. Cross-analysis", "Age by category heatmap; gender by level; age by level; chi-square test and Cram&eacute;r's V", "Cross-tabs, preference index"],
        ["5. Behaviour", "Courses per learner, Lorenz-style concentration curve, Gini coefficient, level segments", "Engagement metrics"],
        ["6. Delivery", "Five KPIs, Streamlit dashboard, this paper, executive summary", "Deliverables"]],
        [75, 280, FRAME_W - 355]))
    f.append(Spacer(1, 6))
    f.append(P_("Definitions", "h2"))
    f += bullets([
        "<b>Active learner</b>: a user with at least one enrollment in the merged data.",
        "<b>Enrollment</b>: one transaction row linking a learner to a course.",
        "<b>Category Popularity Index</b>: a category's enrollments divided by the average per category, times 100.",
        "<b>Preference index</b>: a group's share of a category divided by the platform share, times 100.",
        "<b>Gini coefficient</b>: 0 means every learner takes the same number of courses, 1 means one learner takes everything.",
        "<b>Cram&eacute;r's V</b>: effect size for a cross-tab, 0 (no link) to 1 (perfect link)."])
    f.append(callout("Age bands",
                     "The project brief lists 36-45 and 45+, which overlap at 45. This paper uses <b>&lt;18, 18-25, 26-35, 36-45 and 46+</b> so that every learner falls in exactly one band."))
    page(f)

    # ---- 5. data integration
    q = quality
    f = section_head(4, "Data", "Data integration and quality")
    f.append(P_(f"Joining the three sheets produced <b>{fmt_int(q.get('merged_rows', R['n_enrollments']))}</b> merged enrollment rows. "
                f"Each join was validated as many-to-one, so a transaction can never be duplicated by the merge. "
                f"Referential integrity was checked in both directions before any analysis began."))
    f.append(table([
        ["Check", "Result"],
        ["Users rows read / duplicate UserIDs removed", f"{fmt_int(q.get('users_raw_rows', 0))} / {fmt_int(q.get('users_duplicate_ids', 0))}"],
        ["Users with invalid or missing age", fmt_int(q.get("users_invalid_age_rows", 0))],
        ["Users with missing gender (set to Not Specified)", fmt_int(q.get("users_missing_gender", 0))],
        ["Courses read / duplicate CourseIDs removed", f"{fmt_int(q.get('courses_raw_rows', 0))} / {fmt_int(q.get('courses_duplicate_ids', 0))}"],
        ["Transactions read / duplicate TransactionIDs removed", f"{fmt_int(q.get('transactions_raw_rows', 0))} / {fmt_int(q.get('transactions_duplicate_ids', 0))}"],
        ["Transactions with unparseable date", fmt_int(q.get("transactions_bad_dates", 0))],
        ["Transactions pointing to an unknown UserID", fmt_int(q.get("transactions_with_unknown_user", 0))],
        ["Transactions pointing to an unknown CourseID", fmt_int(q.get("transactions_with_unknown_course", 0))],
        ["Same learner enrolled in the same course more than once", fmt_int(q.get("repeat_user_course_pairs", 0))],
        ["Registered users with no enrollment (not active)", fmt_int(q.get("learners_without_enrollment", 0))],
        ["Final merged rows / unique learners / unique courses",
         f"{fmt_int(q.get('merged_rows', 0))} / {fmt_int(q.get('merged_unique_learners', 0))} / {fmt_int(q.get('merged_unique_courses', 0))}"]],
        [FRAME_W - 130, 130]))
    f.append(Spacer(1, 8))
    bad = (q.get("transactions_with_unknown_user", 0) + q.get("transactions_with_unknown_course", 0)
           + q.get("transactions_bad_dates", 0) + q.get("users_invalid_age_rows", 0))
    verdict = ("No broken keys, bad dates or invalid ages were found, so the merged table can be used as it stands."
               if bad == 0 else
               f"{fmt_int(bad)} records had a broken key, bad date or invalid age. Broken-key transactions were excluded "
               f"and invalid ages were left blank (shown as an <i>Unknown</i> age group) rather than guessed.")
    f.append(callout("Quality verdict", verdict, color=TEAL))
    f.append(P_("Cleaning rules", "h2"))
    f += bullets([
        "Text fields were trimmed and standardised (for example M and F became Male and Female).",
        "Ages outside 5 to 100 were treated as errors and left blank, never replaced by an average.",
        "A missing gender became <i>Not Specified</i>, so no learner silently disappears from totals.",
        f"Of {fmt_int(R['n_registered'])} registered users, {fmt_int(R['n_learners'])} are active learners "
        f"({pct(R['n_learners'] / R['n_registered'] * 100)}). Demographic findings describe active learners only."])
    page(f)

    # ---- 6. age
    f = section_head(5, "Demographics", "Age profile of learners")
    f.append(P_(f"Active learners range from {R['age_min']} to {R['age_max']} years. The mean age is <b>{R['age_mean']:.1f}</b>, the median "
                f"<b>{R['age_median']:.0f}</b> and the standard deviation {R['age_std']:.1f}. "
                f"The <b>{F['top_age']}</b> band is the most active, with {pct(F['top_age_learners'])} of learners and "
                f"{pct(F['top_age_share'])} of enrollments. Together, {F['top_age']} and {F['second_age']} supply "
                f"{pct(F['top2_age_share'])} of all enrollments, while the smallest band, {F['small_age']}, supplies only "
                f"{pct(F['small_age_share'])}."))
    f += figure(fp("f01_age_distribution.png"), 125, "Age distribution of active learners with age-band boundaries and the median.")
    f += figure(fp("f02_age_groups.png"), 128, "Learners and enrollments per age group (left) and average courses per learner (right).")
    rows = [["Age group", "Learners", "Share", "Enrollments", "Share", "Courses / learner"]]
    for a, r in at.iterrows():
        rows.append([a, fmt_int(r["Learners"]), pct(r["LearnerShare%"]), fmt_int(r["Enrollments"]), pct(r["EnrollShare%"]), f"{r['EnrollPerLearner']:.2f}"])
    f.append(table(rows, [70, 70, 60, 80, 60, FRAME_W - 340]))
    f.append(Spacer(1, 5))
    spread = (F["intense_val"] - F["light_val"]) / max(R["avg_courses"], 1e-9)
    tail = ("Reach is therefore driven mostly by <i>how many</i> people join in each age band rather than by how hard they study."
            if spread < .15 else
            "The gap is large enough that age bands differ in <i>how hard</i> they study as well as in how many people join.")
    f.append(P_(f"{F['intense_age']} learners take the most courses on average "
                f"({F['intense_val']:.2f}), and {F['light_age']} learners the fewest ({F['light_val']:.2f}). " + tail))
    page(f)

    # ---- 7. gender
    f = section_head(6, "Demographics", "Gender participation")
    gr = f"{F['g1']} to {F['g2']}" if F["g2"] else F["g1"]
    f.append(P_(f"{F['g1']} learners are the largest group at {pct(F['g1_share'])}" +
                (f", followed by {F['g2']} at {pct(F['g2_share'])}. The participation ratio of {gr} is <b>{R['gender_ratio']:.2f}</b>, "
                 f"meaning there are {R['gender_ratio']:.2f} {F['g1']} learners for every {F['g2']} learner. " if F["g2"] else ". ") +
                (("Enrollment share closely follows learner share in every group (right panel), so gender differences in reach come from "
                  "who joins, not from who enrolls more often once they have joined.")
                 if (gt["EnrollShare%"] - gt["LearnerShare%"]).abs().max() < 2 else
                 "Enrollment share departs noticeably from learner share for at least one group (right panel), so some groups enroll more "
                 "often than others once they have joined.")))
    f += figure(fp("f03_gender_overview.png"), 128, "Learner base by gender (left); share of learners versus share of enrollments (right).")
    f += figure(fp("f04_gender_by_age.png"), 118, "Gender mix within each age group. Bars sum to 100% per group.")
    rows = [["Gender", "Learners", "Share", "Enrollments", "Share", "Courses / learner"]]
    for g, r in gt.iterrows():
        rows.append([g, fmt_int(r["Learners"]), pct(r["LearnerShare%"]), fmt_int(r["Enrollments"]), pct(r["EnrollShare%"]), f"{r['EnrollPerLearner']:.2f}"])
    f.append(table(rows, [70, 70, 60, 80, 60, FRAME_W - 340]))
    f.append(Spacer(1, 5))
    gb = R["gender_by_age_pct"]
    if F["g2"] and F["g2"] in gb.columns:
        a_hi = gb[F["g2"]].idxmax(); a_lo = gb[F["g2"]].idxmin()
        gap_pts = gb.loc[a_hi, F["g2"]] - gb.loc[a_lo, F["g2"]]
        advice = ("Outreach aimed at closing a gender gap should therefore be targeted at the bands where the smaller group is thinnest "
                  "rather than applied evenly." if gap_pts >= 8 else
                  "The gender mix is nearly the same across age bands, so a gender-balance programme can be run platform-wide "
                  "rather than band by band.")
        f.append(callout("Inclusivity read-out",
                         f"{F['g2']} learners make up the largest share of {a_hi} learners ({pct(gb.loc[a_hi, F['g2']], 0)}) and the smallest share of "
                         f"{a_lo} learners ({pct(gb.loc[a_lo, F['g2']], 0)}), a spread of {gap_pts:.0f} percentage points. " + advice, color=CORAL))
    page(f)

    # ---- 8. enrollment distribution
    f = section_head(7, "Enrollments", "Enrollment distribution")
    f.append(P_(f"<b>{F['cat_top']}</b> is the most popular category with {pct(F['cat_top_share'])} of enrollments, and "
                f"<b>{F['cat_bot']}</b> is the least popular with {pct(F['cat_bot_share'])}, a gap of {F['cat_ratio']:.1f} times. "
                f"The top three categories ({F['cat_top3']}) hold {pct(F['cat_top3_share'])} of demand. "
                f"The category with the most courses is {F['cat_most_courses']}; the category that attracts the most enrollments "
                f"<i>per course</i> is {F['cat_per_course_top']} ({F['cat_per_course_val']:.0f}), which shows where each new course "
                f"is likely to be best used."))
    f += figure(fp("f05_category_popularity.png"), 122, "Enrollments by course category with the Category Popularity Index.")
    f += figure(fp("f06_type_level.png"), 125, "Enrollments by course type (left) and course level (right).")
    rows = [["Category", "Courses", "Enrollments", "Share", "Popularity index", "Per course"]]
    for c, r in ct.sort_values("Enrollments", ascending=False).iterrows():
        rows.append([c, fmt_int(r["Courses"]), fmt_int(r["Enrollments"]), pct(r["Share%"]), f"{r['PopularityIndex']:.0f}", f"{r['EnrollPerCourse']:.0f}"])
    f.append(table(rows, [120, 55, 75, 55, 80, FRAME_W - 385], font=7.5))
    f.append(Spacer(1, 5))
    f.append(P_(f"By type, <b>{F['type_top']}</b> courses take {pct(F['type_top_share'])} of enrollments. By level, <b>{F['lvl_top']}</b> leads with "
                f"{pct(F['lvl_top_share'])} while {F['lvl_low']} is smallest at {pct(F['lvl_low_share'])}."))
    page(f)

    # ---- 9. age x category
    f = section_head(8, "Demographics x preference", "Age and category preference")
    f.append(P_(f"The heatmap on the left shows each age group's category mix; the one on the right converts it to a preference index so that "
                f"groups of different size can be compared fairly. The strongest over-representation is <b>{F['lift_max_age']}</b> learners in "
                f"<b>{F['lift_max_cat']}</b> (index {F['lift_max']:.0f}, i.e. {F['lift_max'] - 100:.0f}% above the platform share). The strongest "
                f"under-representation is <b>{F['lift_min_age']}</b> learners in <b>{F['lift_min_cat']}</b> (index {F['lift_min']:.0f})."))
    f += figure(fp("f07_heatmap_age_category.png"), 150, "Age group by category: share of the group's enrollments (left) and preference index (right).")
    f.append(P_("What each age band leans towards", "h2"))
    rows = [["Age group", "Top category (share)", "Most distinctive (index)"]]
    for _, r in R["personas"][R["personas"]["Segment"].str.startswith("Age")].iterrows():
        rows.append([r["Segment"].replace("Age ", ""), f"{r['TopCategory']} ({pct(r['TopCategoryShare%'], 0)})", f"{r['MostDistinctive']} ({r['Lift']:.0f})"])
    f.append(table(rows, [90, 170, FRAME_W - 260]))
    f.append(Spacer(1, 5))
    f.append(P_(assoc_sentence("age group and category", R.get("chi_age_category")) +
                " The test shows whether the pattern is larger than chance; the effect size shows whether it is large enough to act on."))
    f.append(callout("Practical meaning",
                     "A category that is popular overall can still be weak in one age band. Marketing messages and course bundles should "
                     "follow the distinctive category of each band, not just the platform-wide leader.", color=AMBER))
    page(f)

    # ---- 10. gender x level/type
    f = section_head(9, "Demographics x preference", "Gender, level and type")
    if F["g2"]:
        f.append(P_(f"Between {F['g1']} and {F['g2']} learners, the widest category gap is in <b>{F['gap_cat_g1']}</b>, where {F['g1']} learners "
                    f"place {F['gap_g1']:.1f} percentage points more of their enrollments than {F['g2']} learners; in <b>{F['gap_cat_g2']}</b> "
                    f"the gap runs the other way by {F['gap_g2']:.1f} points. The widest level gap is in <b>{F['gap_lvl']}</b> courses "
                    f"({abs(F['gap_lvl_val']):.1f} points). " + assoc_sentence("gender and category", R.get("chi_gender_category"))))
    f += figure(fp("f08_gender_category.png"), 125, "Category choice by gender, as a share of each gender's enrollments.")
    f += figure(fp("f09_gender_level_type.png"), 128, "Course level (left) and course type (right) by gender.")
    rows = [["Gender", *R["gender_x_level_pct"].columns.tolist(), "Top category"]]
    for g in gt.index:
        rows.append([g, *[pct(R["gender_x_level_pct"].loc[g, c]) for c in R["gender_x_level_pct"].columns],
                     R["gender_x_category_pct"].loc[g].idxmax()])
    n_l = R["gender_x_level_pct"].shape[1]
    f.append(table(rows, [70] + [70] * n_l + [FRAME_W - 70 - 70 * n_l]))
    f.append(Spacer(1, 5))
    f.append(P_(assoc_sentence("gender and level", R.get("chi_gender_level")) +
                " Where the effect size is weak, the safest reading is that men and women (and other learners) choose courses far more alike than "
                "different, and that differences in <i>reach</i> matter more than differences in <i>taste</i>."))
    page(f)

    # ---- 11. age x level
    f = section_head(10, "Demographics x preference", "Age and course level")
    f.append(P_(f"<b>{F['beg_hi_age']}</b> learners lean most on {F['beg_col']} courses ({pct(F['beg_hi'], 0)} of their enrollments), while "
                f"<b>{F['beg_lo_age']}</b> learners lean least ({pct(F['beg_lo'], 0)}). {F['adv_col']} courses are taken most by "
                f"<b>{F['adv_hi_age']}</b> learners ({pct(F['adv_hi'], 0)}) and least by <b>{F['adv_lo_age']}</b> learners ({pct(F['adv_lo'], 0)}). "
                + assoc_sentence("age group and level", R.get("chi_age_level"))))
    f += figure(fp("f10_age_level.png"), 140, "Level mix of each age group's enrollments.")
    rows = [["Age group", *R["age_x_level_pct"].columns.tolist(), "Preferred level"]]
    for a in R["age_x_level_pct"].index:
        rows.append([a, *[pct(R["age_x_level_pct"].loc[a, c]) for c in R["age_x_level_pct"].columns], R["age_x_level_pct"].loc[a].idxmax()])
    f.append(table(rows, [70] + [75] * n_l + [FRAME_W - 70 - 75 * n_l]))
    f.append(Spacer(1, 6))
    f.append(P_("Reading the pattern", "h2"))
    f.append(P_(f"If the {F['adv_col']} share rises or falls steadily with age, it suggests that skill depth is linked to life stage and that learning "
                f"paths should be designed per band. If it stays flat, level choice is better explained by prior experience than by age, and "
                f"placement tests or self-assessment would be a better targeting tool than age."))
    f.append(P_("Course type by age group", "h2"))
    rows = [["Age group", *R["age_x_type_pct"].columns.tolist()]]
    for a in R["age_x_type_pct"].index:
        rows.append([a, *[pct(R["age_x_type_pct"].loc[a, c]) for c in R["age_x_type_pct"].columns]])
    nt = R["age_x_type_pct"].shape[1]
    f.append(table(rows, [70] + [90] * nt))
    page(f)

    # ---- 12. behaviour
    f = section_head(11, "Behaviour", "Learner behaviour and concentration")
    f.append(P_(f"A learner takes <b>{R['avg_courses']:.2f}</b> courses on average (median {R['median_courses']:.0f}, maximum {R['max_courses']}). "
                f"{pct(F['single_share'], 0)} of learners have taken only one course, and {pct(F['heavy_share'], 0)} have taken four or more. "
                f"On average a learner has explored {R['avg_categories']:.2f} categories, and {pct(R['multi_category_share'], 0)} have crossed into "
                f"more than one category."))
    f += figure(fp("f11_courses_per_learner.png"), 135, "Distribution of courses per learner (left) and engagement bands (right).")
    f += figure(fp("f12_concentration.png"), 105, "Concentration curve: how much of total enrollment the most active learners generate.")
    ab = R["age_behaviour"]; gbh = R["gender_behaviour"]
    rows = [["Group", "Avg courses", "Median", "Max"]]
    for a, r in ab.iterrows():
        rows.append([f"Age {a}", f"{r['mean']:.2f}", f"{r['median']:.0f}", f"{r['max']:.0f}"])
    for g, r in gbh.iterrows():
        rows.append([f"Gender {g}", f"{r['mean']:.2f}", f"{r['median']:.0f}", f"{r['max']:.0f}"])
    f.append(table(rows, [150, 100, 100, FRAME_W - 350]))
    f.append(Spacer(1, 5))
    gword = "fairly evenly spread" if R["gini"] < .25 else "moderately concentrated" if R["gini"] < .45 else "highly concentrated"
    f.append(P_(f"Enrollment is {gword}. The most active 10% of learners generate <b>{pct(R['top10_share'], 0)}</b> of enrollments and "
                f"the most active 20% generate <b>{pct(R['top20_share'], 0)}</b>. The Gini coefficient is <b>{R['gini']:.2f}</b>. "
                f"Retaining the most active learners protects a disproportionate share of demand, and moving single-course learners to a second "
                f"course is the clearest route to growth."))
    page(f)

    # ---- 13. progression + timing
    s = R["level_segments"].dropna(how="all")
    f = section_head(12, "Behaviour", "Skill progression and timing")
    f.append(P_("To compare beginner and advanced learners, each learner is placed in a segment by the <i>highest</i> level they have taken."))
    f += figure(fp("f14_level_segments.png"), 128, "Learner segments by highest level reached: share, average courses, average categories.")
    rows = [["Segment", "Learners", "Share", "Avg courses", "Avg categories", "Avg age"]]
    for name, r in s.iterrows():
        rows.append([name, fmt_int(r["Learners"]), pct(r["Share%"]), f"{r['AvgEnrollments']:.2f}", f"{r['AvgCategories']:.2f}", f"{r['AvgAge']:.1f}"])
    f.append(table(rows, [110, 65, 60, 75, 80, FRAME_W - 390]))
    f.append(Spacer(1, 4))
    if len(s) >= 2:
        hi_, lo_ = s["AvgEnrollments"].iloc[-1], s["AvgEnrollments"].iloc[0]
        concl = ("it still shows that advanced learners are the platform's heaviest users." if hi_ > lo_ * 1.1 else
                 "the two groups are close, so reaching an advanced course does not mark out a heavier user.")
        f.append(P_(f"Learners who have reached the top level take {hi_:.2f} courses on average, against "
                    f"{lo_:.2f} for beginner-only learners. Part of any gap is mechanical, because a learner who "
                    f"takes more courses has more chances to meet an advanced one, but " + concl))
    f += figure(fp("f13_monthly_trend.png"), 125, f"Monthly enrollments, first-time learners and a 3-month moving average, {d0} to {d1}.")
    chg = F["half_change"]
    dir_txt = "rose" if chg > 3 else "fell" if chg < -3 else "stayed broadly flat"
    f.append(P_(f"Demand peaked in <b>{F['peak_month']}</b> ({F['peak_val']} enrollments) and was lowest in {F['low_month']} ({F['low_val']}); the monthly "
                f"average is {F['month_avg']:.0f}. Comparing the second half of the period with the first, monthly enrollments {dir_txt}"
                + (f" ({chg:+.0f}%)" if dir_txt != "stayed broadly flat" else "") +
                f". {F['dow_top']} is the busiest weekday and {F['dow_low']} the quietest."))
    page(f)

    # ---- 14. personas & KPI scorecard
    f = section_head(13, "Synthesis", "Learner segments and KPI scorecard")
    f += figure(fp("f15_kpi_panel.png"), 128, "Headline indicators for the platform.")
    f.append(P_("The five required KPIs", "h2"))
    f.append(table([
        ["KPI", "Value", "Reading"],
        ["Total Enrollments", fmt_int(K["Total Enrollments"]), "Platform engagement indicator"],
        ["Enrollments by Age Group", f"Top: {K['Top Age Group']} ({K['Top Age Group Share %']}%)", "Demographic reach (full split in Section 5)"],
        ["Gender Participation Ratio", str(K["Gender Participation Ratio"]), "Inclusivity metric"],
        ["Category Popularity Index", f"{K['Top Category']} ({K['Top Category Popularity Index']:.0f})", "Course demand; 100 = average category"],
        ["Level Preference Distribution", f"{K['Top Level']} ({K['Top Level Share %']}%)", "Skill maturity of the learner base"]],
        [150, 160, FRAME_W - 310]))
    f.append(Spacer(1, 5))
    f.append(P_("Learner segments and what they prefer", "h2"))
    rows = [["Segment", "Learners", "Top category", "Most distinctive (index)", "Preferred level"]]
    for _, r in R["personas"].iterrows():
        rows.append([r["Segment"], fmt_int(r["Learners"]), f"{r['TopCategory']} ({pct(r['TopCategoryShare%'], 0)})",
                     f"{r['MostDistinctive']} ({r['Lift']:.0f})", f"{r['PreferredLevel']} ({pct(r['LevelShare%'], 0)})"])
    f.append(table(rows, [70, 52, 130, 130, FRAME_W - 382]))
    page(f)

    # ---- 15. recommendations
    f = section_head(14, "Action", "Recommendations and conclusion")
    f.append(P_("Recommendations", "h2"))
    top_p = R["personas"][R["personas"]["Segment"].str.startswith("Age")]
    big = top_p.sort_values("Learners", ascending=False).iloc[0]
    small_age = at["Learners"].idxmin()
    f += bullets([
        f"<b>1. Protect the core category.</b> {F['cat_top']} draws {pct(F['cat_top_share'])} of enrollments. Keep it fresh with new courses and "
        f"update the most-enrolled titles before adding breadth elsewhere.",
        f"<b>2. Add courses where each course works hardest.</b> {F['cat_per_course_top']} earns {F['cat_per_course_val']:.0f} enrollments per course, the "
        f"best in the catalogue. New course slots there are the lowest-risk investment.",
        f"<b>3. Rebuild or reposition {F['cat_bot']}.</b> At {pct(F['cat_bot_share'])} of enrollments it is the weakest category. Test whether the gap "
        f"is a content-quality problem or a visibility problem before retiring it.",
        f"<b>4. Market by band.</b> The {big['Segment'].replace('Age ', '')} band is the biggest ({fmt_int(big['Learners'])} learners) and leans to "
        f"{big['MostDistinctive']}. Use each band's most distinctive category in its campaigns, for example {F['lift_max_cat']} for {F['lift_max_age']} learners.",
        f"<b>5. Grow the thinnest band deliberately.</b> {small_age} learners are the smallest group. Partnerships, scholarships or "
        f"format changes aimed at this band widen reach without competing with the core.",
        (f"<b>6. Close gender gaps with targeted outreach.</b> Gender differences are mainly in reach ({F['g1']} {pct(F['g1_share'], 0)}), not in course taste "
         f"(Cram&eacute;r's V {R['chi_gender_category']['cramers_v']:.2f}). Focus on the age bands where the smaller gender is least represented (Section 6)."
         if R.get("chi_gender_category") and R["chi_gender_category"]["cramers_v"] < .15 else
         f"<b>6. Tailor categories by gender.</b> Gender differences in category choice are large enough to act on "
         f"(widest gap: {F.get('gap_cat_g1', 'n/a')}). Reflect them in recommendations and featured courses, while keeping outreach inclusive."),
        f"<b>7. Build pathways for single-course learners.</b> {pct(F['single_share'], 0)} of learners took one course. Bundles, "
        f"next-course prompts and level-to-level pathways convert them into repeat learners.",
        f"<b>8. Reward and retain the active core.</b> The top 20% of learners drive {pct(R['top20_share'], 0)} of enrollments. Loyalty offers "
        f"and early access protect that base.",
        f"<b>9. Match level mix to audience.</b> Offer more {F['adv_col']} content where that band is under-served "
        f"({F['adv_lo_age']}: {pct(F['adv_lo'], 0)}) and more {F['beg_col']} on-ramps where that share is low.",
        "<b>10. Monitor quarterly.</b> Re-run this pipeline each quarter (one command per step) and track the five KPIs over time."])
    f.append(P_("Limitations", "h2"))
    f += bullets([
        "The analysis describes active learners and enrollments only; completion, ratings and revenue are outside the data.",
        "Associations are not causes. A chi-square test shows a pattern is unlikely to be chance, not why it exists.",
        "Age is a snapshot per learner, and small age bands can give unstable percentages; counts are always shown beside shares."])
    f.append(callout("Conclusion",
                     f"EduPro's learner base is centred on the {F['top_age']} age band and tilted towards {F['g1']} learners; {F['cat_top']} leads demand "
                     f"and {F['lvl_top']} courses lead by level. The platform's most useful next moves are to target messages by age band, add courses where "
                     f"each course performs best, and turn single-course learners into repeat learners.", color=TEAL))
    page(f)
    story.pop()  # drop last PageBreak
    return story


# ------------------------------------------------------------------ page templates
def _cover(R):
    K = R["kpi"]

    def draw(c, doc):
        c.saveState()
        c.setFillColor(INK); c.rect(0, PAGE_H * .36, PAGE_W, PAGE_H * .64, stroke=0, fill=1)
        c.setFillColor(PRIMARY); c.rect(0, PAGE_H * .36, PAGE_W, 10, stroke=0, fill=1)
        c.setFillColor(AMBER); c.rect(LM, PAGE_H - 150, 70, 5, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 10)
        c.drawString(LM, PAGE_H - 125, "RESEARCH PAPER  |  DESCRIPTIVE LEARNER INTELLIGENCE")
        c.setFont("Helvetica-Bold", 34)
        for i, line in enumerate(["Learner Demographics", "and Course Enrollment", "Behaviour on EduPro"]):
            c.drawString(LM, PAGE_H - 215 - i * 42, line)
        c.setFillColor(colors.HexColor("#B9BCE6")); c.setFont("Helvetica", 13)
        c.drawString(LM, PAGE_H - 365, "Who learns, what they choose, and why it matters")
        c.setFont("Helvetica", 10.5); c.setFillColor(colors.white)
        c.drawString(LM, PAGE_H - 420, f"Prepared by {config.AUTHOR}")
        c.drawString(LM, PAGE_H - 436, f"{config.ORG}  |  {today()}")
        # KPI strip
        items = [(fmt_int(K["Total Enrollments"]), "enrollments"), (fmt_int(K["Active Learners"]), "active learners"),
                 (f"{K['Avg Courses per Learner']}", "courses per learner"), (str(K["Top Age Group"]), "top age group")]
        w = (PAGE_W - 2 * LM) / 4
        for i, (v, lab) in enumerate(items):
            x = LM + i * w
            c.setFillColor(INK); c.setFont("Helvetica-Bold", 22); c.drawString(x, PAGE_H * .36 - 70, v)
            c.setFillColor(MUTED); c.setFont("Helvetica", 9); c.drawString(x, PAGE_H * .36 - 86, lab)
            c.setFillColor(AMBER if i % 2 == 0 else TEAL); c.rect(x, PAGE_H * .36 - 54, 28, 3, stroke=0, fill=1)
        c.setFillColor(MUTED); c.setFont("Helvetica", 8.5)
        c.drawString(LM, 70, "Includes: analysis of age, gender, category, type and level  |  15 pages  |  15 figures")
        c.drawString(LM, 58, f"Project: {config.PROJECT_NAME}")
        if DEMO:
            c.setFillColor(CORAL); c.rect(0, 0, PAGE_W, 26, stroke=0, fill=1)
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(PAGE_W / 2, 9, "DEMO BUILD - SYNTHETIC TEST DATA - NOT REAL EDUPRO RESULTS")
        c.restoreState()
    return draw


def _body(c, doc):
    c.saveState()
    c.setStrokeColor(GRID); c.setLineWidth(.6)
    c.line(LM, PAGE_H - 38, PAGE_W - RM, PAGE_H - 38)
    c.setFillColor(PRIMARY); c.setFont("Helvetica-Bold", 8)
    c.drawString(LM, PAGE_H - 32, "EDUPRO LEARNER LENS")
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_W - RM, PAGE_H - 32, "Learner Demographics and Course Enrollment Behaviour")
    c.line(LM, 40, PAGE_W - RM, 40)
    c.drawString(LM, 28, f"{config.AUTHOR}  |  {config.ORG}")
    if DEMO:
        c.setFillColor(CORAL); c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(PAGE_W / 2, 28, "DEMO - SYNTHETIC DATA")
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_W - RM, 28, f"Page {doc.page}")
    c.restoreState()


def build_paper(R, quality, out=config.REPORT_PDF, demo=False):
    global DEMO
    DEMO = demo
    FigCounter.n = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                          title="Learner Demographics and Course Enrollment Behaviour on EduPro",
                          author=config.AUTHOR, subject="EduPro Learner Lens research paper")
    cover_frame = Frame(LM, BM, FRAME_W, FRAME_H, id="cover", showBoundary=0)
    body_frame = Frame(LM, BM, FRAME_W, FRAME_H, id="body", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="cover", frames=[cover_frame], onPage=_cover(R)),
                          PageTemplate(id="body", frames=[body_frame], onPage=_body)])
    doc.build(build_story(R, quality))
    return out
