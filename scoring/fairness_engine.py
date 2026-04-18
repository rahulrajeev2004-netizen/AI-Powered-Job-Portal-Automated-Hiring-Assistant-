import json
from typing import List, Dict, Any

class FairnessEngine:
    def __init__(self, boost: float = 0.05):
        self.boost                     = boost
        self.normalization_method      = "min-max"
        self.bias_adjustment_method    = "rule-based (+0.05 boost based on Rule 4)"

    @staticmethod
    def _should_apply_boost(c: Dict) -> bool:
        # Rule 4: skill_overlap == 0 OR total_score < 0.25
        skill_overlap = c.get("skill_overlap", 0.0)
        base_score = c.get("final_score", 0.0)
        return skill_overlap == 0 or base_score < 0.25

    def apply_fairness(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        candidates = job_data.get("candidates", [])
        if not candidates: return job_data
        
        processed = []
        for c in candidates:
            # Check if boost already applied by Scorer (fairness_adjustment > 0)
            already_boosted = c.get("fairness_adjustment", 0.0) > 0
            
            should_boost = self._should_apply_boost(c)
            applied_now = False
            
            if should_boost and not already_boosted:
                c["final_score"] = min(c["final_score"] + self.boost, 1.0)
                c["fairness_adjustment"] = self.boost
                c["explanation"] += " [Fairness Adjusted]"
                applied_now = True
            
            processed.append(c)
            
        return {
            "job_id": job_data.get("job_id"),
            "fairness_applied": True,
            "candidates": processed
        }

    def process_all(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.apply_fairness(job) for job in data]
