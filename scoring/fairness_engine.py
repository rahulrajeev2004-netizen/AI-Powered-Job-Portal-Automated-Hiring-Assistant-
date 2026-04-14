import json
from typing import List, Dict, Any

class FairnessEngine:
    def __init__(self, threshold: float = 0.7, boost: float = 0.05):
        self.threshold                 = threshold
        self.boost                     = boost
        self.normalization_method      = "min-max"
        self.bias_adjustment_method    = "rule-based (+0.05 boost capped at 1.0)"

    @staticmethod
    def _should_flag(normalized: float) -> bool:
        return 0.4 <= round(normalized, 4) <= 0.9

    @staticmethod
    def _build_bias_analysis(candidates: List[Dict]) -> Dict:
        scores     = [c["normalized_score"] for c in candidates]
        flagged_n  = sum(1 for c in candidates if c["bias_flag"])

        max_score  = round(max(scores), 2) if scores else 0.0
        min_score  = round(min(scores), 2) if scores else 0.0
        avg_norm   = round(sum(scores) / len(scores), 2) if scores else 0.0
        variance_i = round(max_score - avg_norm, 2)

        bias_detected = (avg_norm < 0.4) or (variance_i > 0.5)

        reason = (
            f"Score imbalance detected: min={min_score}, max={max_score}, "
            f"avg={avg_norm}. Variance indicator={variance_i}. "
            f"{flagged_n} candidate(s) received fairness adjustment."
            if bias_detected else
            f"Score distribution is balanced: min={min_score}, max={max_score}, "
            f"avg={avg_norm}. Variance indicator={variance_i}. "
            f"{flagged_n} candidate(s) received fairness adjustment."
        )

        return {
            "bias_detected": bias_detected,
            "reason":        reason,
            "method":        "min-max + rule-based adjustment"
        }

    def apply_fairness(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        candidates = job_data.get("candidates", [])

        if not candidates:
            return {
                "job_id": job_data.get("job_id"),
                "fairness_adjusted": False,
                "normalization_method": self.normalization_method,
                "bias_adjustment_method": self.bias_adjustment_method,
                "candidates": [],
                "bias_analysis": {"bias_detected": False, "reason": "No candidates.", "method": "min-max"}
            }

        # 1. Duplicate Detection & Deduplication (Objective 4)
        seen_fingerprints = {}
        unique_candidates = []
        for cand in candidates:
            # Fingerprint based on breakdown values and explanation to detect true duplicates
            breakdown = cand.get("breakdown", {})
            explanation = cand.get("explanation", "")
            fingerprint = f"{json.dumps(breakdown, sort_keys=True)}|{explanation}"
            
            if fingerprint in seen_fingerprints:
                print(f"[DEBUG FAIRNESS] Duplicate candidate detected: {cand.get('candidate_id')}. Matching with {seen_fingerprints[fingerprint]}")
                continue # Skip duplicates
            
            seen_fingerprints[fingerprint] = cand.get("candidate_id")
            unique_candidates.append(cand)

        # 2. Normalization (Objective 2)
        raw_scores = [c.get("original_score", 0.0) for c in unique_candidates]
        max_s = max(raw_scores)
        min_s = min(raw_scores)
        rng = max_s - min_s
        scaling_factor = round(1.0 / rng, 4) if rng > 0 else 1.0

        processed = []
        for c in unique_candidates:
            orig = c.get("original_score", 0.0)
            norm = (orig - min_s) / rng if rng > 0 else 1.0
            norm = round(norm, 4)

            # 3. Bias Adjustment (Objective 6)
            flag = self._should_flag(norm)
            adj = min(norm + self.boost, 1.0) if flag else norm
            
            # Extract breakdown metrics for tie-breaking (Objective 1)
            breakdown = c.get("breakdown", {})
            processed.append({
                "candidate_id": c.get("candidate_id"),
                "raw_score": orig,
                "normalized_score": norm,
                "bias_flag": flag,
                "adjustment_applied": self.boost if flag else 0.0,
                "adjusted_score": round(adj, 4),
                "final_score": round(adj, 2), # Final display score
                "skills": breakdown.get("skills", 0.0),
                "experience": breakdown.get("experience", 0.0),
                "education": breakdown.get("education", 0.0),
                "domain_relevance": breakdown.get("domain_relevance", 0.0)
            })

        # 4. Deterministic Ranking (Objective 1)
        # Hierarchy: final_score -> skills -> experience -> education -> domain_relevance -> candidate_id
        sorted_c = sorted(
            processed,
            key=lambda x: (
                -x["final_score"], 
                -x["skills"], 
                -x["experience"], 
                -x["education"], 
                -x["domain_relevance"],
                x["candidate_id"]
            )
        )

        final = []
        for i, c in enumerate(sorted_c):
            c["rank"] = i + 1
            final.append(c)

        bias_analysis = self._build_bias_analysis(final)

        return {
            "job_id": job_data.get("job_id"),
            "fairness_adjusted": True,
            "normalization_method": self.normalization_method,
            "normalization_factor": scaling_factor,
            "normalization_range": {"min": min_s, "max": max_s},
            "bias_adjustment_method": self.bias_adjustment_method,
            "candidates": final,
            "bias_analysis": bias_analysis,
        }

    def process_all(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.apply_fairness(job) for job in data]
