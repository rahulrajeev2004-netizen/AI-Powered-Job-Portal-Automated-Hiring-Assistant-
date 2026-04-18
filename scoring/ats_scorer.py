import re
import math
import json
from typing import List, Dict, Any, Tuple

def normalize_skill(skill: str) -> str:
    s = str(skill).lower().strip()
    return re.sub(r'[^a-z0-9 ]', '', s)

def extract_skills_v28(cand_data: Dict, job_data: Dict):
    """
    Strict-Gated Extraction Engine (v28.0).
    """
    resume_text = str(cand_data.get("resume_text", "")).lower()
    c_skills = {normalize_skill(s) for s in cand_data.get("skills", [])}
    r_skills = [normalize_skill(s) for s in job_data.get("required_skills", [])]
    
    semantic_map = {
        "patient care": ["clinical care", "patient interaction", "bedside nursing", "treated patients"],
        "clinical assessment": ["patient assessment", "vital signs", "rounds", "clinical diagnosis"],
        "documentation": ["charting", "ehr", "medical records", "documentation"],
        "communication": ["liaised", "collaborated", "coordinated", "informed families"],
        "critical care": ["icu", "intensive care", "emergency care"],
        "empathy": ["compassion", "patient support", "comfort"]
    }

    explicit_m = []
    implied_m = []
    inferred_m = []
    
    for r in r_skills:
        if r in c_skills or r in resume_text:
            explicit_m.append(r)
            continue
        syns = semantic_map.get(r, [])
        if any(s in resume_text for s in syns):
            implied_m.append(r)
            continue
        if len(resume_text) > 400:
             inferred_m.append(r)

    total = len(r_skills) if len(r_skills) > 0 else 1
    return explicit_m, implied_m, inferred_m, total

