"""
utils/suggestions.py
Generates per-section improvement suggestions based on ATS scoring results.
"""

# Rewrite examples per section showing weak → strong
REWRITE_EXAMPLES = {
    "experience": {
        "weak":   "Worked on backend tasks and helped with the team.",
        "strong": "Led backend development of a REST API serving 10K+ daily users, reducing response time by 35% using caching.",
    },
    "projects": {
        "weak":   "Made a vehicle detection project using Python.",
        "strong": "Built a real-time Vehicle Monitoring System using Python, OpenCV, and YOLOv8, achieving 92% detection accuracy on a 5K-image dataset.",
    },
    "skills": {
        "weak":   "Python, SQL, some web stuff.",
        "strong": "Python · FastAPI · Django · PostgreSQL · Redis · Docker · Git · REST APIs · Linux",
    },
    "summary": {
        "weak":   "I am a computer science student looking for opportunities.",
        "strong": "Final-year CS student with hands-on experience in backend development (Django, FastAPI) and ML (PyTorch, scikit-learn), seeking a software engineering internship.",
    },
}

# Advice rules: maps (section, issue_keyword) → suggestion text
ADVICE_RULES = {
    "experience": [
        {
            "trigger": "metrics",
            "advice": "Add numbers wherever possible — users served, performance gains, team size, time saved.",
        },
        {
            "trigger": "brief",
            "advice": "Each role should have 3–5 bullet points. Use the format: Action Verb + What You Did + Result.",
        },
        {
            "trigger": "keyword",
            "advice": "Include keywords from job descriptions: 'designed', 'implemented', 'optimized', 'deployed'.",
        },
    ],
    "projects": [
        {
            "trigger": "technologies",
            "advice": "Always list the specific tech stack used — language, frameworks, tools, and any APIs.",
        },
        {
            "trigger": "impact",
            "advice": "Quantify the project: dataset size, accuracy achieved, number of users, deployment status (live link or GitHub).",
        },
        {
            "trigger": "brief",
            "advice": "Each project should have a 2–3 line description: what it does, how it was built, and what it achieved.",
        },
    ],
    "skills": [
        {
            "trigger": "brief",
            "advice": "List at least 12–15 skills. Group them: Languages · Frameworks · Databases · Tools · Platforms.",
        },
    ],
    "contact": [
        {
            "trigger": "linkedin",
            "advice": "Add your LinkedIn URL — many ATS systems and recruiters check this directly.",
        },
        {
            "trigger": "github",
            "advice": "Add your GitHub profile — essential for technical roles to showcase your work.",
        },
        {
            "trigger": "email",
            "advice": "Your resume must have a professional email address.",
        },
        {
            "trigger": "phone",
            "advice": "Include a phone number with country code for international roles.",
        },
    ],
    "education": [
        {
            "trigger": "brief",
            "advice": "Include: degree name, institution, graduation year, and GPA (if 3.0+). Add relevant coursework if experience is limited.",
        },
    ],
    "certifications": [
        {
            "trigger": "missing",
            "advice": "Even one certification (Google, AWS, Coursera) significantly boosts ATS scores for technical roles.",
        },
    ],
    "summary": [
        {
            "trigger": "missing",
            "advice": "Add a 2–3 sentence summary at the top: who you are, your top skills, and what you're looking for.",
        },
        {
            "trigger": "brief",
            "advice": "Make your summary role-specific. Tailor it to the job you're applying for.",
        },
    ],
}

# General tips shown regardless of section scores
GENERAL_TIPS = [
    "Use a single-column layout — multi-column resumes often confuse ATS parsers.",
    "Avoid tables, text boxes, headers/footers — they get dropped by most ATS systems.",
    "File name matters: use 'FirstName_LastName_Resume.pdf', not 'CV_final_v3.pdf'.",
    "Keep your resume to 1 page if you have under 3 years of experience.",
    "Use standard section headings (Education, Experience) — creative names like 'My Journey' confuse ATS.",
]


def generate_suggestions(ats_result: dict) -> dict:
    """
    Given ATS scoring result, produce suggestions per section.
    Returns: { section: { advice: [str], rewrite_example: dict|None } }
    """
    suggestions = {}
    section_scores = ats_result.get("section_scores", {})

    for section, score_data in section_scores.items():
        section_advice = []
        rewrite = None

        issues = score_data.get("issues", [])
        score = score_data.get("score", 100)
        present = score_data.get("present", True)

        # Only suggest for sections that need improvement
        if score >= 90 and present:
            suggestions[section] = {"advice": [], "rewrite_example": None}
            continue

        rules = ADVICE_RULES.get(section, [])

        # Match rules against detected issues
        for rule in rules:
            trigger = rule["trigger"]
            # Check if any issue string mentions the trigger keyword
            if not present or any(trigger in issue.lower() for issue in issues):
                section_advice.append(rule["advice"])

        # If section is missing entirely, add all rules for it
        if not present and not section_advice:
            for rule in rules:
                section_advice.append(rule["advice"])

        # Add rewrite example if section score is below 70
        if score < 70 and section in REWRITE_EXAMPLES:
            rewrite = REWRITE_EXAMPLES[section]

        suggestions[section] = {
            "advice": section_advice,
            "rewrite_example": rewrite,
        }

    return {
        "section_suggestions": suggestions,
        "general_tips": GENERAL_TIPS,
    }
