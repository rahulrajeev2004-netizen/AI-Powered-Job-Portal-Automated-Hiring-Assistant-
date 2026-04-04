import numpy as np
import re
from typing import List, Dict, Any, Optional

class Scorer:
    def __init__(self, embedder=None):
        self.embedder = embedder

    def normalize_skill(self, skill: str) -> str:
        s = str(skill).lower().strip()
        s = s.replace("skills", "").strip()
        s = re.sub(r'[^\w\s]', '', s).strip()
        syns = {
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
        return syns.get(s, s)

    def is_valid_skill(self, skill: str) -> bool:
        s = str(skill).lower().strip()
        if not s or len(s) < 2 or len(s.split()) > 3: return False
        
        # DO NOT REMOVE VALID MEDICAL SKILLS
        whitelist = ["basic life support", "bls", "advanced cardiovascular life support", "acls", "registered nurse license", "rn license", "rn", "clinical documentation"]
        if any(w in s for w in whitelist): return True

        # STRICT list of forbidden concepts (Environment Neutralization)
        forbidden = {"hospital", "clinic", "school", "college", "university", "institute", "center", "facility", "insurance", "ambulance", "theatre", "department", "unit", "home", "ship", "defense", "public health", "zone", "zones", "disaster", "institution", "pharmaceutical", "setting"}
        for term in forbidden:
            if term in s: return False
        return True

    def is_soft_skill(self, skill: str) -> bool:
        soft_indicators = ["team coordination", "communication", "teamwork", "problem-solving", "problem solving", "problemsolving", "analytical", "analytical thinking", "emotional resilience", "compassion", "patience", "empathy", "leadership", "time management", "adaptability", "writing", "thinking", "attention to detail", "attention", "detail", "listening", "interpersonal", "critical thinking", "observation"]
        s = str(skill).lower().strip()
        return any(ind in s for ind in soft_indicators)

    def compute_semantic_relevance(self, job_title: str, candidate_text: str) -> float:
        if not self.embedder:
            return 0.5
        try:
            j_vec = self.embedder.get_embeddings(job_title)
            c_vec = self.embedder.get_embeddings(candidate_text[:500])
            if len(j_vec) > 0 and len(c_vec) > 0:
                sim = np.dot(j_vec[0], c_vec[0])
                return float(sim)
        except Exception:
            pass
        return 0.5

    def calculate_match_scores(self, resume_data: Dict[str, Any], jd_data: Dict[str, Any], semantic_score: float = 0.5):
        """
        STRICT Refined ATS Scorer (Requirement 11).
        Pipeline: Normalize -> Exact -> Synonym -> Semantic (Embeddings) at 0.75 ONLY.
        """
        job_title = jd_data.get("job_title", "Unknown Role")
        
        # Requirement 5: Balanced Formula Weights
        weights = {"skill": 0.4, "experience": 0.2, "education": 0.1, "semantic": 0.3}

        # Dynamic Semantic Variation
        cand_text = resume_data.get("resume_text", "") + " " + resume_data.get("role", "")
        dynamic_semantic = self.compute_semantic_relevance(job_title, cand_text) if self.embedder else semantic_score

        raw_cand = resume_data.get("skills", [])
        raw_req = jd_data.get("required_skills", []) or jd_data.get("requirements", {}).get("skills", {}).get("mandatory", [])
        
        # Step 1: Normalize & Filter
        c_norm_map = {}
        r_norm_map = {}
        removed_skills = []
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
                    if self.is_valid_skill(p):
                        target_map[self.normalize_skill(p)] = p.lower().strip()
                    else:
                        rem_list.append(p.lower().strip())
                        rem_list.append(p.lower().strip())
                        
        process_and_add(raw_cand, c_norm_map, removed_skills)
        process_and_add(raw_req, r_norm_map, removed_skills)

        # Domain skill enrichment
        jt_lower = job_title.lower()
        added_skills = []
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
            ns = self.normalize_skill(s)
            if ns not in r_norm_map:
                r_norm_map[ns] = s
                added_skills.append(s)
                
        # CRITICAL RULE: Restore protected skills if they were removed
        protected = ["basic life support (bls)", "basic life support", "bls", "advanced cardiovascular life support (acls)", "advanced cardiovascular life support", "acls", "registered nurse license (rn)", "registered nurse license", "rn license"]
        for rs in list(removed_skills):
            rs_lower = rs.lower()
            if any(p in rs_lower for p in protected):
                removed_skills.remove(rs)
                ns = self.normalize_skill(rs)
                r_norm_map[ns] = ns

        # 3. Separate Hard and Soft Skills (Requirement 3)
        r_hard = [r for r in r_norm_map.keys() if not self.is_soft_skill(r)]
        
        # 4. PROTECTED SKILLS IN HARD (Requirement 4)
        protected_actual = ["basic life support (bls)", "advanced cardiovascular life support (acls)", "registered nurse license (rn)"]
        if "nurse" in jt_lower or "rn" in jt_lower:
            for p in protected_actual:
                ns = self.normalize_skill(p)
                if ns not in r_hard:
                    r_norm_map[ns] = p
                    r_hard.append(ns)
                    added_skills.append(p)
        
        # Auto-expand to reach >= 3 hard skills
        if len(r_hard) < 3:
            if "nurse" in jt_lower or "rn" in jt_lower:
                generic_add = ["patient care", "clinical procedures", "documentation"]
                for s in generic_add:
                    ns = self.normalize_skill(s)
                    if ns not in r_hard and len(r_hard) < 3:
                        r_norm_map[ns] = s.lower().strip()
                        r_hard.append(ns)
                        added_skills.append(s.lower().strip())
                        
        if not r_hard: r_hard = list(r_norm_map.keys())
        r_soft = [r for r in r_norm_map.keys() if self.is_soft_skill(r)]
        
        matched_reqs = set()
        actual_candidate_matches = set()
        
        # Step 3 & 4: Exact & Synonym Match
        c_norm_set = set(c_norm_map.keys())
        for r in r_norm_map.keys():
            if r in c_norm_set:
                matched_reqs.add(r)
                actual_candidate_matches.add(c_norm_map[r])

        # Step 5: STRICT 0.75 Semantic Match (Embeddings)
        if self.embedder and len(matched_reqs) < len(r_norm_map):
            rem_req = [rs for rs in r_norm_map.keys() if rs not in matched_reqs]
            rem_cand = [cs for cs in c_norm_set if cs not in matched_reqs]
            
            if rem_req and rem_cand:
                req_vecs = self.embedder.get_embeddings(rem_req)
                cand_vecs = self.embedder.get_embeddings(rem_cand)
                
                for i, r_vec in enumerate(req_vecs):
                    for j, c_vec in enumerate(cand_vecs):
                        sim = np.dot(r_vec, c_vec)
                        if sim >= 0.75:
                            matched_reqs.add(rem_req[i])
                            actual_candidate_matches.add(c_norm_map[rem_cand[j]])
                            break

        # Filtering soft skills explicitly from outputs (Requirement 6, 7 & 9)
        # matched_skills = intersection(candidate_skills, hard_skills)
        matched_reqs_hard = [r for r in matched_reqs if r in r_hard]
        matched_list = [r.lower().strip() for r in matched_reqs_hard]
        
        # missing_skills = hard_skills - matched_skills
        # REVERT: Certifications should be in missing_skills if not matched (Requirement 1 & 2)
        missing_skills = [r.lower().strip() for r in r_hard if r not in matched_reqs_hard]
        
        # FIX added_skills: ensure all exist in final hard_skills (Requirement 5 & Final Subset Fix)
        normalized_added = []
        for a in added_skills:
            na = self.normalize_skill(a)
            if na in r_hard:
                normalized_added.append(na)
        added_skills = list(dict.fromkeys(normalized_added))
        
        # 8. RECOMPUTE SKILL SCORE
        total_hard = len(r_hard)
        skill_score = len(matched_list) / total_hard if total_hard > 0 else 0.0
        
        total_required = total_hard
        hard_skills_list = [r.lower().strip() for r in r_hard]
        soft_skills_list = [r.lower().strip() for r in r_soft]

        # Semantic Consistency (Requirement Final): true if semantic_score >= 0.5
        consistency_flag = True if dynamic_semantic >= 0.5 else False

        # Experience (Scaled Requirement 3)
        try:
            exp_years = float(resume_data.get("experience_years", 0))
            req_years = float(jd_data.get("experience_required", 2) or jd_data.get("requirements", {}).get("experience", {}).get("min_years", 2))
        except (TypeError, ValueError):
            exp_years, req_years = 0.0, 2.0
        experience_score = min(exp_years / req_years, 1.0) if req_years > 0 else 1.0

        # 4. EXPERIENCE ADJUSTMENT
        exp_explanation = ""
        if skill_score < 0.4:
            experience_score = experience_score * 0.5
            exp_explanation = " (experience adjusted due to low skill match)"

        # Education (Partial scoring Requirement 3)
        cand_edu = str(resume_data.get("education", "")).lower()
        req_edu = str(jd_data.get("education_required", "") or jd_data.get("requirements", {}).get("education", {}).get("min_degree", "")).lower()
        if not cand_edu or not req_edu:
            edu_score = 0.0
        else:
            if req_edu in cand_edu: edu_score = 1.0
            elif "degree" in cand_edu or "nurse" in cand_edu: edu_score = 0.7
            else: edu_score = 0.3

        # Weighted Base
        weighted_base = (
            (skill_score * weights["skill"]) +
            (experience_score * weights["experience"]) +
            (edu_score * weights["education"]) +
            (dynamic_semantic * weights["semantic"])
        )

        penalties = []
        # 5. PENALTY FIX: only missing hard skills
        crit = [self.normalize_skill(s) for s in (jd_data.get("critical_skills", []) or (jd_data.get("requirements", {}).get("skills", {}).get("mandatory", []) or [])[:2])]
        m_set = set(self.normalize_skill(s) for s in matched_list)
        for c in crit:
            if c not in m_set and not self.is_soft_skill(c):
                penalties.append({"reason": f"Missing critical: {c}", "impact": -0.03})
                
        # Domain softening (Requirement 7)
        dom_pen = -0.05 if dynamic_semantic > 0.5 else -0.10
        
        if any(spec in jt_lower for spec in ["nicu", "neonatal", "pediatric"]):
            if not any("pediatric" in s or "neonatal" in s for s in m_set):
                penalties.append({"reason": "Domain gap: Pediatric/Neonatal Care", "impact": dom_pen})
        if any(spec in jt_lower for spec in ["icu", "intensive care"]):
            if not any("critical" in s or "icu" in s for s in m_set):
                penalties.append({"reason": "Domain gap: Intensive Care", "impact": dom_pen})
        if any(spec in jt_lower for spec in ["crna", "anesthetist"]):
            if not any("anesthesia" in s or "pharmacology" in s for s in m_set):
                penalties.append({"reason": "Domain gap: Anesthesia Support", "impact": dom_pen})
                
        # Remove duplicates
        unique_pen = []
        seen_reasons = set()
        for p in penalties:
            if p["reason"] not in seen_reasons:
                seen_reasons.add(p["reason"])
                unique_pen.append(p)
        penalties = unique_pen
        
        # 5. PENALTY NORMALIZATION: Cap total penalty at -0.1
        total_p = sum(p["impact"] for p in penalties)
        total_p = max(total_p, -0.1)
        
        final_score = round(max(0.0, min(1.0, weighted_base + total_p)), 2)
        if not matched_list and skill_score > 0.0: raise ValueError("Skill score mismatch")

        # 6. MATCH LEVEL CORRECTION
        if final_score >= 0.75:
            match_level = "Strong Match"
        elif final_score >= 0.60:
            match_level = "Moderate Match"
        else:
            match_level = "Weak Match"

        # Requirement: Exclude protected from explanation total (Requirement 6)
        protected_norm = ["basic life support (bls)", "advanced cardiovascular life support (acls)", "registered nurse license (rn)"]
        hard_no_protected = [h for h in hard_skills_list if h not in protected_norm]
        total_no_protected = len(hard_no_protected)
        matches_no_protected = len([m for m in matched_list if self.normalize_skill(m) in hard_no_protected])
        
        sl = []
        if exp_explanation: sl.append("relevant experience" + exp_explanation)
        elif experience_score >= 0.4: sl.append("relevant experience")
        if dynamic_semantic > 0.6: sl.append("high role relevance")
        ss = " and ".join(sl) if sl else "details"
        
        missing_tech = [m for m in missing_skills]
        ms = ", ".join(missing_tech[:3]) if missing_tech else "none"

        explanation = f"Final Match Score: {final_score}. Candidate matches {matches_no_protected}/{total_no_protected} core skills (excluding certifications). Strengths: {ss}. Missing technical skills: {ms}."

        hard_skills_list = [r_norm_map[r] for r in r_hard] if r_hard else list(r_norm_map.values())
        soft_skills_list = [r_norm_map[r] for r in r_soft]

        return {
            "job_title": job_title,
            "final_score": final_score,
            "match_level": match_level,
            "score_breakdown": {
                "skill": { 
                    "score": round(skill_score, 2), 
                    "hard_skills": hard_skills_list,
                    "soft_skills": soft_skills_list,
                    "matched_skills": matched_list, 
                    "missing_skills": missing_skills,
                    "added_skills": added_skills,
                    "removed_skills": removed_skills
                },
                "experience": { "score": round(experience_score, 2), "candidate_years": exp_years, "required_years": req_years },
                "education": { "score": round(edu_score, 2) },
                "semantic": { 
                    "score": round(dynamic_semantic, 2),
                    "consistency_flag": consistency_flag
                },
                "total_penalty": round(total_p, 2)
            },
            "penalties_applied": penalties,
            "explanation": explanation
        }