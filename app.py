"""
app.py — ResumeLens
AI-powered resume analyzer with ATS scoring, job matching, and skill gap analysis.
"""

from pathlib import Path
import html
import streamlit as st

from utils.parser import extract_text_from_pdf, parse_sections, extract_skills_list
from utils.ats_scorer import score_resume
from utils.suggestions import generate_suggestions
from utils.job_scraper import get_all_jobs
from utils.skill_gap import analyze_skill_gap


BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
CSS_PATH = STATIC_DIR / "css" / "style.css"
HTML_DIR = STATIC_DIR / "html"


def clean_copied_code(content: str) -> str:
    content = content.strip()

    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    return content


def compact_html(content: str) -> str:
    content = clean_copied_code(content)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return "".join(lines)


def load_css(css_file: Path) -> str:
    if not css_file.exists():
        return ""

    with open(css_file, "r", encoding="utf-8") as file:
        css = file.read()

    css = clean_copied_code(css)
    return f"<style>{css}</style>"


def load_html(html_file: Path) -> str:
    if not html_file.exists():
        return ""

    with open(html_file, "r", encoding="utf-8") as file:
        template = file.read()

    return compact_html(template)


def safe_value(value) -> str:
    if value is None:
        return ""

    return html.escape(str(value), quote=True)


def render_template(template_name: str, **kwargs) -> str:
    template = load_html(HTML_DIR / template_name)

    for key, value in kwargs.items():
        template = template.replace("{" + key + "}", safe_value(value))

    return template


def render_raw_template(template_name: str, **kwargs) -> str:
    template = load_html(HTML_DIR / template_name)

    for key, value in kwargs.items():
        template = template.replace("{" + key + "}", str(value))

    return template


def render_html(markup: str) -> None:
    st.markdown(compact_html(markup), unsafe_allow_html=True)


def render_skill_pill_items(skills, pill_class: str, prefix: str) -> str:
    pill_template = load_html(HTML_DIR / "skill_pill.html")

    pills = []

    for skill in skills:
        pill_html = pill_template
        pill_html = pill_html.replace("{pill_class}", safe_value(pill_class))
        pill_html = pill_html.replace("{prefix}", safe_value(prefix))
        pill_html = pill_html.replace("{skill}", safe_value(skill))
        pills.append(pill_html)

    return "".join(pills)


def render_skill_pills(skills, pill_class: str, prefix: str) -> str:
    pills_html = render_skill_pill_items(skills, pill_class, prefix)
    wrapper_template = load_html(HTML_DIR / "skill_pills.html")
    return wrapper_template.replace("{pills_html}", pills_html)


def render_missing_skills_inline(missing_skills) -> str:
    if not missing_skills:
        return ""

    pills_html = render_skill_pill_items(missing_skills, "skill-missing", "!")
    return f'<div class="job-missing-skills"><div class="job-missing-title">Missing Skills</div><div class="missing-skills-wrapper">{pills_html}</div></div>'


def get_score_color(score: int, strong_threshold: int = 70, mid_threshold: int = 50) -> str:
    if score >= strong_threshold:
        return "#28a745"

    if score >= mid_threshold:
        return "#ffc107"

    return "#dc3545"


def get_job_badge_color(score: int) -> str:
    if score >= 70:
        return "#28a745"

    if score >= 40:
        return "#ffc107"

    return "#888888"


st.set_page_config(
    page_title="ResumeLens",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(load_css(CSS_PATH), unsafe_allow_html=True)


render_html(
    """
    <div class="app-hero">
        <div class="app-title-wrap">
            <div class="app-icon">📄</div>
            <div>
                <h1 class="app-title">AI Resume Analyser</h1>
                <p class="app-subtitle">Upload your resume. Get your ATS score, improvement suggestions, matching jobs, and a skill gap report.</p>
            </div>
        </div>
    </div>
    """
)

st.markdown("---")


col_upload, col_role = st.columns([1, 1])

with col_upload:
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

with col_role:
    target_role = st.text_input(
        "Target Role",
        placeholder="e.g. Backend Developer, Data Scientist",
        help="Used for skill gap analysis and job search"
    )

    job_location = st.text_input(
        "Job Location",
        value="remote",
        placeholder="e.g. remote, Lahore, London"
    )


analyze_btn = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)


