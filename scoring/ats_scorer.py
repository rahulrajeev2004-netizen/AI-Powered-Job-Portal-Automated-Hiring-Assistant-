import json
import re
import numpy as np
from typing import List, Dict, Any, Optional
import os
import sys

# Optional: Add project root to path for Embedder access
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Try to import project embedder
try:
    from semantic_matching.embedder import Embedder
    _EMBEDDER = Embedder()
except ImportError:
    _EMBEDDER = None

def normalize_skill(skill: str) -> str:
    s = str(skill).lower().strip()
    s = s.replace("skills", "").strip()
    s = re.sub(r'[^\w\s]', '', s).strip()
    syn_map = {
        "rn": "registered nurse license (rn)",
        "registered nurse license": "registered nurse license (rn)",
        "registered nurse license rn": "registered nurse license (rn)",
        "bls": "basic life support (bls)",
        "basic life support": "basic life support (bls)",
        "basic life support bls": "basic life support (bls)",
        "acls": "advanced cardiovascular life support (acls)",
        "advanced cardiovascular life support": "advanced cardiovascular life support (acls)",
        "advanced cardiovascular life support acls": "advanced cardiovascular life support (acls)",
        "communication skills": "communication",
        "problemsolving": "problem-solving",
        "problemsolving ability": "problem-solving",
        "critical care": "critical care nursing",
        "icu care": "critical care nursing",
        "patient support": "patient care",
        "emergency handling": "emergency response",
        "iv": "iv therapy"
    }
    return syn_map.get(s, s)

def is_valid_skill(skill: str) -> bool:
    s = str(skill).lower().strip()
    if not s or len(s) < 2 or len(s.split()) > 3: return False
    
    # DO NOT REMOVE VALID MEDICAL SKILLS (Requirement 4)
    whitelist = ["basic life support", "bls", "advanced cardiovascular life support", "acls", "registered nurse license", "rn license", "rn", "clinical documentation"]
    if any(w in s for w in whitelist): return True

    # Strict list of forbidden concepts (Requirement 1 & 2 - Environment Neutralization)
    forbidden = {"hospital", "clinic", "school", "college", "university", "institute", "institution", "center", "facility", "insurance", "ambulance", "theatre", "department", "unit", "home", "ship", "defense", "public health", "camp", "camps", "services", "zone", "zones", "disaster", "pharmaceutical", "setting"}
    for term in forbidden:
        if term in s: return False
    return True

def is_soft_skill(skill: str) -> bool:
    soft_indicators = ["team coordination", "communication", "teamwork", "problem-solving", "problem solving", "problemsolving", "analytical", "analytical thinking", "emotional resilience", "compassion", "patience", "empathy", "leadership", "time management", "adaptability", "writing", "thinking", "attention to detail", "attention", "detail", "listening", "interpersonal", "critical thinking", "observation"]
    s = str(skill).lower().strip()
    return any(ind in s for ind in soft_indicators)

def get_cosine_similarity(vec1, vec2):
    if vec1.size == 0 or vec2.size == 0: return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-9)