def candidate_score_generator(candidate: Dict, job: Dict, semantic_similarity: float = 0.5):
    """
    Strict Gated Decision Engine (v28.0).
    Implements mandatory hiring gates and explicit evidence capping.
    """
    # 1. Extraction
    explicit_m, implied_m, inferred_m, total_req = extract_skills_v28(candidate, job)
    
    # 2. Coverage Metrics
    explicit_skill_coverage = len(explicit_m) / total_req
    implied_skill_coverage = (len(implied_m) + len(inferred_m)) / total_req
    core_skill_coverage = len(explicit_m + implied_m) / total_req
    
    # 3. Base Scoring (v24.0 Legacy)
    ey = float(candidate.get("experience_years", 0) or 0)
    ry = float(job.get("experience_required", 1.0) or 1.0)
    resume_text = str(candidate.get("resume_text", "")).lower()
    job_title_req = str(job.get("job_title", "")).lower()
    role_terms = [t for t in re.split(r'\W+', job_title_req) if len(t) > 3]
    
    skill_val = (len(explicit_m) * 1.0 + len(implied_m) * 0.6 + len(inferred_m) * 0.3) / total_req
    skill_score = min(skill_val, 1.0)
    
    if ey >= ry: exp_score = 1.0
    elif ey >= (ry * 0.5): exp_score = 0.7
    elif ey > 0: exp_score = 0.3
    else: exp_score = 0.0
    
    domain_match_count = sum(1 for t in role_terms if t in resume_text)
    domain_rel = 0.0
    if role_terms:
        ratio = domain_match_count / len(role_terms)
        if ratio > 0.6: domain_rel = 1.0
        elif ratio > 0.1: domain_rel = 0.6
    else: domain_rel = 0.6
    
    base_score = (skill_score * 0.4) + (exp_score * 0.3) + (domain_rel * 0.2) + (0.6 * 0.1)
    
    score_p = 0
    if core_skill_coverage < 0.5: score_p -= 0.15
    if explicit_skill_coverage == 0: score_p -= 0.10
    if domain_rel == 0: score_p -= 0.25
    
    final_score = base_score + score_p
    if ey >= 5 and domain_rel == 1.0: final_score += 0.10
    final_score = round(max(0, min(1, final_score)), 4)
    
    # 4. Confidence Calibration (v28.0)
    base_confidence = (0.5 * explicit_skill_coverage) + \
                      (0.3 * min(implied_skill_coverage, 1.0)) + \
                      (0.2 * domain_rel)
                      
    c_penalty = 0
    applied_p = []
    if explicit_skill_coverage == 0: 
        c_penalty -= 0.1
        applied_p.append("Low Explicit Skill Evidence")
    if core_skill_coverage < 0.6: 
        c_penalty -= 0.15
        applied_p.append("Missing Core Skills")
    if domain_rel == 0: 
        c_penalty -= 0.2
        applied_p.append("Domain Misalignment")
    if skill_val < 0.3: 
        c_penalty -= 0.1
        applied_p.append("High Reliance on Inferred Skills")
        
    # Variation epsilon
    epsilon = (len(resume_text) % 500) / 10000.0
    confidence_score = base_confidence + c_penalty + epsilon
    
    # CRITICAL CAP (Step 3)
    capped_confidence = round(min(confidence_score, explicit_skill_coverage + 0.2), 4)
    final_confidence = max(0, min(1, capped_confidence))
    
    # 5. Strict Decision Logic (Step 4)
    # GATE 1: final_score > 0.7 AND confidence > 0.6 AND core_coverage >= 0.6 AND explicit_coverage > 0
    if (final_score > 0.7 and final_confidence > 0.6 and core_skill_coverage >= 0.6 and explicit_skill_coverage > 0):
        status = "Shortlist"
    elif final_score > 0.5:
        status = "Review"
    else:
        status = "Reject"
        
    # Consistency check overrides (Step 1)
    if core_skill_coverage < 0.6 and status == "Shortlist": status = "Review"
    if explicit_skill_coverage == 0 and status == "Shortlist": status = "Review"
    if final_confidence < 0.5 and status == "Shortlist": status = "Review"

    # Risk level alignment (Step 6)
    if final_confidence >= 0.7: risk_level = "LOW"
    elif final_confidence >= 0.4: risk_level = "MODERATE"
    else: risk_level = "HIGH"

    # Explanation
    if status == "Shortlist":
        explanation = f"Verified candidate with strong technical coverage ({int(core_skill_coverage*100)}%) and reliable explicit evidence."
    elif status == "Review":
        reason = "missing explicit proof" if explicit_skill_coverage == 0 else "limited core coverage" if core_skill_coverage < 0.6 else "mixed evidentiary signals"
        explanation = f"Qualified background identified but retained in Review due to {reason}."
    else:
        explanation = "Profile rejected due to significant skill gaps or domain misalignment."

    return {
        "candidate_id": candidate.get("candidate_id"),
        "final_score": final_score,
        "normalized_score": 0.0,
        "confidence_score": final_confidence,
        "status": status,
        "risk_level": risk_level,
        "matched_skills": [f"{s} (explicit)" for s in explicit_m] + [f"{s} (implied)" for s in implied_m],
        "missing_skills": [s for s in job.get("required_skills", []) if normalize_skill(s) not in (explicit_m + implied_m)],
        "core_skill_coverage": round(core_skill_coverage, 2),
        "explicit_skill_coverage": round(explicit_skill_coverage, 2),
        "indicators": {"green_flags": ["Explicit Evidence"] if explicit_skill_coverage > 0.4 else [], "red_flags": applied_p[:2]},
        "explanation": explanation,
        "audit_trace": {
            "base_confidence": round(base_confidence, 4),
            "total_penalty": round(abs(c_penalty), 2),
            "capped_confidence": final_confidence,
            "core_gate_pass": core_skill_coverage >= 0.6,
            "explicit_gate_pass": explicit_skill_coverage > 0
        }
    }
