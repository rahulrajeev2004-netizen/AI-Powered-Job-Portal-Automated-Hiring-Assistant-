import os
import sys
import json
from typing import List, Dict, Any

# Ensure project root is in path for existing modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from scoring.ats_scorer import candidate_score_generator
from scoring.fairness_engine import FairnessEngine
from parsers.resume_segmenter import segment_resume, SKILLS, WORK_EXPERIENCE, EDUCATION, SUMMARY
from parsers.pdf_parser import extract_text_from_pdf
from parsers.jd_parser import parse_jd
from engines.skill_extractor.skill_extractor import SkillExtractor
from engines.experience_analyzer.experience_analyzer import ExperienceAnalyzer

# Path to master skills
SKILLS_DICT_PATH = os.path.join(project_root, "data", "skills", "master_skills.json")

# Lazy initialization
_SKILL_EXTRACTOR = None
_EXP_ANALYZER = None

def get_skill_extractor():
    global _SKILL_EXTRACTOR
    if _SKILL_EXTRACTOR is None:
        if os.path.exists(SKILLS_DICT_PATH):
            _SKILL_EXTRACTOR = SkillExtractor(SKILLS_DICT_PATH)
        else:
            print(f"Warning: Skills dictionary not found at {SKILLS_DICT_PATH}")
    return _SKILL_EXTRACTOR

def get_experience_analyzer():
    global _EXP_ANALYZER
    if _EXP_ANALYZER is None:
        _EXP_ANALYZER = ExperienceAnalyzer(current_date="2026-04")
    return _EXP_ANALYZER

def score_candidates(parsed_resumes: List[Dict], job_description: str, bias_boost: float = 0.05) -> List[Dict]:
    """
    Core logic to score, normalize, adjust for bias, and rank candidates.
    
    Args:
        parsed_resumes: List of dictionaries with resume data (skills, experience, etc.)
        job_description: The job description text
        bias_boost: Configurable bias adjustment boost
        
    Returns:
        List of candidates with original_score, normalized_score, adjusted_score, and rank.
    """
    # 1. Parse Job Description for scoring
    job_data = {
        "job_title": "Target Role",
        "job_description": job_description,
        "required_skills": [], 
        "experience_required": 2,
        "education_required": "degree"
    }
    
    # Try to parse JD
    try:
        pj = parse_jd(job_description)
        if pj:
            job_data.update(pj)
            if isinstance(job_data.get("required_skills"), str):
                job_data["required_skills"] = [s.strip() for s in job_data["required_skills"].split(",")]
    except Exception as e:
        print(f"JD parsing failed: {e}")

    # 2. Compute Original Scores
    import random
    matches = []
    print(f"\n[DEBUG LOGIC] Scoring started for Job ID: {job_data.get('job_title')}")
    
    # Extract requirement values for matching
    required_skills = set([s.lower() for s in job_data.get("required_skills", [])])
    req_exp = float(job_data.get("experience_required", 2.0)) or 1.0 # Avoid div by zero
    
    for cand in parsed_resumes:
        # A. Skill Match (0.5 weight)
        cand_skills = cand.get("skills", [])
        if isinstance(cand_skills, str):
            cand_skills = [s.strip() for s in cand_skills.split("\n") if s.strip()]
        
        cand_skill_set = set([s.lower() for s in cand_skills])
        if required_skills:
            skill_match = len(required_skills.intersection(cand_skill_set)) / len(required_skills)
        else:
            skill_match = 0.5 # Default if no skills required
            
        # B. Experience Match (0.3 weight)
        cand_exp = float(cand.get("experience_years", 0.0))
        experience_match = min(1.0, cand_exp / req_exp)
        
        # C. Education Match (0.2 weight)
        # Simple string match for 'degree' or 'education'
        edu_str = str(cand.get("education", "")).lower()
        edu_req = str(job_data.get("education_required", "degree")).lower()
        education_match = 1.0 if edu_req in edu_str else 0.0
        
        # FINAL FORMULA: (0.5 * skills) + (0.3 * exp) + (0.2 * edu)
        formula_score = (skill_match * 0.5) + (experience_match * 0.3) + (education_match * 0.2)
        
        # D. Add small random variation (0.01 - 0.05) to ensure NO TIES
        # This keeps scores realistic but guarantees variation for ranking
        variation = random.uniform(0.01, 0.05)
        original_score = round(formula_score + variation, 4)

        matches.append({
            "candidate_id": cand.get("candidate_id", "Unknown"),
            "original_score": original_score
        })

    if not matches:
        print("[DEBUG LOGIC] No candidates found.")
        return []

    # 3. Apply Normalization and Bias Adjustment
    # FairnessEngine handles MANDATORY debug logs (Original Scores, Min, Max)
    engine = FairnessEngine(boost=bias_boost)
    job_wise_data = {"job_id": job_data.get("job_title", "J1"), "candidates": matches}
    fairness_result = engine.apply_fairness(job_wise_data)
    
    print(f"[DEBUG LOGIC] Scoring completed. Final Results: {len(fairness_result.get('candidates', []))}\n")
    return fairness_result.get("candidates", [])

def parse_resume_task(file_path: str) -> Dict[str, Any]:
    """
    Task to parse a resume and extract skills/experience using dedicated engines.
    """
    raw_text = ""
    if file_path.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
    if not raw_text:
        raise ValueError("Failed to extract text from resume")
        
    segmented = segment_resume(raw_text)
    
    # Extract Skills
    extractor = get_skill_extractor()
    if extractor:
        context = f"{segmented.get(SKILLS, '')}\n{segmented.get(SUMMARY, '')}\n{segmented.get(WORK_EXPERIENCE, '')}"
        extracted = extractor.extract_skills(context, section_context="skills")
        segmented["extracted_skills"] = [s["skill"] for s in extracted]
    else:
        segmented["extracted_skills"] = []

    # Analyze Experience Years
    analyzer = get_experience_analyzer()
    exp_text = segmented.get(WORK_EXPERIENCE, "")
    if analyzer and exp_text:
        try:
            exp_results = analyzer.analyze(exp_text, {"required_skills": []})
            segmented["experience_years"] = round(exp_results.get("total_experience_months", 0) / 12.0, 1)
        except Exception:
            segmented["experience_years"] = 0.0
    else:
        segmented["experience_years"] = 0.0

    return segmented
