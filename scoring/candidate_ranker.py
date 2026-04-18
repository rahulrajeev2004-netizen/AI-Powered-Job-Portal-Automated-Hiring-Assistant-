from typing import List, Dict, Any, Optional
import numpy as np

class CandidateRanker:
    """
    Refined ATS Engine - Decision Reliability & Consistency Logic.
    Implements strict match mapping, status overrides, and job-level attribute normalization.
    """
    
    def __init__(self, ranking_mode: str = "default"):
        self.ranking_mode = ranking_mode

    def get_match_level(self, score: float, skill_ratio: float) -> str:
        # Match Level Standardization (Prompt 10)
        if skill_ratio < 0.3:
            return "Poor Match"
        
        # Base level from score
        if score >= 0.65:
            level = "Strong Match"
        elif score >= 0.40:
            level = "Moderate Match"
        elif score >= 0.20:
            level = "Weak Match"
        else:
            level = "Poor Match"

        # Refinement: Skill-based caps
        if skill_ratio <= 0.6 and level == "Strong Match":
            return "Moderate Match"
        
        return level

    def determine_consistent_status(self, score: float, match_level: str, i: int, pool_quality: str, 
                                    abs_flag: bool, skill_ratio: float, below_min: bool, 
                                    mode: str) -> str:
        # 1. Absolute Reject Floor (Prompt 10)
        if score < 0.4:
            return "Rejected"
            
        # 2. Shortlist Threshold (Prompt 10)
        if score >= 0.65:
            return "Shortlisted"
        else:
            return "Review"

    def rank_job_candidates(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strict Gated Ranker - Rule v28.0.
        """
        job_id = job_data.get("job_id", "Unknown")
        raw_candidates = job_data.get("candidates", [])
        
        if not raw_candidates:
            return {"job_id": job_id, "candidates": [], "summary": {"total_candidates": 0}}

        # 1. Deterministic Ranking
        sorted_pool = sorted(raw_candidates, key=lambda c: -round(float(c.get("final_score", 0.0)), 4))
        
        scores = [float(c["final_score"]) for c in sorted_pool]
        max_s = max(scores) if scores else 0
        min_s = min(scores) if scores else 0
        s_range = max_s - min_s
        
        # 2. Status & Normalization
        processed = []
        counts = {"Shortlist": 0, "Review": 0, "Reject": 0}
        
        for i, cand in enumerate(sorted_pool):
            status = cand.get("status", "Reject")
            score = float(cand.get("final_score", 0.0))
            conf = float(cand.get("confidence_score", 0.0))
            risk = cand.get("risk_level", "HIGH")
            
            norm_score = round((score - min_s) / s_range, 4) if s_range > 0 else 0.0
                
            processed.append({
                "candidate_id": cand.get("candidate_id"),
                "final_score": score,
                "normalized_score": norm_score,
                "confidence_score": conf,
                "rank": i + 1,
                "status": status,
                "risk_level": risk,
                "matched_skills": cand.get("matched_skills"),
                "missing_skills": cand.get("missing_skills"),
                "core_skill_coverage": cand.get("core_skill_coverage", 0.0),
                "explicit_skill_coverage": cand.get("explicit_skill_coverage", 0.0),
                "indicators": cand.get("indicators"),
                "explanation": cand.get("explanation"),
                "audit_trace": {**cand.get("audit_trace", {}), "rank": i+1}
            })
            counts[status] += 1

        # 3. System Flags
        system_flags = []
        if counts["Shortlist"] == 0:
            system_flags.append("LOW_QUALITY_CANDIDATE_POOL")
        if max_s < 0.60:
            system_flags.append("NO_STRONG_MATCH_FOUND")

        return {
            "job_id": job_id, "job_title": job_data.get("job_title", job_id),
            "candidates": processed, 
            "summary": {"total_candidates": len(processed), "shortlisted": counts["Shortlist"], "review": counts["Review"], "rejected": counts["Reject"]},
            "system_flags": system_flags
        }

    def process_batch(self, batch_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.rank_job_candidates(job) for job in batch_data]

def rank_candidates(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Handle flat list input by grouping by job_id
    from collections import defaultdict
    jobs = defaultdict(list)
    for m in matches:
        jid = m.get("job_id") or m.get("job_title") or "Unknown"
        jobs[jid].append(m)
    ranker = CandidateRanker()
    return [ranker.rank_job_candidates({"job_id": jid, "candidates": cands}) for jid, cands in jobs.items()]
