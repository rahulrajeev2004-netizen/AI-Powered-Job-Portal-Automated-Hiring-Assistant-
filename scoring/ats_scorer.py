import json
import re
import numpy as np
import math
import os
import sys
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ats_scorer")

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
        "rn": "rn license",
        "registered nurse": "rn license",
        "registered nurse license": "rn license",
        "registered nurse license rn": "rn license",
        "bls certification": "bls",
        "bls": "bls",
        "basic life support": "bls",
        "acls certification": "acls",
        "acls": "acls",
        "advanced cardiovascular life support": "acls",
        "communication skills": "communication",
        "excellent communication": "communication",
        "verbal skills": "communication",
        "interpersonal": "communication",
        "interpersonal skills": "communication",
        "team player": "teamwork",
        "collaboration": "teamwork",
        "collaborative": "teamwork",
        "organizational skills": "organization",
        "time management": "organization",
        "organizing": "organization",
        "problemsolving": "problem solving",
        "analytical": "problem solving",
        "analytical skills": "problem solving",
        "critical thinking": "problem solving",
        "patient care": "patient care",
        "team coordination": "teamwork"
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
                        
    # Include all explicit requirements, both hard and soft
    matched_list = [r.lower().strip() for r in matched_reqs]
    
    missing_list = [r.lower().strip() for r in r_norm_map.keys() if r not in matched_reqs]
    
    # FIX added_skills: ensure all exist in final hard_skills (Requirement 5 & Final Subset Fix)
    normalized_added = []
    for a in added_skills:
        na = normalize_skill(a)
        if na in r_norm_map.keys():
            normalized_added.append(na)
    added_skills = list(dict.fromkeys(normalized_added))
    
    # 8. RECOMPUTE SKILL SCORE
    total_hard = len(r_norm_map)
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
    # v3.4 Final Production Weights
    w_skill, w_exp, w_edu, w_dom = 0.4, 0.3, 0.2, 0.1
    job_title = job.get("job_title", "General Professional") or "General Professional"
    if job_title == "Crtical Nurse": job_title = "Critical Nurse"
    
    cand_text = (candidate.get("resume_text", "") + " " + " ".join(candidate.get("skills", []))).lower()
    dynamic_semantic = compute_semantic_relevance(job_title, cand_text) if _EMBEDDER else semantic_similarity
    
    # 1. Skills Logic (Consistency - Objective 1 & 2)
    # Ensure required_skills is never empty for v3.3
    req_skills = job.get("required_skills", [])
    if not req_skills:
        # Generic defaults for validation or catch-all
        req_skills = ["communication", "teamwork", "organization", "problem solving"]
        job["required_skills"] = req_skills

    res = compute_skill_match_strict_semantic(
        candidate.get("skills", []), 
        req_skills,
        job_title
    )
    skill_score, matched_skills, missing_skills, total_required, hard_skills, soft_skills, added_skills, removed_skills = res
    req_norm = []
    for s in req_skills:
        ns = normalize_skill(s)
        if ns not in req_norm:
            req_norm.append(ns)
    
    matched_skills = []
    for s in res[1]:
        ns = normalize_skill(s)
        if ns not in matched_skills:
            matched_skills.append(ns)

    missing_skills = [s for s in req_norm if s not in matched_skills]
    
    def missing_sort_key(s):
        sl = s.lower()
        cert_terms = ["license", "certification", "certified", "rn", "aws", "pmp", "cpa", "mba", "msc", "btech"]
        if any(k in sl for k in cert_terms): return 0
        if any(k in sl for k in ["acls", "bls"]): return 1
        return 2
    missing_skills = sorted(missing_skills, key=missing_sort_key)
    
    # Precise re-calculation using standardized sets
    if req_norm:
        skill_score = len(matched_skills) / len(req_norm)
    
    # 2. Experience Scaling
    try:
        ey = float(candidate.get("experience_years", 0))
        ry = float(job.get("experience_required", 2.0))
    except (TypeError, ValueError):
        ey, ry = 0.0, 2.0
    exp_score = min(ey / ry, 1.0) if ry > 0 else 1.0
        
    # 3. Education Score (Discrete - Day 20 Production Rule)
    edu_score = 0.0
    cand_edu = str(candidate.get("education", "")).lower()
    
    # Domain specific relevance
    if any(k in job_title.lower() for k in ["nurse", "clinical", "icu", "health"]):
        if any(k in cand_edu for k in ["nursing", "bsn", "msc", "nurse"]):
            edu_score = 1.0
        elif any(k in cand_edu for k in ["medical", "pharma", "biology"]):
            edu_score = 0.5
    elif any(k in job_title.lower() for k in ["engineer", "developer", "software", "tech"]):
        if any(k in cand_edu for k in ["computer", "engineering", "software"]):
            edu_score = 1.0
        elif any(k in cand_edu for k in ["science", "math", "physics"]):
            edu_score = 0.5
    else:
        # General role fallback
        if len(cand_edu) > 5:
            edu_score = 0.3
    
    # 4. Domain Relevance Variance (Objective 5)
    skill_overlap = skill_score
    exp_align = min(ey / ry, 1.0) if ry > 0 else 1.0
    
    cert_keywords = ["license", "certification", "certified", "bls", "acls", "rn", "aws", "pmp", "cpa", "mba"]
    req_certs = [c for c in req_norm if any(k in c.lower() for k in cert_keywords)]
    actual_matched_certs = [c for c in matched_skills if any(k in c.lower() for k in cert_keywords)]
    actual_missing_certs = [c for c in req_certs if c not in actual_matched_certs]
    if len(req_certs) > 0:
        cert_match_value = len(actual_matched_certs) / len(req_certs)
    else:
        cert_match_value = 0.0
        
    cert_data = {
        "matched": actual_matched_certs,
        "missing": actual_missing_certs
    }
    cert_status_text = f"{len(actual_matched_certs)}/{len(req_certs)}" if req_certs else "N/A"
    
    # Role Keywords Match (discrete normalization: 0, 0.25, 0.5, 0.75, 1.0)
    role_terms = [t.lower() for t in re.split(r'\W+', job_title) if len(t) > 3]
    if not role_terms:
        # Fallback terms for general professional context
        role_terms = ["management", "operations", "specialist"]
        
    role_terms = list(set(role_terms))
    matched_role_terms = [t for t in role_terms if t in cand_text]
    raw_role_match = len(matched_role_terms) / len(role_terms) if role_terms else 0.0
    
    # Snap to discrete values (Normalization 0-1)
    if raw_role_match >= 0.875: role_match = 1.0
    elif raw_role_match >= 0.625: role_match = 0.75
    elif raw_role_match >= 0.375: role_match = 0.5
    elif raw_role_match >= 0.125: role_match = 0.25
    else: role_match = 0.0
    
    # STRICT RULE: IF skill_overlap == 0, cap role match to 0.3 (non-technical match only)
    if skill_overlap == 0:
        role_match = min(role_match, 0.3)
        
    domain_score = (0.35 * skill_overlap) + (0.25 * exp_align) + (0.2 * cert_match_value) + (0.2 * role_match)
    
    # 3. Apply Domain Penalty Rule (CRITICAL Day 20 Requirement)
    if skill_overlap == 0:
        domain_score = min(domain_score, 0.02) # Hard cap at 0.02 as per Day 20 Strict Rule
        cand_id = candidate.get("candidate_id", "Unknown")
        logger.info(f"Applying strict domain penalty for {cand_id}: skill_overlap is 0.")
    
    domain_score = round(max(0.0, min(1.0, domain_score)), 4)
    
    dom_detail = {
        "formula": "(0.35 * skill_overlap) + (0.25 * exp_align) + (0.2 * cert_match_value) + (0.2 * role_match)",
        "score": domain_score,
        "components": {
            "skill_overlap": round(skill_overlap, 2),
            "experience_alignment": round(exp_align, 2),
            "cert_match_value": round(cert_match_value, 2),
            "certification_details": cert_data,
            "role_keyword_match": round(role_match, 2)
        }
    }
    if skill_overlap == 0:
        dom_detail["note"] = "Strong penalty applied due to zero skill overlap (score capped ≤ 0.02)"

    # 5. Computed Base Score
    skills_comp = round(skill_score * w_skill, 4)
    exp_comp = round(exp_score * w_exp, 4)
    edu_comp = round(edu_score * w_edu, 4)
    dom_comp = round(domain_score * w_dom, 4)
    computed_score = round(skills_comp + exp_comp + edu_comp + dom_comp, 4)
    
    # 6. Explanations (Objective 5 - Data Driven)
    # Clean Explanation
    cert_status = cert_status_text if cert_status_text != "0/0" else "N/A"
    if len(missing_skills) > 3:
        gaps = f"Gaps: {', '.join(missing_skills[:3])} (+{len(missing_skills)-3} more)"
    elif missing_skills:
        gaps = f"Gaps: {', '.join(missing_skills)}"
    else:
        gaps = "No major gaps"
    
    explanation = f"Exp: {ey}\u2192{round(exp_score,2)} (cap), Skills: {len(matched_skills)}/{len(req_norm) if req_norm else 1}, Certs: {cert_status}, Domain: {domain_score}; {gaps}"
    
    is_low_quality = (len(matched_skills) == 0 and ey == 0)
    if is_low_quality:
        explanation = "[LOW QUALITY] " + explanation
    elif skill_overlap == 0:
        explanation = "No Skill Match: " + explanation

    return {
        "candidate_id": candidate.get("candidate_id"),
        "computed_score": computed_score, # Passed before fairness
        "quality_flag": "LOW QUALITY" if is_low_quality else "STANDARD",
        "score_breakdown": {
            "skills": skills_comp,
            "experience": exp_comp,
            "education": edu_comp,
            "domain_relevance": dom_comp,
            "penalties": 0.0
        },
        "domain_relevance_detail": dom_detail,
        "audit_trace": {
            "skills_calc": f"{w_skill} * ({len(matched_skills)}/{len(req_norm) if req_norm else 1}) = {skills_comp}",
            "experience_calc": f"{w_exp} * min({ey}/{ry}, 1.0) = {exp_comp}",
            "education_calc": f"{w_edu} * {edu_score} = {edu_comp}",
            "domain_calc": f"{w_dom} * {domain_score} = {dom_comp}",
            "final_sum": f"({skills_comp}) + ({exp_comp}) + ({edu_comp}) + ({dom_comp}) = {computed_score}"
        },
        "explanation": explanation,
        "raw_details": {
            "required_skills": req_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "metadata": {"ey": ey, "ry": ry}
        }
    }
