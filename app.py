"""
app.py — ResumeLens
AI-powered resume analyzer with ATS scoring, job matching, and skill gap analysis.
"""

import streamlit as st

from utils.parser import extract_text_from_pdf, parse_sections, extract_skills_list
from utils.ats_scorer import score_resume
from utils.suggestions import generate_suggestions
from utils.job_scraper import get_all_jobs
from utils.skill_gap import analyze_skill_gap

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="ResumeLens",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# Styling
# ─────────────────────────────────────────────

st.markdown("""
<style>
    /* Overall page */
    .block-container { padding-top: 2rem; max-width: 1100px; }

    /* Score ring */
    .score-ring {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #1e3a5f, #0f2236);
        border-radius: 50%;
        width: 160px;
        height: 160px;
        margin: auto;
        box-shadow: 0 0 0 6px #2a5298;
        color: white;
    }
    .score-number { font-size: 3rem; font-weight: 800; line-height: 1; }
    .score-label  { font-size: 0.8rem; color: #aac4ff; letter-spacing: 0.1em; }

    /* Section score bar */
    .section-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    .section-name { width: 130px; font-size: 0.85rem; font-weight: 600; }
    .bar-bg {
        flex: 1;
        height: 10px;
        border-radius: 5px;
        background: #e0e7ef;
        overflow: hidden;
    }
    .bar-fill {
        height: 100%;
        border-radius: 5px;
        transition: width 0.4s ease;
    }
    .score-pct { width: 36px; font-size: 0.8rem; text-align: right; color: #555; }

    /* Job card */
    .job-card {
        border: 1px solid #dde3ed;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
        background: white;
    }
    .job-title { font-size: 1.05rem; font-weight: 700; color: #1e3a5f; }
    .job-meta  { font-size: 0.82rem; color: #666; margin-top: 2px; }
    .match-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 8px;
    }

    /* Skill pill */
    .skill-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 3px;
        font-weight: 500;
    }
    .skill-have    { background: #d4edda; color: #155724; }
    .skill-missing { background: #f8d7da; color: #721c24; }

    /* Suggestion card */
    .suggestion-block {
        background: #f0f4ff;
        border-left: 4px solid #2a5298;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
        color: #1a1a2e !important;
    }

    /* Rewrite example */
    .rewrite-weak   { background: #fff3cd; color: #5a4000 !important; padding: 10px; border-radius: 6px; margin-bottom: 6px; font-size: 0.85rem; }
    .rewrite-strong { background: #d4edda; color: #155724 !important; padding: 10px; border-radius: 6px; font-size: 0.85rem; }

    /* Tab header */
    .section-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e3a5f;
        border-bottom: 2px solid #2a5298;
        padding-bottom: 6px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────

st.markdown("## 📄 ResumeLens")
st.markdown("Upload your resume. Get your ATS score, improvement suggestions, matching jobs, and a skill gap report.")
st.markdown("---")


# ─────────────────────────────────────────────
# Input
# ─────────────────────────────────────────────

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
        "Job Location (for Indeed)",
        value="remote",
        placeholder="e.g. remote, New York, London"
    )

analyze_btn = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)


# ─────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────

if analyze_btn:
    if not uploaded_file:
        st.error("Please upload a PDF resume.")
        st.stop()
    if not target_role.strip():
        st.error("Please enter a target role.")
        st.stop()

    # ── Extract text ──
    with st.spinner("Extracting resume text..."):
        raw_text = extract_text_from_pdf(uploaded_file)

    if raw_text.startswith("ERROR"):
        st.error(raw_text)
        st.stop()

    with st.spinner("Analyzing resume..."):
        sections = parse_sections(raw_text)
        skills_list = extract_skills_list(sections.get("skills", ""))
        ats_result = score_resume(sections, raw_text)
        suggestions = generate_suggestions(ats_result)
        skill_gap = analyze_skill_gap(skills_list, target_role)

    with st.spinner("Fetching matching jobs (this may take 10–15 seconds)..."):
        jobs = get_all_jobs(target_role, skills_list, location=job_location)

    st.success("Analysis complete!")
    st.markdown("---")

    # ─────────────────────────────────────────────
    # TAB LAYOUT
    # ─────────────────────────────────────────────

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 ATS Score",
        "💡 Suggestions",
        "💼 Job Matches",
        "🎯 Skill Gap"
    ])

    # ────────────────────
    # TAB 1 — ATS Score
    # ────────────────────
    with tab1:
        st.markdown('<div class="section-header">ATS Analysis</div>', unsafe_allow_html=True)

        overall = ats_result["overall_score"]
        grade = ats_result["grade"]
        missing = ats_result["missing_sections"]

        # Score ring
        ring_col, details_col = st.columns([1, 2])

        with ring_col:
            color = "#28a745" if overall >= 70 else "#ffc107" if overall >= 50 else "#dc3545"
            st.markdown(f"""
            <div class="score-ring" style="box-shadow: 0 0 0 6px {color};">
                <span class="score-number" style="color:{color}">{overall}</span>
                <span class="score-label">ATS SCORE</span>
                <span style="font-size:0.9rem; margin-top:4px; color:#ccc">{grade}</span>
            </div>
            """, unsafe_allow_html=True)

        with details_col:
            st.markdown("**Section Breakdown**")
            section_scores = ats_result["section_scores"]

            for section, data in section_scores.items():
                score = data["score"]
                bar_color = "#28a745" if score >= 70 else "#ffc107" if score >= 40 else "#dc3545"
                st.markdown(f"""
                <div class="section-row">
                    <span class="section-name">{section.title()}</span>
                    <div class="bar-bg">
                        <div class="bar-fill" style="width:{score}%; background:{bar_color};"></div>
                    </div>
                    <span class="score-pct">{score}%</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Contact info found
        contact = ats_result.get("contact_info", {})
        if contact:
            st.markdown("**Contact Info Detected**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Email", "✅" if contact.get("email") else "❌")
            c2.metric("Phone", "✅" if contact.get("phone") else "❌")
            c3.metric("LinkedIn", "✅" if contact.get("linkedin") else "❌")
            c4.metric("GitHub", "✅" if contact.get("github") else "❌")

        # Missing sections
        if missing:
            st.markdown("---")
            st.warning(f"**Missing Sections:** {', '.join(missing)}")

        # Per-section issues
        st.markdown("---")
        st.markdown("**Detailed Checks**")
        for section, data in section_scores.items():
            with st.expander(f"{section.title()} — {data['score']}%"):
                if data["passed_checks"]:
                    for p in data["passed_checks"]:
                        st.markdown(f"✅ {p}")
                if data["issues"]:
                    for i in data["issues"]:
                        st.markdown(f"❌ {i}")
                if not data["issues"] and not data["passed_checks"]:
                    st.markdown("No issues detected.")


    # ────────────────────
    # TAB 2 — Suggestions
    # ────────────────────
    with tab2:
        st.markdown('<div class="section-header">Improvement Suggestions</div>', unsafe_allow_html=True)

        section_suggestions = suggestions["section_suggestions"]
        general_tips = suggestions["general_tips"]

        has_suggestions = False
        for section, data in section_suggestions.items():
            advice = data.get("advice", [])
            rewrite = data.get("rewrite_example")

            if not advice and not rewrite:
                continue

            has_suggestions = True
            score = ats_result["section_scores"][section]["score"]
            st.markdown(f"#### {section.title()} *(score: {score}%)*")

            for tip in advice:
                st.markdown(f"""
                <div class="suggestion-block">💬 {tip}</div>
                """, unsafe_allow_html=True)

            if rewrite:
                st.markdown("**Example Rewrite:**")
                st.markdown(f"""
                <div class="rewrite-weak">❌ <strong>Before:</strong> {rewrite['weak']}</div>
                <div class="rewrite-strong">✅ <strong>After:</strong> {rewrite['strong']}</div>
                """, unsafe_allow_html=True)

            st.markdown("")

        if not has_suggestions:
            st.success("Your resume looks strong! No major issues found.")

        st.markdown("---")
        st.markdown("**General ATS Tips**")
        for tip in general_tips:
            st.markdown(f"• {tip}")


    # ────────────────────
    # TAB 3 — Job Matches
    # ────────────────────
    with tab3:
        st.markdown('<div class="section-header">Matching Jobs</div>', unsafe_allow_html=True)

        if not jobs:
            st.warning("No jobs found. Indeed may be blocking the scraper, or RemoteOK returned no results for this role. Try a broader role name.")
        else:
            st.markdown(f"Found **{len(jobs)}** jobs matching **{target_role}**")

            # Source breakdown
            indeed_count = sum(1 for j in jobs if j["source"] == "Indeed")
            rok_count = sum(1 for j in jobs if j["source"] == "RemoteOK")
            st.caption(f"Indeed: {indeed_count} | RemoteOK: {rok_count}")
            st.markdown("---")

            for job in jobs:
                score = job.get("match_score", 0)
                badge_color = "#28a745" if score >= 70 else "#ffc107" if score >= 40 else "#888"
                source_badge = "🟦 RemoteOK" if job["source"] == "RemoteOK" else "🟥 Indeed"
                missing_skills = job.get("missing_skills", [])

                st.markdown(f"""
                <div class="job-card">
                    <div class="job-title">{job['title']}</div>
                    <div class="job-meta">🏢 {job['company']} &nbsp;|&nbsp; 📍 {job['location']} &nbsp;|&nbsp; {source_badge}</div>
                    <span class="match-badge" style="background:{badge_color}20; color:{badge_color}; border: 1px solid {badge_color};">
                        Match: {score}%
                    </span>
                    {"<br><small style='color:#888'>Missing: " + ", ".join(missing_skills) + "</small>" if missing_skills else ""}
                </div>
                """, unsafe_allow_html=True)

                if job.get("url"):
                    st.markdown(f"[View Job ↗]({job['url']})", unsafe_allow_html=False)

                st.markdown("")


    # ────────────────────
    # TAB 4 — Skill Gap
    # ────────────────────
    with tab4:
        st.markdown('<div class="section-header">Skill Gap Analysis</div>', unsafe_allow_html=True)

        coverage = skill_gap["coverage_pct"]
        matched = skill_gap["matched_skills"]
        missing_skills = skill_gap["missing_skills"]
        priority = skill_gap["priority_skills"]
        roadmap = skill_gap["learning_roadmap"]

        # Coverage metric
        col_cov, col_matched, col_missing = st.columns(3)
        col_cov.metric("Role Coverage", f"{coverage}%")
        col_matched.metric("Skills You Have", len(matched))
        col_missing.metric("Skills to Learn", len(missing_skills))

        st.markdown("---")

        # Skills you have
        st.markdown(f"**Skills you already have for *{target_role}*:**")
        if matched:
            pills_html = "".join(
                f'<span class="skill-pill skill-have">✓ {s}</span>' for s in matched
            )
            st.markdown(f'<div>{pills_html}</div>', unsafe_allow_html=True)
        else:
            st.warning("No matching skills detected. Make sure your Skills section is filled out clearly.")

        st.markdown("")

        # Skills to learn
        st.markdown("**Skills to learn:**")
        if missing_skills:
            pills_html = "".join(
                f'<span class="skill-pill skill-missing">✗ {s}</span>' for s in missing_skills
            )
            st.markdown(f'<div>{pills_html}</div>', unsafe_allow_html=True)
        else:
            st.success("You have all required skills for this role!")

        # Priority
        if priority:
            st.markdown("---")
            st.markdown("**🎯 Focus on these first:**")
            for i, skill in enumerate(priority, 1):
                st.markdown(f"**{i}.** {skill}")

        # Roadmap
        if roadmap:
            st.markdown("---")
            st.markdown("**📍 Learning Roadmap**")
            for phase in roadmap:
                st.markdown(f"• {phase}")

        # Extracted skills (debug/transparency)
        with st.expander("📋 Skills extracted from your resume"):
            if skills_list:
                st.write(", ".join(skills_list))
            else:
                st.warning("No skills extracted. Check that your resume has a clearly labeled Skills section.")