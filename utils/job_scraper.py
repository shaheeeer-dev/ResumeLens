"""
utils/job_scraper.py
Scrapes job listings from RemoteOK (public API) and Indeed (HTML scraping).
Matches jobs to resume skills using TF-IDF cosine similarity.
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Rotate user agents to avoid blocks on Indeed
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ─────────────────────────────────────────────
# RemoteOK — Free public API, no auth needed
# ─────────────────────────────────────────────

def scrape_remoteok(role: str, limit: int = 10) -> list:
    """
    Fetch jobs from RemoteOK public API.
    Returns list of job dicts.
    """
    url = "https://remoteok.com/api"
    headers = {**HEADERS, "User-Agent": USER_AGENTS[0]}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # First element is a legal notice dict, skip it
        jobs_raw = [j for j in data if isinstance(j, dict) and "position" in j]

        # Filter by role keyword
        role_keywords = role.lower().split()
        matched = []

        for job in jobs_raw:
            title = job.get("position", "").lower()
            tags = " ".join(job.get("tags", [])).lower()
            description = job.get("description", "")

            if any(kw in title or kw in tags for kw in role_keywords):
                matched.append({
                    "title":       job.get("position", "N/A"),
                    "company":     job.get("company", "N/A"),
                    "location":    "Remote",
                    "url":         job.get("url", "https://remoteok.com"),
                    "description": _clean_html(description),
                    "source":      "RemoteOK",
                    "tags":        job.get("tags", []),
                })

            if len(matched) >= limit:
                break

        return matched

    except Exception as e:
        print(f"[RemoteOK] Error: {e}")
        return []


# ─────────────────────────────────────────────
# Indeed — HTML scraping (may need UA rotation)
# ─────────────────────────────────────────────

def scrape_indeed(role: str, location: str = "remote", limit: int = 10) -> list:
    """
    Scrape Indeed job listings.
    Note: Indeed may block scraping. If it fails, falls back to empty list gracefully.
    """
    query = role.replace(" ", "+")
    loc = location.replace(" ", "+")
    url = f"https://www.indeed.com/jobs?q={query}&l={loc}&sort=date"

    import random
    ua = random.choice(USER_AGENTS)
    headers = {**HEADERS, "User-Agent": ua}

    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            print(f"[Indeed] Status {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|jobsearch-SerpJobCard"))

        if not job_cards:
            # Try alternate selectors (Indeed changes HTML often)
            job_cards = soup.find_all("td", class_="resultContent")

        jobs = []
        for card in job_cards[:limit]:
            title_el = card.find("h2") or card.find("a", {"data-jk": True})
            company_el = card.find("span", {"data-testid": "company-name"}) or card.find("span", class_=re.compile("companyName"))
            location_el = card.find("div", {"data-testid": "text-location"}) or card.find("div", class_=re.compile("companyLocation"))
            link_el = card.find("a", href=True)

            title = title_el.get_text(strip=True) if title_el else "N/A"
            company = company_el.get_text(strip=True) if company_el else "N/A"
            loc_text = location_el.get_text(strip=True) if location_el else location
            href = link_el["href"] if link_el else ""
            job_url = f"https://www.indeed.com{href}" if href.startswith("/") else href

            if title != "N/A":
                jobs.append({
                    "title":       title,
                    "company":     company,
                    "location":    loc_text,
                    "url":         job_url,
                    "description": "",  # Indeed hides full desc without JS
                    "source":      "Indeed",
                    "tags":        [],
                })

        return jobs

    except Exception as e:
        print(f"[Indeed] Error: {e}")
        return []


# ─────────────────────────────────────────────
# Match scoring — TF-IDF cosine similarity
# ─────────────────────────────────────────────

def compute_match_score(resume_skills: list, job: dict) -> int:
    """
    Compute match % between resume skills and job (title + tags + description).
    Returns 0–100.
    """
    resume_text = " ".join(resume_skills).lower()
    job_text = " ".join([
        job.get("title", ""),
        " ".join(job.get("tags", [])),
        job.get("description", ""),
    ]).lower()

    if not resume_text.strip() or not job_text.strip():
        return 0

    try:
        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform([resume_text, job_text])
        score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return int(score * 100)
    except Exception:
        return 0


def find_missing_skills(resume_skills: list, job: dict) -> list:
    """
    Given resume skills and a job's tags/description,
    return skills mentioned in the job but not in the resume.
    """
    resume_lower = {s.lower() for s in resume_skills}
    job_tags = [t.lower() for t in job.get("tags", [])]

    missing = []
    for tag in job_tags:
        # Only flag if it looks like a tech skill (short token)
        if len(tag) < 25 and tag not in resume_lower:
            missing.append(tag)

    return missing[:8]  # cap at 8


def get_all_jobs(role: str, resume_skills: list, location: str = "remote") -> list:
    """
    Fetch from all sources, score each job, return sorted list.
    """
    all_jobs = []

    remoteok_jobs = scrape_remoteok(role, limit=10)
    indeed_jobs = scrape_indeed(role, location=location, limit=10)

    all_jobs.extend(remoteok_jobs)
    all_jobs.extend(indeed_jobs)

    # Score and enrich each job
    for job in all_jobs:
        job["match_score"] = compute_match_score(resume_skills, job)
        job["missing_skills"] = find_missing_skills(resume_skills, job)

    # Sort by match score descending
    all_jobs.sort(key=lambda x: x["match_score"], reverse=True)

    return all_jobs


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _clean_html(html_text: str) -> str:
    """Strip HTML tags from a string."""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ", strip=True)[:500]