def compute_skill_match_strict_semantic(cand_skills: List[str], req_skills: List[str], job_title: str):
    added_skills = []
    removed_skills = []
    
    # 1. Normalize & Filter
    c_norm_map = {}
    r_norm_map = {}
    def process_and_add(skill_list, target_map, rem_list):
        for s in skill_list:
            sl = s.lower().strip()
            # Generalized split patterns
            split_indicators = [" and ", " & ", " and ", "/"]
            parts = [s]
            if any(ind in sl for ind in ["compassion and empathy", "communication and counseling", "patience and empathy", "patience and adaptability"]):
                parts = sl.replace(" and ", " & ").split(" & ")
            
            for p in parts:
                p = p.strip()
                if is_valid_skill(p):
                    target_map[normalize_skill(p)] = p.lower().strip()
                else:
                    rem_list.append(p.lower().strip())
                    
    process_and_add(cand_skills, c_norm_map, removed_skills)
    process_and_add(req_skills, r_norm_map, removed_skills)
            
    # Domain skill enrichment
    jt_lower = job_title.lower()
    auto_add = []
    
    if jt_lower == "critical care nurse" or "critical care" in jt_lower:
        auto_add.extend(["icu care", "ventilator management", "hemodynamic monitoring", "critical care nursing"])
    elif "patient care nurse" in jt_lower:
        auto_add.extend(["patient care", "clinical procedures", "basic nursing care"])
    elif any(k in jt_lower for k in ["nicu", "neonatal"]):
        auto_add.extend(["neonatal care", "ventilator support"])
    elif "cardiac" in jt_lower:
        auto_add.extend(["ecg", "cardiac monitoring"])
    elif "school nurse" in jt_lower:
        auto_add.extend(["child care", "first aid", "basic health assessment"])
        
    if "nurse" in jt_lower:
        if "patient care" not in auto_add:
            auto_add.append("patient care")
        
    for s in auto_add:
        ns = normalize_skill(s)
        if ns not in r_norm_map:
            r_norm_map[ns] = s
            added_skills.append(s)
            
    # Restore protected skills
    protected = ["basic life support (bls)", "basic life support", "bls", "advanced cardiovascular life support (acls)", "advanced cardiovascular life support", "acls", "registered nurse license (rn)", "registered nurse license", "rn license"]
    for rs in list(removed_skills):
        rs_lower = rs.lower()
        if any(p in rs_lower for p in protected):
            removed_skills.remove(rs)
            ns = normalize_skill(rs)
            r_norm_map[ns] = ns

    # 3. Separate Hard and Soft Skills (Requirement 3)
    r_hard = [r for r in r_norm_map.keys() if not is_soft_skill(r)]
    
    # 4. PROTECTED SKILLS IN HARD (Requirement 4)
    # If missing, ADD them. If in removed, MOVE them back.
    protected_actual = ["basic life support (bls)", "advanced cardiovascular life support (acls)", "registered nurse license (rn)"]
    if "nurse" in jt_lower or "rn" in jt_lower:
        for p in protected_actual:
            ns = normalize_skill(p)
            if ns not in r_hard:
                r_norm_map[ns] = p
                r_hard.append(ns)
                added_skills.append(p)
    
    # Auto-expand to reach >= 3 hard skills (Domain Requirement 3)
    if len(r_hard) < 3:
        if "nurse" in jt_lower or "rn" in jt_lower:
            generic_add = ["patient care", "clinical procedures", "documentation"]
            for s in generic_add:
                ns = normalize_skill(s)
                if ns not in r_hard and len(r_hard) < 3:
                    r_norm_map[ns] = s
                    r_hard.append(ns)
                    added_skills.append(s.lower().strip())
                    
    if not r_hard: r_hard = list(r_norm_map.keys()) # Fallback if all are soft
    
    r_soft = [r for r in r_norm_map.keys() if is_soft_skill(r)]
    
    matched_reqs = set()
    actual_candidate_matches = set()
    
    # 2. Exact & Synonym Match
    c_norm_set = set(c_norm_map.keys())
    for r in r_norm_map.keys():
        if r in c_norm_set:
            matched_reqs.add(r)
            actual_candidate_matches.add(c_norm_map[r])
            
    # 3. Strict 0.75 Semantic Match
    if _EMBEDDER and len(matched_reqs) < len(r_norm_map):
        rem_req = [r for r in r_norm_map.keys() if r not in matched_reqs]
        rem_cand = [c for c in c_norm_set if c not in matched_reqs]
        if rem_req and rem_cand:
            r_vecs = _EMBEDDER.get_embeddings(rem_req)
            c_vecs = _EMBEDDER.get_embeddings(rem_cand)
            for i, rv in enumerate(r_vecs):
                for j, cv in enumerate(c_vecs):
                    if get_cosine_similarity(rv, cv) >= 0.75:
                        matched_reqs.add(rem_req[i])
                        actual_candidate_matches.add(c_norm_map[rem_cand[j]])
                        break
                        
    # Filtering soft skills explicitly from outputs (Requirement 6 & 7 & 9)
    # intersection(candidate_skills, hard_skills)
    matched_reqs_hard = [r for r in matched_reqs if r in r_hard]
    matched_list = [r.lower().strip() for r in matched_reqs_hard]
    
    # missing_skills = hard_skills - matched_skills
    # REVERT: Certifications should be in missing_skills if not matched (Requirement 1 & 2)
    missing_list = [r.lower().strip() for r in r_hard if r not in matched_reqs_hard]
    
    # FIX added_skills: ensure all exist in final hard_skills (Requirement 5 & Final Subset Fix)
    normalized_added = []
    for a in added_skills:
        na = normalize_skill(a)
        if na in r_hard:
            normalized_added.append(na)
    added_skills = list(dict.fromkeys(normalized_added))
    
    # 8. RECOMPUTE SKILL SCORE
    total_hard = len(r_hard)
    skill_score = len(matched_list) / total_hard if total_hard > 0 else 0.0
    
    total_required = total_hard
    hard_skills_list = [r.lower().strip() for r in r_hard]
    soft_skills_list = [r.lower().strip() for r in r_soft]
    
    return skill_score, matched_list, missing_list, total_required, hard_skills_list, soft_skills_list, added_skills, removed_skills

