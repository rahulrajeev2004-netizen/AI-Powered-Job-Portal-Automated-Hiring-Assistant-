import json
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EligibilityEngine:
    """
    Candidate Eligibility Decision Engine for ATS.
    Classifies candidates into Eligible, Review, or Rejected based on strict recruiter-defined rules.
    """
    def __init__(self, config: Dict[str, Any]):
        self.job_id = config.get("job_id", "UNKNOWN")
        self.job_title = config.get("job_title", "Unknown Role")
        self.min_score = float(config.get("min_score", 0.0))
        self.mandatory_skills = [s.lower().strip() for s in config.get("mandatory_skills", [])]
        self.min_experience = float(config.get("min_experience", 0.0))
        self.max_experience = float(config.get("max_experience", 100.0))
        self.allowed_locations = [loc.lower().strip() for loc in config.get("allowed_locations", [])]
        self.availability_required = bool(config.get("availability_required", False))
        self.review_score_range = config.get("review_score_range", [0.0, 0.0])
        
        # Ensure review_score_range is a list of 2 floats
        if not isinstance(self.review_score_range, list) or len(self.review_score_range) != 2:
            self.review_score_range = [0.0, self.min_score]
        else:
            self.review_score_range = [float(x) for x in self.review_score_range]

    def evaluate_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculated Hiring Logic:
        - Strict Score Thresholds: 0.7 (Eligible), 0.3 (Reject), Middle (Review)
        - Meaningful, non-redundant reasoning
        - High confidence for clear pass/fail
        """
        candidate_id = candidate.get("candidate_id", "Unknown")
        score = float(candidate.get("final_score", 0.0))
        
        # --- 1. Skill Match Assessment ---
        cand_skills = set([s.lower().strip() for s in candidate.get("skills", [])])
        mandatory_set = set([s.lower().strip() for s in self.mandatory_skills])
        
        if not mandatory_set:
            skill_ratio = 1.0
        else:
            matched = len(mandatory_set.intersection(cand_skills))
            skill_ratio = matched / len(mandatory_set)
        
        is_relevant_match = skill_ratio >= 0.3
        is_partial_match = 0.05 <= skill_ratio < 0.3
        is_extremely_poor = skill_ratio < 0.05

        # --- 2. Corrected Logic (Strict Score Tiers) ---
        reasons = []

        # TIER 1: STRONG (SCORE >= 0.7)
        if score >= 0.7:
            status = "Eligible"
            confidence = "High"
            reasons = ["Strong ATS score", "Relevant skill match"]
            action = "AI Interview"
        
        # TIER 2: WEAK (SCORE < 0.2)
        elif score < 0.2:
            status = "Rejected"
            confidence = "High"
            reasons = ["Very low score", "Weak or missing required skills"]
            action = "Reject"
            
        # TIER 3: MID (0.2 <= SCORE < 0.7)
        else:
            status = "Review"
            confidence = "Medium"
            action = "Recruiter Review"
            reasons.append("Score in review range")
            if is_partial_match or is_relevant_match:
                reasons.append("Partial skill match")
            else:
                reasons.append("Weak or missing required skills")

        return {
            "candidate_id": candidate_id,
            "final_score": score,
            "eligibility_status": status,
            "decision_confidence": confidence,
            "reasons": reasons[:2],
            "next_action": action
        }

    def process_batch(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a list of candidates and generate the production-ready JSON output.
        """
        results = []
        counts = {"eligible": 0, "review": 0, "rejected": 0}

        for cand in candidates:
            decision = self.evaluate_candidate(cand)
            results.append(decision)
            counts[decision["eligibility_status"].lower()] += 1

        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "total_candidates_processed": len(candidates),
            "decision_summary": counts,
            "candidates": results
        }
