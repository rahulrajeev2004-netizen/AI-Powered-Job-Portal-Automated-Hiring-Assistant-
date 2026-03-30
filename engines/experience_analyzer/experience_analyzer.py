import re
import json
import os
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional, Tuple

sys.path.append(os.getcwd())
from utils.logger import get_logger

logger = get_logger("experience_analyzer", "logs/experience_analysis.log")

# ============================================================
# DOMAIN CONFIGURATION
# ============================================================
TECH_CANDIDATE_KEYWORDS = ["data", "ai", "machine learning", "analytics", "engineer",
                            "software", "developer", "cloud", "devops", "backend", "frontend",
                            "fullstack", "python", "programming", "architect", "mlops"]

TECH_JOB_KEYWORDS = ["data", "analyst", "ai", "product", "technology", "business analyst",
                      "software", "developer", "engineer", "cloud", "machine learning",
                      "analytics", "backend", "frontend", "devops", "architect"]

INTERDISCIPLINARY_JOB_KEYWORDS = ["healthcare ai", "informatics", "medical claims", "health analytics",
                                    "telehealth", "telemedicine", "insurance nurse", "program manager",
                                    "healthcare consultant", "consultant"]

NURSING_KEYWORDS = ["staff nurse", "ward nurse", "icu nurse", "surgical nurse", "pediatric nurse",
                    "emergency nurse", "cardiac nurse", "obstetric nurse", "dialysis nurse",
                    "bedside nurse", "oncology nurse", "geriatric nurse", "psychiatric nurse",
                    "trauma nurse", "school nurse", "home health nurse", "traveling nurse",
                    "community health nurse", "addiction nurse", "military nurse",
                    "palliative", "phlebotomy", "perioperative", "rehabilitation nurse",
                    "occupational health nurse", "pain management nurse", "neurology nurse",
                    "endocrinology nurse", "rural nurse", "cosmetic nurse", "cruise nurse"]

# Skills for scoring
TECH_SKILLS = ["python", "sql", "machine learning", "pandas", "numpy", "scikit-learn", "tensorflow",
               "pytorch", "power bi", "tableau", "django", "javascript", "html", "css", "react",
               "node.js", "docker", "kubernetes", "aws", "azure", "gcp", "git", "matplotlib", "seaborn",
               "r", "scala", "spark", "nlp", "deep learning", "computer vision", "fastapi",
               "flask", "postgresql", "mongodb", "redis", "data visualization", "cloud", "devops",
               "serverless", "architecture", "microservices"]

HEALTH_SKILLS = ["patient care", "clinical", "bsc nursing", "gnm", "medication",
                 "iv therapy", "vital signs", "emergency response", "empathy", "counseling",
                 "wound care", "infection control", "documentation", "triage", "nursing"]

SCIENCE_SKILLS = ["polymer synthesis", "chemical analysis", "laboratory", "analytical chemistry",
                  "titration", "spectroscopy", "chromatography", "lab documentation", "research"]

# Scoring reference for title similarity
STRONG_TECH_ROLE_PAIRS = {
    "data analyst": ["data analyst", "data science", "analytics", "business analyst"],
    "software engineer": ["software engineer", "backend developer", "developer", "programmer"],
    "junior backend developer": ["backend developer", "software engineer", "developer"],
    "cloud architect": ["cloud", "architect", "devops", "infrastructure", "aws", "azure"],
    "ai engineer": ["ai", "machine learning", "data science", "mlops"],
    "product manager": ["product manager", "product owner", "program manager"],
    "data scientist": ["data scientist", "machine learning", "ai engineer", "analytics"],
}