def compute_semantic_relevance(job_title: str, candidate_text: str) -> float:
    if not _EMBEDDER:
        return 0.5
    try:
        j_vec = _EMBEDDER.get_embeddings(job_title)
        c_vec = _EMBEDDER.get_embeddings(candidate_text[:500])  # Use first 500 chars 
        if len(j_vec) > 0 and len(c_vec) > 0:
            return float(get_cosine_similarity(j_vec[0], c_vec[0]))
    except Exception:
        pass
    return 0.5

def candidate_score_generator(candidate: Dict, job: Dict, semantic_similarity: float):
    # Requirement 5: Updated Formula Weights
    w = {"skill": 0.4, "exp": 0.2, "edu": 0.1, "sem": 0.3}
    job_title = job.get("job_title", "Unknown")
    
    cand_text = candidate.get("resume_text", "") + " " + candidate.get("role", "")
    dynamic_semantic = compute_semantic_relevance(job_title, cand_text) if _EMBEDDER else semantic_similarity
    
    res = compute_skill_match_strict_semantic(
        candidate.get("skills", []), 
        job.get("required_skills", []),
        job_title
    )
    skill_score, matched_skills, missing_skills, total_required, hard_skills, soft_skills, added_skills, removed_skills = res
    
    # 6. SEMANTIC CONSISTENCY FIX
    diff = abs(skill_score - dynamic_semantic)
    consistency_flag = True if diff > 0.4 else False
    
    # Experience (Scaled Requirement 3)
    try:
        ey = float(candidate.get("experience_years", 0))
        ry = float(job.get("experience_required", 2))
    except (TypeError, ValueError):
        ey, ry = 0.0, 2.0
    exp_score = min(ey / ry, 1.0) if ry > 0 else 1.0
    
    # 7. EXPERIENCE ADJUSTMENT
    exp_explanation = ""
    if skill_score < 0.4:
        exp_score = exp_score * 0.5
        exp_explanation = " (experience reduced due to low skill match)"
        
    # Education (Partial scoring Requirement 3)
    ce = str(candidate.get("education", "")).lower()
    re = str(job.get("education_required", "")).lower()
    if not ce or not re:
        edu_score = 0.0
    else:
        # Partial match logic
        if re in ce: edu_score = 1.0
        elif "degree" in ce or "bachelor" in ce or "nurse" in ce: edu_score = 0.7
        else: edu_score = 0.3
    
    base = (skill_score * w["skill"]) + (exp_score * w["exp"]) + (edu_score * w["edu"]) + (dynamic_semantic * w["sem"])
    
    pen = []
    # 5. PENALTY FIX: only missing hard skills
    crit = [normalize_skill(s) for s in job.get("critical_skills", []) if is_valid_skill(s)]
    m_set_norm = set(normalize_skill(s) for s in matched_skills)
    for c in crit:
        if c not in m_set_norm and not is_soft_skill(c):
            pen.append({"reason": f"Missing critical: {c}", "impact": -0.03})
            
    jt_lower = job_title.lower()
    # Soften domain penalty if semantic is high
    domain_penalty = -0.05 if dynamic_semantic > 0.5 else -0.08
    
    if any(spec in jt_lower for spec in ["nicu", "neonatal", "pediatric"]):
        if not any("pediatric" in s or "neonatal" in s for s in m_set_norm):
            pen.append({"reason": "Domain gap: Pediatric/Neonatal Care", "impact": domain_penalty})
    if any(spec in jt_lower for spec in ["icu", "intensive care", "cardiac"]):
        if not any(x in s for x in ["critical", "icu", "cardiac"] for s in m_set_norm):
            pen.append({"reason": "Domain gap: Intensive/Cardiac Care", "impact": domain_penalty})
    if any(spec in jt_lower for spec in ["crna", "anesthetist"]):
        if not any("anesthesia" in s or "pharmacology" in s for s in m_set_norm):
            pen.append({"reason": "Domain gap: Anesthesia Support", "impact": domain_penalty})
            
    # Remove duplicates
    unique_pen = []
    seen_reasons = set()
    for p in pen:
        if p["reason"] not in seen_reasons:
            seen_reasons.add(p["reason"])
            unique_pen.append(p)
    pen = unique_pen
    
    # 5. PENALTY NORMALIZATION (cap at -0.1)
    total_penalty = sum(p["impact"] for p in pen)
    total_penalty = max(total_penalty, -0.1)
    
    final_score = base + total_penalty
    final_score = round(max(0.0, min(1.0, final_score)), 2)
    
    # Semantic Consistency (Requirement Final): true if semantic_score >= 0.5
    consistency_flag = True if dynamic_semantic >= 0.5 else False
    
    # 8. MATCH LEVEL CORRECTION
    if final_score >= 0.75:
        match_level = "Strong Match"
    elif final_score >= 0.60:
        match_level = "Moderate Match"
    else:
        match_level = "Weak Match"

    # Requirement: Exclude protected skills from explanation total (Final FIX)
    protected_norm = ["basic life support (bls)", "advanced cardiovascular life support (acls)", "registered nurse license (rn)"]
    hard_no_protected = [h for h in hard_skills if h not in protected_norm]
    total_no_protected = len(hard_no_protected)
    matches_no_protected = len([m for m in matched_skills if normalize_skill(m) in hard_no_protected])
    
    strengths_list = []
    if exp_score >= 0.4: strengths_list.append("relevant experience" + exp_explanation)
    if dynamic_semantic > 0.6: strengths_list.append("high role relevance")
    strengths_str = " and ".join(strengths_list) if strengths_list else "background details"

    missing_tech = [m for m in missing_skills]
    missing_str = ", ".join(missing_tech[:3]) if missing_tech else "none"

    explanation = f"Final Match Score: {final_score}. Candidate matches {matches_no_protected}/{total_no_protected} core skills (excluding certifications). Strengths: {strengths_str}. Missing technical skills: {missing_str}."

    return {
        "job_title": job_title,
        "final_score": final_score,
        "match_level": match_level,
        "score_breakdown": {
            "skill": {
                "score": round(skill_score, 2),
                "hard_skills": hard_skills,
                "soft_skills": soft_skills,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "added_skills": added_skills,
                "removed_skills": removed_skills
            },
            "experience": {"score": round(exp_score, 2), "years": ey, "required": ry},
            "education": {"score": round(edu_score, 2)},
            "semantic": {
                "score": round(dynamic_semantic, 2),
                "consistency_flag": consistency_flag
            },
            "total_penalty": round(total_penalty, 2)
        },
        "penalties_applied": pen,
        "explanation": explanation
    }
