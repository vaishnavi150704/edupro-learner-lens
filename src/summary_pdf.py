"""Step 4b - two-page executive summary for non-technical (government) stakeholders."""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, PageBreak, KeepInFrame, Spacer
from reportlab.pdfgen import canvas as _c
import config
from src.report_helpers import *
from src import report_pdf
from src.report_pdf import facts

FIG = config.FIG_DIR


def _decor(demo):
    def draw(c, doc):
        c.saveState()
        c.setFillColor(INK); c.rect(0, PAGE_H - 92, PAGE_W, 92, stroke=0, fill=1)
        c.setFillColor(AMBER); c.rect(0, PAGE_H - 96, PAGE_W, 4, stroke=0, fill=1)
        if doc.page == 1:
            c.setFillColor(colors.HexColor("#B9BCE6")); c.setFont("Helvetica-Bold", 8.5)
            c.drawString(LM, PAGE_H - 30, "EXECUTIVE SUMMARY  |  FOR GOVERNMENT STAKEHOLDERS")
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 19)
            c.drawString(LM, PAGE_H - 56, "Who learns on EduPro, and what they choose")
            c.setFont("Helvetica", 9.5)
            c.drawString(LM, PAGE_H - 76, f"{config.AUTHOR}  |  {config.ORG}  |  {today()}")
        else:
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 14)
            c.drawString(LM, PAGE_H - 52, "What it means and what to do next")
            c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#B9BCE6"))
            c.drawString(LM, PAGE_H - 72, "EduPro Learner Lens  |  Executive summary, page 2 of 2")
        c.setStrokeColor(GRID); c.line(LM, 40, PAGE_W - RM, 40)
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawString(LM, 28, "Full evidence: EduPro research paper (15 pages) and live dashboard")
        if demo:
            c.setFillColor(CORAL); c.setFont("Helvetica-Bold", 8)
            c.drawRightString(PAGE_W - RM, 28, "DEMO - SYNTHETIC DATA")
        c.restoreState()
    return draw


def build_summary(R, quality, out=config.SUMMARY_PDF, demo=False):
    F = facts(R, quality)
    K = R["kpi"]
    at, gt, ct = R["age_table"], R["gender_table"], R["category_table"]
    FigCounter.n = 0
    FH = PAGE_H - 96 - 56 - 10
    story = []

    f = []
    f.append(Spacer(1, 4))
    f.append(P_(f"EduPro serves <b>{fmt_int(R['n_learners'])} active learners</b> who made <b>{fmt_int(R['n_enrollments'])} course enrollments</b> "
                f"across {R['n_courses']} courses. This summary explains, in plain terms, who those learners are, what they choose, and what the "
                f"platform should do with that knowledge. It describes the present learner base; it does not forecast or measure revenue."))
    f += figure(FIG / "f15_kpi_panel.png", 150, "Headline indicators.")
    f.append(P_("What we found", "h2"))
    f += bullets([
        f"<b>Age.</b> The <b>{F['top_age']}</b> age group is the most active, with {pct(F['top_age_share'], 0)} of all enrollments. "
        f"The smallest group, {F['small_age']}, supplies {pct(F['small_age_share'], 0)}.",
        f"<b>Gender.</b> Learners are {pct(F['g1_share'], 0)} {F['g1']}"
        + (f" and {pct(F['g2_share'], 0)} {F['g2']}" if F["g2"] else "") + ".",
        f"<b>Subjects.</b> <b>{F['cat_top']}</b> is the most popular category ({pct(F['cat_top_share'], 0)} of enrollments); "
        f"<b>{F['cat_bot']}</b> is the least ({pct(F['cat_bot_share'], 0)}).",
        f"<b>Skill level.</b> {F['lvl_top']} courses are the most chosen ({pct(F['lvl_top_share'], 0)}).",
        f"<b>Engagement.</b> A learner takes {R['avg_courses']:.1f} courses on average. The most active 20% of learners account for "
        f"{pct(R['top20_share'], 0)} of enrollments, and {pct(F['single_share'], 0)} of learners have taken just one course."])
    f += figure(FIG / "f05_category_popularity.png", 118, "Which course categories attract the most enrollments.")
    f += figure(FIG / "f02_age_groups.png", 118, "Which age groups are most active.")
    story.append(KeepInFrame(FRAME_W, FH, f, mode="shrink")); story.append(PageBreak())

    f = [Spacer(1, 4)]
    f.append(P_("Who prefers what", "h2"))
    rows = [["Learner group", "Learners", "Most chosen category", "Most distinctive choice", "Preferred level"]]
    for _, r in R["personas"].iterrows():
        rows.append([r["Segment"], fmt_int(r["Learners"]), f"{r['TopCategory']}", f"{r['MostDistinctive']}", f"{r['PreferredLevel']}"])
    f.append(table(rows, [80, 55, 120, 120, FRAME_W - 375]))
    f.append(Spacer(1, 3))
    f.append(P_("<i>Most distinctive choice</i> is the category a group picks far more often than the platform average.", "cap"))
    cg = R.get("chi_gender_category")
    similar = cg and cg["cramers_v"] < .15
    f.append(callout("What this means",
                     f"Different age groups lean towards different subjects, so one message for everyone will under-serve some of them. "
                     + ("Men and women choose subjects very similarly; the main gender difference is in <i>how many</i> of each join, "
                        "not what they study." if similar else
                        "Gender also shapes some subject choices, so featured courses should reflect it.")))
    f.append(P_("Recommended actions", "h2"))
    f += bullets([
        f"<b>Invest where demand is proven.</b> Keep {F['cat_top']} strong and add courses in {F['cat_per_course_top']}, where each course attracts the most learners.",
        f"<b>Review {F['cat_bot']}.</b> Decide whether to improve, promote or retire it.",
        f"<b>Reach every age group.</b> Tailor outreach to each group's favourite subject, and run a targeted effort for the smallest group ({F['small_age']}).",
        f"<b>Support inclusion.</b> Aim awareness efforts at the age groups where the smaller gender group is thinnest.",
        f"<b>Keep learners learning.</b> Offer clear next-course pathways to the {pct(F['single_share'], 0)} who have taken only one course.",
        "<b>Measure every quarter.</b> Track the five indicators (total enrollments, enrollments by age group, gender participation ratio, "
        "category popularity, level preference) so decisions stay evidence-based."])
    f.append(P_("About the data", "h2"))
    f.append(P_(f"The analysis joins the Users, Courses and Transactions records ({fmt_int(R['n_enrollments'])} enrollments, "
                f"{R['date_min'].strftime('%b %Y')} to {R['date_max'].strftime('%b %Y')}). Records were checked for duplicates, broken links and invalid "
                f"values before use. Findings describe associations between learner groups and choices, not causes. "
                f"Learners are grouped as &lt;18, 18-25, 26-35, 36-45 and 46+."))
    f.append(callout("Next step", "Approve a pilot that applies the age-targeted outreach and next-course pathways above, and review the five indicators "
                                  "after one quarter to see what changed.", color=TEAL))
    story.append(KeepInFrame(FRAME_W, FH, f, mode="shrink"))

    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=104, bottomMargin=52,
                          title="EduPro Executive Summary", author=config.AUTHOR)
    frame = Frame(LM, 52, FRAME_W, FH, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=_decor(demo))])
    doc.build(story)
    return out
