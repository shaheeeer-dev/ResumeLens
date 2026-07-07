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
    import os
    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY secret or environment variable is missing.")
    return Groq(api_key=api_key)


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
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=2500,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.warning("Groq AI suggestion engine could not be reached (possibly invalid API key or connection error). Mock recommendations loaded for testing.")
        return _get_mock_suggestions(ats_result)


def _get_mock_suggestions(ats_result: dict) -> dict:
    """
    Generate realistic mock suggestions based on ATS score breakdown
    so the user can work on the frontend even without a valid API key.
    """
    mock_suggestions = {
        "experience": {
            "advice": [
                "Begin bullet points with strong action verbs (e.g., 'Spearheaded', 'Optimized') instead of passive phrases.",
                "Quantify your impact by adding metrics, percentages, and dollar amounts (e.g., 'reduced latency by 30%').",
                "Ensure your tech stack is explicitly mentioned within each job description."
            ],
            "rewrite_example": {
                "weak": "Responsible for developing backend features using Python.",
                "strong": "Spearheaded development of 5+ microservices using Python and FastAPI, reducing API latency by 35% and supporting 10k+ daily active users."
            }
        },
        "projects": {
            "advice": [
                "Include direct links to GitHub repositories or live deployments for verification.",
                "Clearly state the problem, your solution, and the technologies used in each project description."
            ],
            "rewrite_example": {
                "weak": "Made an AI resume web app using Streamlit.",
                "strong": "Architected an AI-powered resume analyzer using Streamlit and scikit-learn; optimized parser parsing algorithms to process PDFs in under 2 seconds."
            }
        },
        "skills": {
            "advice": [
                "Group your skills logically into categories (e.g., Languages, Frameworks, Developer Tools).",
                "Remove outdated technologies to keep your profile modern and focused."
            ],
            "rewrite_example": None
        },
        "summary": {
            "advice": [
                "Make your professional summary more concise and punchy (aim for 3-4 sentences maximum).",
                "Tailor the summary to align directly with your target role keywords."
            ],
            "rewrite_example": {
                "weak": "Software engineer looking for a backend role to use my skills.",
                "strong": "Results-driven Software Engineer with 3+ years of experience designing scalable REST APIs and backend architectures. Proven track record of optimizing database performance and deploying cloud-native applications."
            }
        },
        "contact": {
            "advice": [
                "Include a professional LinkedIn profile and a link to your GitHub portfolio.",
                "Ensure your contact details are placed clearly at the top of the page."
            ],
            "rewrite_example": None
        },
        "education": {
            "advice": [
                "List your degree, major, institution, and graduation year clearly.",
                "Add relevant coursework or academic honors if you are a recent graduate."
            ],
            "rewrite_example": None
        },
        "certifications": {
            "advice": [
                "List active cloud or developer certifications (e.g., AWS Certified Developer, Google Cloud Engineer) to stand out."
            ],
            "rewrite_example": None
        }
    }
    
    # Filter only relevant sections that have issues (score < 90)
    section_suggestions = {}
    for section, data in ats_result.get("section_scores", {}).items():
        if data.get("score", 0) < 90 and section in mock_suggestions:
            section_suggestions[section] = mock_suggestions[section]

    # Fallback to general ones if all sections are perfect
    if not section_suggestions:
        section_suggestions = {
            "experience": mock_suggestions["experience"]
        }

    return {
        "section_suggestions": section_suggestions,
        "general_tips": [
            "Keep your resume to a single page if you have less than 5 years of experience.",
            "Use standard, ATS-friendly section headings like 'Work Experience' and 'Skills' rather than creative alternatives.",
            "Save and upload your resume as a PDF to preserve exact formatting, but ensure it is text-selectable."
        ],
        "weak_buzzwords": [
            "Responsible for - Vague descriptor that highlights duties rather than achievements. Replace with action verbs.",
            "Helped - Passive word. Use words like 'Facilitated', 'Collaborated', or 'Championed'.",
            "Worked on - Doesn't convey your specific contribution. Specify whether you designed, implemented, or tested."
        ],
        "repeated_phrases": [
            "Developed backend - Repeated multiple times in Experience and Projects. Use synonyms like 'Engineered', 'Architected', or 'Constructed'."
        ]
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