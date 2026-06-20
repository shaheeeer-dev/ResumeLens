# Resume Lens 📄

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/scikit--learn-1.4+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>
</p>

<p align="center">
  <b>AI-powered resume analyzer with ATS scoring, improvement suggestions, live job matching, and skill gap analysis.</b>
</p>

---

## What it does

Upload your resume. Get a full breakdown in under 30 seconds.

| Feature | Description |
|---|---|
| 📊 **ATS Score** | Weighted section scoring across Contact, Education, Skills, Experience, Projects, Certifications |
| 💡 **Suggestions** | Per-section feedback with before/after rewrite examples |
| 💼 **Job Matching** | Live job scraping from RemoteOK and Indeed, matched to your skills via TF-IDF |
| 🎯 **Skill Gap** | Compares your resume skills against role requirements and generates a learning roadmap |

---

## Demo

```
Upload Resume (PDF)
        ↓
    ATS Score → 90 / 100 (Excellent)
        ↓
  Suggestions → "Add measurable impact to Experience section"
        ↓
  Job Matches → Backend Intern @ Stripe — Match: 82%
        ↓
  Skill Gap   → Missing: Spring Boot, Docker, Redis
                Phase 1: Learn Spring Boot, Docker
                Phase 2: Learn Redis, Kubernetes
```

---

## Project Structure

```
shortlistd/
├── app.py                  # Main Streamlit app
├── requirements.txt
├── README.md
└── utils/
    ├── parser.py           # PDF text extraction + section parsing
    ├── ats_scorer.py       # Weighted ATS scoring logic
    ├── suggestions.py      # Improvement suggestion engine + rewrite examples
    ├── job_scraper.py      # RemoteOK API + Indeed scraper + TF-IDF match scoring
    └── skill_gap.py        # Role skill map, gap analysis, learning roadmap
```

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/shortlistd.git
cd shortlistd

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## Usage

1. Upload your PDF resume
2. Enter your target role — `Backend Developer`, `Data Scientist`, `DevOps Engineer`, etc.
3. Enter a job location or leave it as `remote`
4. Hit **Analyze Resume**
5. Review your results across 4 tabs

---

## Supported Roles for Skill Gap Analysis

| Role | Role |
|---|---|
| Backend Developer | Frontend Developer |
| Full Stack Developer | Data Scientist |
| Machine Learning Engineer | Data Analyst |
| DevOps Engineer | Android Developer |
| Software Engineer | *(easily extensible)* |

To add a new role, open `utils/skill_gap.py` and add an entry to `ROLE_SKILL_MAP`.

---

## Tech Stack

<p>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/pdfminer.six-PDF_Parsing-4A90D9?style=flat-square"/>
  <img src="https://img.shields.io/badge/BeautifulSoup4-Scraping-43B02A?style=flat-square"/>
  <img src="https://img.shields.io/badge/scikit--learn-TF--IDF_Matching-F7931E?style=flat-square&logo=scikit-learn&logoColor=white"/>
  <img src="https://img.shields.io/badge/Requests-HTTP-009688?style=flat-square"/>
</p>

---

## Job Scraping Notes

- **RemoteOK** — Free public JSON API, no auth required, works reliably
- **Indeed** — HTML scraping with rotating user-agents; may get rate-limited depending on your IP
- **LinkedIn** — intentionally excluded (heavily restricted, ToS issues)

If Indeed scraping fails, the app degrades gracefully and still returns RemoteOK results.

---

## Limitations

- PDF parsing may struggle with heavily styled or multi-column resume templates — plain single-column PDFs work best
- Skill extraction is keyword-based, not semantic
- Indeed scraping can break if they update their HTML structure
- Job match scoring uses TF-IDF cosine similarity, not an LLM — good enough for demo purposes

---

## License

MIT — do whatever you want with it.