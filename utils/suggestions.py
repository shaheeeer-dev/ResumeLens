"""
utils/suggestions.py — AI‑powered improvement suggestions via Groq
"""
import json
import streamlit as st
from groq import Groq

# ----------------------------------------------------------------------
# 1. Groq client (reads key from Streamlit secrets)
# ----------------------------------------------------------------------
@st.cache_resource
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


# ----------------------------------------------------------------------
# 2. Core AI function
# ----------------------------------------------------------------------
def _ai_suggestions(ats_result: dict, raw_text: str) -> dict:
    """
    Sends the resume text + ATS findings to Groq and returns a
    structured JSON with per‑section advice, rewrite examples,
    weak buzzwords, and repeated phrases.
    """
    # Build a summary of ATS findings for the model
    section_findings = []
    for section, data in ats_result.get("section_scores", {}).items():
        issues = data.get("issues", [])
        passed = data.get("passed_checks", [])
        score = data["score"]
        findings = f"{section}: score={score}%"
        if issues:
            findings += f", issues: {'; '.join(issues)}"
        if passed:
            findings += f", passed: {'; '.join(passed)}"
        section_findings.append(findings)

    ats_summary = "\n".join(section_findings)

    prompt = f"""
You are an expert resume coach and ATS analyst. Below is a resume and a list of automated ATS findings.

Your job is to return a JSON object with exactly these keys:

- "section_suggestions": an object where each key is a section name (e.g., "experience", "projects", "skills", "summary", "education", "contact", "certifications") and the value is an object with:
    - "advice": an array of 1‑3 actionable, specific suggestions for that section. Use the ATS issues to guide you, but also notice other weaknesses.
    - "rewrite_example": either null or an object with "weak" and "strong" strings. If the section contains bullet points, pick the weakest one and rewrite it with more impact, action verbs, and quantified results. If there's no text to rewrite, set to null.

- "general_tips": an array of 3‑5 general ATS tips that apply to this resume (not generic copy‑paste, but derived from the actual content).

- "weak_buzzwords": an array of strings that were overused or vague (e.g., "helped", "worked on", "assisted with", "responsible for", "various", "tasks"). Include a short explanation for each.

- "repeated_phrases": an array of phrases that appear more than twice in the resume, each with a note on where they appear and why that hurts.

Important:
- Be brutally honest but constructive.
- For rewrite_example, make sure the "strong" version is realistic and keeps the same factual core.
- Return only the JSON object, no other text.

ATS Findings:
{ats_summary}

Resume Text:
---
{raw_text[:6000]}   # trim to avoid token limits
---
"""
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=2500,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI suggestion engine failed: {e}")
        # fallback to empty structure
        return {
            "section_suggestions": {},
            "general_tips": [],
            "weak_buzzwords": [],
            "repeated_phrases": [],
        }


# ----------------------------------------------------------------------
# 3. Public function – same signature as before, but accepts raw_text
# ----------------------------------------------------------------------
def generate_suggestions(ats_result: dict, raw_text: str = "") -> dict:
    """
    Returns a dict with:
      - section_suggestions  (as before)
      - general_tips         (as before)
      - weak_buzzwords       (NEW)
      - repeated_phrases     (NEW)
    """
    if not raw_text.strip():
        # fallback: return empty if no text provided
        return {
            "section_suggestions": {},
            "general_tips": [],
            "weak_buzzwords": [],
            "repeated_phrases": [],
        }

    ai_output = _ai_suggestions(ats_result, raw_text)

    return {
        "section_suggestions": ai_output.get("section_suggestions", {}),
        "general_tips": ai_output.get("general_tips", []),
        "weak_buzzwords": ai_output.get("weak_buzzwords", []),
        "repeated_phrases": ai_output.get("repeated_phrases", []),
    }