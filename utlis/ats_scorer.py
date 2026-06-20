"""
utils/ats_scorer.py
Scores resume sections and produces an overall ATS score.
"""

from utils.parser import extract_contact_info


# Minimum word counts to consider a section "sufficient"
SECTION_MIN_WORDS = {
    "contact":        10,
    "education":      20,
    "skills":         15,
    "experience":     50,
    "projects":       30,
    "certifications": 5,
    "summary":        20,
}

# Weight of each section in the overall score (must sum to 100)
SECTION_WEIGHTS = {
    "contact":        15,
    "education":      15,
    "skills":         20,
    "experience":     25,
    "projects":       15,
    "certifications":  5,
    "summary":         5,
}

# Bonus keywords that indicate quality content
QUALITY_SIGNALS = {
    "experience": ["achieved", "led", "built", "developed", "increased", "reduced",
                   "managed", "delivered", "launched", "improved", "%", "users", "revenue"],
    "projects":   ["github", "deployed", "api", "accuracy", "performance", "dataset",
                   "model", "system", "application", "%", "users"],
    "skills":     [],  # scored by count instead
}


def score_section(section_name: str, section_text: str, contact_info: dict = None) -> dict:
    """
    Score a single section. Returns:
    {
        score: int (0–100),
        present: bool,
        word_count: int,
        issues: [str],
        passed_checks: [str]
    }
    """
    issues = []
    passed = []
    word_count = len(section_text.split()) if section_text else 0
    present = word_count > 0

    # --- Contact section: special logic ---
    if section_name == "contact":
        return _score_contact(contact_info or {})

    # --- Section missing entirely ---
    if not present:
        return {
            "score": 0,
            "present": False,
            "word_count": 0,
            "issues": [f"{section_name.title()} section is missing"],
            "passed_checks": [],
        }

    # --- Word count check ---
    min_words = SECTION_MIN_WORDS.get(section_name, 20)
    if word_count < min_words:
        issues.append(f"Too brief — only {word_count} words (aim for {min_words}+)")
        content_score = 40
    elif word_count < min_words * 2:
        passed.append("Section present with basic content")
        content_score = 70
    else:
        passed.append("Section has sufficient content length")
        content_score = 90

    # --- Quality signals check ---
    signals = QUALITY_SIGNALS.get(section_name, [])
    text_lower = section_text.lower()
    matched_signals = [s for s in signals if s in text_lower]

    if signals:
        ratio = len(matched_signals) / len(signals)
        if ratio == 0:
            issues.append("No measurable results or impact keywords found")
            quality_score = 50
        elif ratio < 0.3:
            issues.append("Few strong action verbs or metrics — add numbers and impact")
            quality_score = 65
        else:
            passed.append("Good use of impact keywords and metrics")
            quality_score = 100
        final_score = int(content_score * 0.6 + quality_score * 0.4)
    else:
        final_score = content_score

    # Clamp
    final_score = max(0, min(100, final_score))

    return {
        "score": final_score,
        "present": True,
        "word_count": word_count,
        "issues": issues,
        "passed_checks": passed,
    }


def _score_contact(contact_info: dict) -> dict:
    issues = []
    passed = []
    score = 0

    checks = {
        "email":    ("Email address", 35),
        "phone":    ("Phone number", 25),
        "linkedin": ("LinkedIn profile", 25),
        "github":   ("GitHub profile", 15),
    }

    for field, (label, weight) in checks.items():
        if contact_info.get(field):
            score += weight
            passed.append(f"{label} found")
        else:
            issues.append(f"{label} is missing")

    return {
        "score": score,
        "present": score > 0,
        "word_count": sum(1 for v in contact_info.values() if v),
        "issues": issues,
        "passed_checks": passed,
    }


def score_resume(sections: dict, raw_text: str) -> dict:
    """
    Run full ATS scoring. Returns:
    {
        overall_score: int,
        section_scores: { section: score_dict },
        missing_sections: [str],
        grade: str,
    }
    """
    contact_info = extract_contact_info(raw_text)
    section_scores = {}
    weighted_total = 0
    missing = []

    for section, weight in SECTION_WEIGHTS.items():
        text = sections.get(section, "")
        result = score_section(section, text, contact_info if section == "contact" else None)
        section_scores[section] = result

        if not result["present"]:
            missing.append(section.title())

        weighted_total += (result["score"] / 100) * weight

    overall = int(weighted_total)
    grade = _grade(overall)

    return {
        "overall_score": overall,
        "section_scores": section_scores,
        "missing_sections": missing,
        "grade": grade,
        "contact_info": contact_info,
    }


def _grade(score: int) -> str:
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 55:
        return "Average"
    elif score >= 40:
        return "Needs Work"
    else:
        return "Poor"
