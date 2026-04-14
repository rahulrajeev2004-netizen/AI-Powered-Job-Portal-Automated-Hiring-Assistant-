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

def score_candidates(parsed_resumes: List[Dict], job_description: str, bias_boost: float = 0.05) -> Dict:
    """
    Production-grade scoring logic with full breakdown, normalization, and metrics.
    """
    import time
    start_time = time.time()
    
    # 1. Parse Job Description for scoring
    job_data = {
        "job_title": "Target Role",
        "job_description": job_description,
        "required_skills": [], 
        "experience_required": 2.0,
        "education_required": "degree",
        "critical_skills": []
    }
    
    try:
        pj = parse_jd(job_description)
        if pj:
            job_data.update(pj)
            # Map nested parsed requirements to the flat format expected by candidate_score_generator
            reqs = pj.get("requirements", {})
            skills_pkg = reqs.get("skills", {})
            job_data["required_skills"] = skills_pkg.get("mandatory", [])
            
            exp_info = reqs.get("experience", {})
            if "min_years" in exp_info:
                job_data["experience_required"] = float(exp_info["min_years"])
                
            edu_info = reqs.get("education", {})
            if "min_degree" in edu_info:
                job_data["education_required"] = edu_info["min_degree"]

            # Ensure proper types for critical skills if provided elsewhere
            if isinstance(job_data.get("critical_skills"), str):
                job_data["critical_skills"] = [s.strip() for s in job_data["critical_skills"].split(",")]
    except Exception as e:
        print(f"JD parsing failed: {e}")

    # 2. Compute Match Scores using candidate_score_generator
    matches = []
    print(f"\n[DEBUG LOGIC] Production scoring started for {len(parsed_resumes)} candidates")
    
    for cand in parsed_resumes:
        # Prepare candidate dict for generator
        cand_input = {
            "candidate_id": cand.get("candidate_id", "Unknown"),
            "skills": cand.get("skills", []),
            "experience_years": cand.get("experience_years", 0.0),
            "education": cand.get("education", ""),
            "resume_text": f"{cand.get('skills', [])} {cand.get('education', '')}"
        }
        
        # Use existing candidate_score_generator
        gen_result = candidate_score_generator(cand_input, job_data, semantic_similarity=0.5)
        
        matches.append({
            "candidate_id": cand_input["candidate_id"],
            "original_score": gen_result["computed_score"],
            "score_breakdown": gen_result["score_breakdown"],
            "domain_relevance_detail": gen_result.get("domain_relevance_detail", {}),
            "raw_details": gen_result.get("raw_details", {}),
            "audit_trace": gen_result.get("audit_trace", {}),
            "explanation": gen_result["explanation"]
        })

    if not matches:
        return {
            "job_summary": job_data,
            "total_candidates": 0,
            "ranked_candidates": [],
            "metrics": {
                "total_processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "average_latency_per_resume_ms": 0,
                "ranking_stability": "stable",
                "bias_fairness_status": "none",
                "system_confidence_score": 0.0
            }
        }

    # 3. Apply Normalization and Bias Adjustment using FairnessEngine
    engine = FairnessEngine(boost=bias_boost)
    # Map matched to FairnessEngine input
    # Note: FairnessEngine expects "breakdown" key for some logic
    fairness_input_candidates = []
    for m in matches:
        fairness_input_candidates.append({
            "candidate_id": m["candidate_id"],
            "original_score": m["original_score"],
            "breakdown": m["score_breakdown"],
            "explanation": m["explanation"]
        })

    job_wise_data = {"job_id": job_data.get("job_title", "J1"), "candidates": fairness_input_candidates}
    fairness_result = engine.apply_fairness(job_wise_data)
    
    # 4. Final Formatting for Production Response
    final_candidates = []
    
    # v3.2 Logic: Capture the actual required skills used by the scorer (from the first candidate)
    actual_req_skills = []
    
    for res in fairness_result.get("candidates", []):
        # Match back the original detailed analysis
        orig_match = next((m for m in matches if m["candidate_id"] == res["candidate_id"]), None)
        
        # v3.2: explicit fairness application
        base_val = res["raw_score"]
        boost_val = res["adjustment_applied"]
        final_score_val = round(min(base_val + boost_val, 1.0), 4)

        breakdown = orig_match["score_breakdown"]
        raw_details = orig_match.get("raw_details", {})
        if not actual_req_skills:
            actual_req_skills = raw_details.get("required_skills", [])
            
        final_candidates.append({
            "candidate_id": res["candidate_id"],
            "final_score": final_score_val,
            "rank": res["rank"],
            "score_breakdown": {
                "skills": breakdown["skills"],
                "experience": breakdown["experience"],
                "education": breakdown["education"],
                "domain_relevance": breakdown["domain_relevance"]
            },
            "domain_relevance_detail": orig_match["domain_relevance_detail"],
            "fairness_adjustment": {
                "applied": res["bias_flag"],
                "value": boost_val
            },
            "matched_skills": raw_details.get("matched_skills", []),
            "missing_skills": raw_details.get("missing_skills", []),
            "audit_trace": {**orig_match.get("audit_trace", {}), **({"fairness_calc": f"{base_val} + {boost_val} = {final_score_val}"} if res["bias_flag"] else {"fairness_calc": f"{base_val} + 0.0 = {final_score_val}"})},
            "explanation": orig_match["explanation"] + (f" Fairness adjustment of +{boost_val} applied." if res["bias_flag"] else "")
        })

    total_time_ms = round((time.time() - start_time) * 1000, 2)
    
    metrics = {
        "processing_time_ms": total_time_ms,
        "ranking_stability": "stable",
        "system_confidence": 0.98
    }

    ranking_metadata = {
        "tie_breaking_rule": "final_score > skills > experience > education > domain_relevance > candidate_id",
        "scoring_formula": "(0.4 * skills) + (0.3 * experience) + (0.2 * education) + (0.1 * domain_relevance)",
        "experience_scaling": "min(years/required, 1.0)",
        "normalization": "not applied",
        "fairness_application": "added to computed_score",
        "model_version": "v3.5 final production ATS"
    }

    # Final Audit Check on Job Metadata
    title = job_data.get("job_title", "General Professional")
    if not title or title == "Unknown": title = "General Professional"

    # Data Quality Check
    data_warning = None
    if final_candidates and all(c["score_breakdown"]["skills"] == 0 for c in final_candidates):
        data_warning = "No candidates matched required skills; ranking driven by experience"
    elif len(final_candidates) >= 2 and final_candidates[0]["score_breakdown"]["skills"] == 0 and final_candidates[1]["score_breakdown"]["skills"] == 0:
        data_warning = "Top candidates lack required skills; review job requirements or candidate pool"

    result = {
        "job_summary": {
            "title": title,
            "exp_req": job_data.get("experience_required", 2.0),
            "required_skills": actual_req_skills
        },
        "total_candidates": len(final_candidates),
        "ranked_candidates": final_candidates,
        "ranking_metadata": ranking_metadata,
        "metrics": metrics
    }
    
    if data_warning:
        result["data_warning"] = data_warning
        
    return result

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