if analyze_btn:
    if not uploaded_file:
        st.error("Please upload a PDF resume.")
        st.stop()

    if not target_role.strip():
        st.error("Please enter a target role.")
        st.stop()

    with st.spinner("Extracting resume text..."):
        raw_text = extract_text_from_pdf(uploaded_file)

    if not isinstance(raw_text, str) or not raw_text.strip():
        st.error("Could not extract readable text from this PDF.")
        st.stop()

    if raw_text.startswith("ERROR"):
        st.error(raw_text)
        st.stop()

    with st.spinner("Analyzing resume..."):
        sections = parse_sections(raw_text) or {}
        skills_list = extract_skills_list(sections.get("skills", "")) or []
        ats_result = score_resume(sections, raw_text) or {}
        suggestions = generate_suggestions(ats_result, raw_text) or {}
        skill_gap = analyze_skill_gap(skills_list, target_role) or {}

    with st.spinner("Fetching matching jobs. This may take 10–15 seconds..."):
        try:
            jobs = get_all_jobs(target_role, skills_list, location=job_location) or []
        except Exception as error:
            jobs = []
            st.warning(f"Job search failed: {error}")

    st.success("Analysis complete.")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 ATS Score",
            "💡 Suggestions",
            "💼 Job Matches",
            "🎯 Skill Gap"
        ]
    )

    with tab1:
        st.markdown(
            '<div class="section-header">ATS Analysis</div>',
            unsafe_allow_html=True
        )

        overall = int(ats_result.get("overall_score", 0))
        grade = ats_result.get("grade", "N/A")
        missing = ats_result.get("missing_sections", [])
        section_scores = ats_result.get("section_scores", {})

        ring_col, details_col = st.columns([1, 2])

        with ring_col:
            ring_color = get_score_color(overall)

            ring_html = render_raw_template(
                "score_ring.html",
                color=ring_color,
                overall=overall,
                grade=safe_value(grade)
            )

            st.markdown(ring_html, unsafe_allow_html=True)

        with details_col:
            st.markdown("### Section Breakdown")

            if section_scores:
                for section, data in section_scores.items():
                    score = int(data.get("score", 0))
                    bar_color = get_score_color(score, strong_threshold=70, mid_threshold=40)

                    row_html = render_raw_template(
                        "section_row.html",
                        section_title=safe_value(str(section).title()),
                        score=score,
                        bar_color=bar_color
                    )

                    st.markdown(row_html, unsafe_allow_html=True)
            else:
                st.info("No section scores were generated.")

        st.markdown("---")

        contact = ats_result.get("contact_info", {})

        if contact:
            st.markdown("### Contact Info Detected")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Email", "✅" if contact.get("email") else "❌")
            c2.metric("Phone", "✅" if contact.get("phone") else "❌")
            c3.metric("LinkedIn", "✅" if contact.get("linkedin") else "❌")
            c4.metric("GitHub", "✅" if contact.get("github") else "❌")

        if missing:
            st.markdown("---")
            st.warning(f"**Missing Sections:** {', '.join(map(str, missing))}")

        st.markdown("---")
        st.markdown("### Detailed Checks")

        if section_scores:
            for section, data in section_scores.items():
                section_score = int(data.get("score", 0))
                passed_checks = data.get("passed_checks", []) or []
                issues = data.get("issues", []) or []

                with st.expander(f"{str(section).title()} — {section_score}%"):
                    if passed_checks:
                        for passed in passed_checks:
                            st.markdown(f"✅ {passed}")

                    if issues:
                        for issue in issues:
                            st.markdown(f"❌ {issue}")

                    if not issues and not passed_checks:
                        st.markdown("No issues detected.")
        else:
            st.info("No detailed checks available.")

    with tab2:
        st.markdown(
            '<div class="section-header">Improvement Suggestions</div>',
            unsafe_allow_html=True
        )

        section_suggestions = suggestions.get("section_suggestions", {}) or {}
        general_tips = suggestions.get("general_tips", []) or []

        has_suggestions = False

        for section, data in section_suggestions.items():
            advice = data.get("advice", []) or []
            rewrite = data.get("rewrite_example")

            if not advice and not rewrite:
                continue

            has_suggestions = True
            section_score = section_scores.get(section, {}).get("score", 0)

            st.markdown(f"#### {str(section).title()} *(score: {section_score}%)*")

            for tip in advice:
                suggestion_html = render_template(
                    "suggestion_block.html",
                    tip=tip
                )

                st.markdown(suggestion_html, unsafe_allow_html=True)

            if rewrite:
                st.markdown("**Example Rewrite:**")

                rewrite_html = render_template(
                    "rewrite.html",
                    weak=rewrite.get("weak", ""),
                    strong=rewrite.get("strong", "")
                )

                st.markdown(rewrite_html, unsafe_allow_html=True)

            st.markdown("")

        if not has_suggestions:
            st.success("Your resume looks strong. No major issues found.")

        if general_tips:
            st.markdown("---")
            st.markdown("### General ATS Tips")

            for tip in general_tips:
                suggestion_html = render_template(
                    "suggestion_block.html",
                    tip=tip
                )

                st.markdown(suggestion_html, unsafe_allow_html=True)

    with tab3:
        st.markdown(
            '<div class="section-header">Matching Jobs</div>',
            unsafe_allow_html=True
        )

        if not jobs:
            st.warning(
                "No jobs found. Indeed may be blocking the scraper, or RemoteOK returned no results for this role. Try a broader role name."
            )
        else:
            st.markdown(f"Found **{len(jobs)}** jobs matching **{target_role}**")

            indeed_count = sum(1 for job in jobs if job.get("source") == "Indeed")
            remoteok_count = sum(1 for job in jobs if job.get("source") == "RemoteOK")

            st.caption(f"Indeed: {indeed_count} | RemoteOK: {remoteok_count}")
            st.markdown("---")

            for job in jobs:
                score = int(job.get("match_score", 0))
                badge_color = get_job_badge_color(score)

                source = job.get("source", "Unknown")
                source_badge = "🟦 RemoteOK" if source == "RemoteOK" else "🟥 Indeed" if source == "Indeed" else safe_value(source)

                missing_skills = job.get("missing_skills", []) or []
                missing_skills_html = render_missing_skills_inline(missing_skills)

                job_html = render_raw_template(
                    "job_card.html",
                    title=safe_value(job.get("title", "Untitled Role")),
                    company=safe_value(job.get("company", "Unknown Company")),
                    location=safe_value(job.get("location", "Not specified")),
                    source_badge=source_badge,
                    badge_color=badge_color,
                    score=score,
                    missing_skills_html=missing_skills_html
                )

                st.markdown(job_html, unsafe_allow_html=True)

                job_url = job.get("url")

                if job_url:
                    st.markdown(f"[View Job ↗]({job_url})")

                st.markdown("")

    with tab4:
        st.markdown(
            '<div class="section-header">Skill Gap Analysis</div>',
            unsafe_allow_html=True
        )

        coverage = int(skill_gap.get("coverage_pct", 0))
        matched = skill_gap.get("matched_skills", []) or []
        missing_skills = skill_gap.get("missing_skills", []) or []
        priority = skill_gap.get("priority_skills", []) or []
        roadmap = skill_gap.get("learning_roadmap", []) or []

        col_cov, col_matched, col_missing = st.columns(3)

        col_cov.metric("Role Coverage", f"{coverage}%")
        col_matched.metric("Skills You Have", len(matched))
        col_missing.metric("Skills to Learn", len(missing_skills))

        st.markdown("---")

        st.markdown(f"### Skills you already have for *{target_role}*")

        if matched:
            matched_html = render_skill_pills(matched, "skill-have", "✓")
            st.markdown(matched_html, unsafe_allow_html=True)
        else:
            st.warning("No matching skills detected. Make sure your Skills section is filled out clearly.")

        st.markdown("")

        st.markdown("### Skills to learn")

        if missing_skills:
            missing_html = render_skill_pills(missing_skills, "skill-missing", "!")
            st.markdown(missing_html, unsafe_allow_html=True)
        else:
            st.success("You have all required skills for this role.")

        if priority:
            st.markdown("---")
            st.markdown("### Focus on these first")

            for index, skill in enumerate(priority, 1):
                st.markdown(f"**{index}.** {skill}")

        if roadmap:
            st.markdown("---")
            st.markdown("### Learning Roadmap")

            for phase in roadmap:
                st.markdown(f"• {phase}")

        with st.expander("📋 Skills extracted from your resume"):
            if skills_list:
                st.write(", ".join(skills_list))
            else:
                st.warning("No skills extracted. Check that your resume has a clearly labeled Skills section.")