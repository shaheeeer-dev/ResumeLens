"""
utils/skill_gap.py
Compares resume skills against role-specific required skills.
"""

# Role → required skills mapping
# Add more roles as needed
ROLE_SKILL_MAP = {
    "backend developer": [
        "Python", "Java", "Node.js", "REST APIs", "SQL", "PostgreSQL",
        "MySQL", "Redis", "Docker", "Git", "Linux", "Spring Boot",
        "Django", "FastAPI", "Express.js", "System Design",
    ],
    "frontend developer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Vue.js",
        "Next.js", "Tailwind CSS", "Git", "REST APIs", "Webpack",
        "Responsive Design", "Figma", "Testing",
    ],
    "full stack developer": [
        "HTML", "CSS", "JavaScript", "React", "Node.js", "Python",
        "REST APIs", "SQL", "PostgreSQL", "MongoDB", "Docker",
        "Git", "Linux", "TypeScript", "System Design",
    ],
    "data scientist": [
        "Python", "R", "SQL", "pandas", "numpy", "scikit-learn",
        "TensorFlow", "PyTorch", "Matplotlib", "Statistics",
        "Machine Learning", "Deep Learning", "Jupyter", "Git",
        "Data Visualization", "Feature Engineering",
    ],
    "machine learning engineer": [
        "Python", "TensorFlow", "PyTorch", "scikit-learn", "SQL",
        "MLOps", "Docker", "Kubernetes", "REST APIs", "Git",
        "Deep Learning", "NLP", "Computer Vision", "Data Pipelines",
        "Model Deployment", "AWS/GCP/Azure",
    ],
    "data analyst": [
        "SQL", "Excel", "Python", "pandas", "Power BI", "Tableau",
        "Statistics", "Data Visualization", "R", "Google Sheets",
        "Reporting", "ETL", "Git",
    ],
    "devops engineer": [
        "Linux", "Docker", "Kubernetes", "CI/CD", "Jenkins",
        "AWS", "GCP", "Azure", "Terraform", "Ansible",
        "Git", "Python", "Bash", "Monitoring", "Networking",
    ],
    "android developer": [
        "Kotlin", "Java", "Android SDK", "Jetpack Compose",
        "REST APIs", "SQLite", "Room DB", "Git", "Firebase",
        "MVVM", "Retrofit", "Material Design",
    ],
    "software engineer": [
        "Data Structures", "Algorithms", "Python", "Java", "C++",
        "System Design", "SQL", "Git", "REST APIs", "Docker",
        "Linux", "OOP", "Testing",
    ],
}

# Normalize role names for fuzzy matching
def _normalize(text: str) -> str:
    return text.lower().strip()


def get_required_skills(role: str) -> list:
    """
    Return the required skill list for a given role.
    Falls back to a generic software engineer list if role not found.
    """
    role_lower = _normalize(role)

    # Exact match
    if role_lower in ROLE_SKILL_MAP:
        return ROLE_SKILL_MAP[role_lower]

    # Partial match — find best fit
    for key in ROLE_SKILL_MAP:
        if any(word in role_lower for word in key.split()):
            return ROLE_SKILL_MAP[key]

    # Default fallback
    return ROLE_SKILL_MAP["software engineer"]


def analyze_skill_gap(resume_skills: list, target_role: str) -> dict:
    """
    Compare resume skills against required skills for the target role.

    Returns:
    {
        target_role: str,
        required_skills: [str],
        matched_skills: [str],
        missing_skills: [str],
        coverage_pct: int,
        priority_skills: [str],   # top 5 missing skills to learn first
        learning_roadmap: [str],  # ordered list of what to learn
    }
    """
    required = get_required_skills(target_role)
    resume_lower = {s.lower().strip() for s in resume_skills}

    matched = []
    missing = []

    for skill in required:
        skill_lower = skill.lower()
        # Fuzzy check: skill substring match (e.g. "postgresql" matches "postgres")
        if skill_lower in resume_lower or any(skill_lower in r or r in skill_lower for r in resume_lower):
            matched.append(skill)
        else:
            missing.append(skill)

    coverage = int((len(matched) / len(required)) * 100) if required else 0

    # Priority: first 5 missing skills (ordered as they appear in the role map)
    priority = missing[:5]

    # Learning roadmap — group into phases
    roadmap = _build_roadmap(missing, target_role)

    return {
        "target_role":      target_role,
        "required_skills":  required,
        "matched_skills":   matched,
        "missing_skills":   missing,
        "coverage_pct":     coverage,
        "priority_skills":  priority,
        "learning_roadmap": roadmap,
    }


def _build_roadmap(missing_skills: list, role: str) -> list:
    """
    Return an ordered list of skills to learn, grouped into phases.
    Simple heuristic: first 3 are "Start Now", next 3 "Learn Next", rest "Long Term".
    """
    if not missing_skills:
        return []

    roadmap = []

    if len(missing_skills) >= 1:
        phase1 = missing_skills[:3]
        roadmap.append(f"Phase 1 — Start Now: {', '.join(phase1)}")

    if len(missing_skills) > 3:
        phase2 = missing_skills[3:6]
        roadmap.append(f"Phase 2 — Learn Next: {', '.join(phase2)}")

    if len(missing_skills) > 6:
        phase3 = missing_skills[6:]
        roadmap.append(f"Phase 3 — Long Term: {', '.join(phase3)}")

    return roadmap