class ExperienceAnalyzer:
    def __init__(self, current_date: Optional[str] = None):
        if current_date:
            try:
                self.current_date = datetime.strptime(current_date, "%Y-%m")
            except:
                self.current_date = datetime.now()
        else:
            self.current_date = datetime.now()

    # ============================================================
    # STEP 1: EXPERIENCE EXTRACTION (Multi-format parser)
    # ============================================================
    def extract_experience_months(self, exp_text: str) -> int:
        if not exp_text or not exp_text.strip():
            return 0

        exp_text_lower = exp_text.lower()
        total_months = 0

        month_map = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
                     "june": 6, "july": 7, "august": 8, "september": 9,
                     "october": 10, "november": 11, "december": 12}

        is_present = any(w in exp_text_lower for w in ["present", "ongoing", "current"])

        # --- Format 1: "Month YYYY" (e.g., "July 2025") ---
        month_year_dates = re.findall(
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
            exp_text_lower
        )
        if month_year_dates and is_present:
            m, y = month_year_dates[0]
            start = datetime(int(y), month_map[m], 1)
            delta = relativedelta(self.current_date, start)
            return max(1, delta.years * 12 + delta.months)

        # --- Format 2: YYYY-Present (e.g., "2015-Present") ---
        year_to_present = re.findall(r'(\d{4})\s*[-–]\s*(present|ongoing|current)', exp_text_lower)
        if year_to_present:
            y = int(year_to_present[0][0])
            start = datetime(y, 1, 1)
            delta = relativedelta(self.current_date, start)
            total_months += max(1, delta.years * 12 + delta.months)

        # --- Format 3: YYYY-MM to YYYY-MM ---
        ym_ranges = re.findall(r'(\d{4})-(\d{2})\s*[-–to]+\s*(\d{4})-(\d{2})', exp_text)
        for sy, sm, ey, em in ym_ranges:
            start = datetime(int(sy), int(sm), 1)
            end = datetime(int(ey), int(em), 1)
            delta = relativedelta(end, start)
            total_months += max(0, delta.years * 12 + delta.months)

        if total_months > 0:
            return total_months

        # --- Format 4: YYYY to YYYY (e.g., "2016–2020") ---
        year_ranges = re.findall(r'(\d{4})\s*[-–]\s*(\d{4})', exp_text)
        for sy, ey in year_ranges:
            months = (int(ey) - int(sy)) * 12
            if months > 0:
                total_months += months

        return max(0, total_months)

    # ============================================================
    # STEP 2: CANDIDATE DOMAIN + SKILL DETECTION
    # ============================================================
    def detect_candidate_profile(self, resume_data: Dict) -> Tuple[str, List[str]]:
        all_text = " ".join(str(v) for v in resume_data.values()).lower()

        tech_score = sum(1 for kw in TECH_CANDIDATE_KEYWORDS if kw in all_text)
        health_score = sum(1 for kw in ["nurse", "nursing", "clinical", "patient", "hospital", "gnm"] if kw in all_text)
        sci_score = sum(1 for kw in ["chemistry", "polymer", "laboratory", "analytical", "spectroscopy"] if kw in all_text)

        if tech_score > 0 and tech_score >= health_score and tech_score >= sci_score:
            domain = "technology"
        elif health_score > 0 and health_score >= tech_score:
            domain = "healthcare"
        elif sci_score > 0:
            domain = "science"
        else:
            domain = "other"

        # Skill extraction
        skills = [s for s in TECH_SKILLS + HEALTH_SKILLS + SCIENCE_SKILLS if s in all_text]
        return domain, skills

    # ============================================================
    # STEP 3: JOB DOMAIN DETECTION
    # ============================================================
    def detect_job_domain(self, jd_title: str) -> str:
        title = jd_title.lower()
        # Check if pure nursing
        if any(kw in title for kw in NURSING_KEYWORDS):
            return "nursing"
        # Check interdisciplinary
        if any(kw in title for kw in INTERDISCIPLINARY_JOB_KEYWORDS):
            return "interdisciplinary"
        # Check tech-oriented
        if any(kw in title for kw in TECH_JOB_KEYWORDS):
            return "technology"
        # Check health
        if any(kw in title for kw in ["nurse", "nursing", "clinical", "health", "care", "medical"]):
            return "healthcare"
        return "other"

    # ============================================================
    # STEP 4: DOMAIN MATCH RESOLUTION
    # ============================================================
    def resolve_domain_match(self, cand_domain: str, job_domain: str) -> Tuple:
        """Returns (domain_match bool/str, domain_score float)"""
        if cand_domain == "technology" and job_domain == "technology":
            return True, 1.0
        if cand_domain == "technology" and job_domain == "interdisciplinary":
            return True, 0.75
        if cand_domain == "healthcare" and job_domain == "healthcare":
            return True, 1.0
        if cand_domain == "healthcare" and job_domain == "interdisciplinary":
            return True, 0.7
        if cand_domain == "technology" and job_domain == "healthcare":
            return False, 0.1
        if cand_domain == "technology" and job_domain == "nursing":
            return False, 0.0
        if cand_domain == "science" and job_domain in ["technology", "interdisciplinary"]:
            return False, 0.15
        if cand_domain == "science" and job_domain == "nursing":
            return False, 0.02
        return False, 0.05

    # ============================================================
    # STEP 5: TITLE SIMILARITY (40% weight)
    # ============================================================
    def compute_title_similarity(self, cand_domain: str, job_title: str, job_domain: str) -> float:
        job_lower = job_title.lower()
        job_words = set(re.findall(r'\w+', job_lower))

        best_score = 0.0

        # Look for best role match from reference pairs
        for ref_role, related in STRONG_TECH_ROLE_PAIRS.items():
            ref_words = set(ref_role.split())
            overlap = len(ref_words.intersection(job_words))
            if overlap > 0:
                score = overlap / max(len(ref_words), len(job_words))
                if score > best_score:
                    best_score = score

        # Extra boosts based on domain alignment
        if cand_domain == "technology":
            if job_domain == "technology":
                best_score = max(best_score, 0.4)
            elif job_domain == "interdisciplinary":
                best_score = max(best_score, 0.3)

        return round(min(best_score, 1.0), 3)

    # ============================================================
    # STEP 6: SKILL OVERLAP (30% weight)
    # ============================================================
    def compute_skill_overlap(self, cand_skills: List[str], jd_data: Dict) -> float:
        jd_mandatory = [s.lower() for s in jd_data.get("requirements", {}).get("skills", {}).get("mandatory", [])]
        jd_preferred = [s.lower() for s in jd_data.get("requirements", {}).get("skills", {}).get("preferred", [])]
        jd_all_skills = jd_mandatory + jd_preferred

        if not jd_all_skills:
            return 0.35  # Neutral when JD has no skills defined

        matches = 0
        for jd_skill in jd_all_skills:
            jd_tokens = set(jd_skill.lower().split())
            for cand_skill in cand_skills:
                cand_tokens = set(cand_skill.lower().split())
                if jd_tokens & cand_tokens:
                    matches += 1
                    break

        return round(min(matches / max(len(jd_all_skills), 1), 1.0), 3)

    # ============================================================
    # STEP 7: EXPERIENCE LEVEL MATCH (10% weight)
    # ============================================================
    def compute_exp_score(self, total_months: int, jd_data: Dict) -> Tuple[float, bool]:
        req_years = jd_data.get("requirements", {}).get("experience", {}).get("min_years", 0) or 0
        req_months = int(req_years) * 12

        if total_months == 0:
            return 0.0, False
        if req_months == 0:
            return 0.8, True  # No requirement → pass
        score = min(total_months / req_months, 1.0)
        meets = (total_months >= req_months)
        return round(score, 3), meets

    # ============================================================
    # CORE ANALYZE METHOD
    # ============================================================
    def analyze(self, resume_data: Dict, jd_data: Dict, total_exp_override: Optional[int] = None) -> Dict:
        # 1. Total Experience
        resume_lower = {k.lower(): v for k, v in resume_data.items()}
        exp_text = str(resume_lower.get("work_experience", "") or resume_lower.get("experience", ""))
        total_months = total_exp_override if total_exp_override is not None else self.extract_experience_months(exp_text)

        # 2. Candidate Profile
        cand_domain, cand_skills = self.detect_candidate_profile(resume_data)

        # 3. JD Info
        jd_title = jd_data.get("job_title", "Unknown")
        job_domain = self.detect_job_domain(jd_title)

        # 4. Domain Match
        domain_match, domain_score = self.resolve_domain_match(cand_domain, job_domain)

        # Hard rule: Pure nursing for non-healthcare = exclude (score 0.0)
        if job_domain == "nursing" and cand_domain not in ("healthcare",):
            return {
                "job_title": jd_title,
                "relevance_score": 0.0,  # Will be filtered out (< 0.05)
                "domain_match": False,
                "total_experience_months": total_months,
                "meets_requirement": False
            }

        # 5. Component Scores
        title_score = self.compute_title_similarity(cand_domain, jd_title, job_domain)    # 40%
        skill_score = self.compute_skill_overlap(cand_skills, jd_data)                    # 30%
        exp_score, meets_req = self.compute_exp_score(total_months, jd_data)              # 10%

        # 6. Weighted Raw Score
        raw_score = (title_score * 0.40) + (skill_score * 0.30) + (domain_score * 0.20) + (exp_score * 0.10)

        # 7. TIERED SCORE NORMALIZATION
        # Tier 1: Exact domain match (Tech-to-Tech, Healthcare-to-Healthcare)
        if domain_match is True and cand_domain == job_domain:
            normalized = 0.65 + (raw_score * 0.28)    # Range: 0.65 - 0.93

        # Tier 2a: Interdisciplinary - strong title match (e.g. Clinical Data Analyst)
        elif domain_match is True and job_domain == "interdisciplinary" and title_score >= 0.35:
            normalized = 0.55 + (raw_score * 0.25)    # Range: 0.55 - 0.72

        # Tier 2b: Interdisciplinary - medium title match (e.g. Healthcare AI Trainer)
        elif domain_match is True and job_domain == "interdisciplinary" and title_score >= 0.15:
            normalized = 0.40 + (raw_score * 0.25)    # Range: 0.40 - 0.57

        # Tier 2c: Interdisciplinary - weak title match (e.g. Telehealth Nurse)
        elif domain_match is True and job_domain == "interdisciplinary":
            normalized = 0.25 + (raw_score * 0.25)    # Range: 0.25 - 0.42

        # Tier 3: Adjacent healthcare (e.g. Tech-to-Healthcare consultant)
        elif domain_match is True and job_domain == "healthcare":
            normalized = 0.18 + (raw_score * 0.15)    # Range: 0.18 - 0.29

        # Tier 4: Weak cross-domain (e.g. Science-to-Tech)
        elif domain_match is False and domain_score >= 0.10:
            normalized = 0.08 + (raw_score * 0.12)    # Range: 0.08 - 0.18

        # Tier 5: Clear mismatch
        else:
            normalized = raw_score * 0.10              # Range: 0.00 - 0.10

        # Hard cap: mismatches never exceed 0.20
        if domain_match is False:
            normalized = min(normalized, 0.20)

        # Override meets_req when domain is wrong or no experience
        if not domain_match or total_months == 0:
            meets_req = False

        return {
            "job_title": jd_title,
            "relevance_score": round(normalized, 3),
            "domain_match": domain_match,
            "total_experience_months": total_months,
            "meets_requirement": meets_req
        }
