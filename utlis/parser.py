"""
utils/parser.py
Extracts text from PDF and splits it into resume sections.
"""

import re
from io import BytesIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from pdfminer.high_level import extract_text


# Section header keywords to detect
SECTION_KEYWORDS = {
    "contact":       ["contact", "email", "phone", "linkedin", "github", "address", "location"],
    "education":     ["education", "academic", "degree", "university", "college", "school", "gpa"],
    "skills":        ["skills", "technologies", "tools", "languages", "frameworks", "competencies", "technical"],
    "experience":    ["experience", "work", "employment", "internship", "job", "position", "career"],
    "projects":      ["projects", "portfolio", "personal projects", "academic projects", "side projects"],
    "certifications":["certifications", "certificates", "courses", "training", "credentials", "licenses"],
    "summary":       ["summary", "objective", "profile", "about", "overview"],
}


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract raw text from an uploaded PDF file object."""
    try:
        raw_bytes = uploaded_file.read()
        text = extract_text(BytesIO(raw_bytes))
        return clean_text(text)
    except Exception as e:
        return f"ERROR: Could not extract text from PDF. {str(e)}"


def clean_text(text: str) -> str:
    """Remove excessive whitespace and fix common PDF extraction artifacts."""
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse 3+ newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip trailing spaces per line
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines).strip()


def parse_sections(text: str) -> dict:
    """
    Split resume text into labeled sections.
    Returns a dict: { section_name: section_text }
    """
    lines = text.split('\n')
    sections = {key: "" for key in SECTION_KEYWORDS}
    sections["other"] = ""

    current_section = "other"

    for line in lines:
        line_lower = line.lower().strip()
        matched = False

        for section, keywords in SECTION_KEYWORDS.items():
            # A section header is usually a short line (< 40 chars) matching a keyword
            if len(line_lower) < 40 and any(kw in line_lower for kw in keywords):
                current_section = section
                matched = True
                break

        if not matched:
            sections[current_section] += line + '\n'

    # Strip each section
    return {k: v.strip() for k, v in sections.items()}


def extract_contact_info(text: str) -> dict:
    """Pull out email, phone, LinkedIn, GitHub from raw text."""
    contact = {}

    email = re.search(r'[\w.\-+]+@[\w.\-]+\.\w{2,}', text)
    phone = re.search(r'(\+?\d[\d\s\-().]{7,}\d)', text)
    linkedin = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
    github = re.search(r'github\.com/[\w\-]+', text, re.IGNORECASE)

    contact['email'] = email.group() if email else None
    contact['phone'] = phone.group().strip() if phone else None
    contact['linkedin'] = linkedin.group() if linkedin else None
    contact['github'] = github.group() if github else None

    return contact


def extract_skills_list(skills_text: str) -> list:
    """Parse the skills section into a list of individual skill tokens."""
    if not skills_text:
        return []

    # Split on common delimiters: commas, bullets, pipes, newlines
    tokens = re.split(r'[,|\n•·\-/]+', skills_text)
    skills = []

    for token in tokens:
        token = token.strip()
        # Filter noise: skip empty, skip long phrases (likely sentences not skills)
        if token and len(token) < 40 and len(token) > 1:
            skills.append(token)

    return list(set(skills))  # deduplicate
