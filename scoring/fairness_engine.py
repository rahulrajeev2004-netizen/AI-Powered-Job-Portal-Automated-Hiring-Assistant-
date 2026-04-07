from typing import List, Dict, Any


class FairnessEngine:
    def __init__(self, threshold: float = 0.7):
        # threshold kept for backward compatibility with existing runner scripts
        self.threshold                 = threshold
        self.normalization_method      = "min-max"
        self.bias_adjustment_method    = "rule-based (+0.05 boost capped at 1.0)"

    # ------------------------------------------------------------------
    # Internal: decide bias_flag for each candidate before adjustment
    # Rule: flag candidates in the mid-range (0.4 <= n <= 0.9) who can
    # benefit from a fairness boost without already being at the top.
    # ------------------------------------------------------------------
    @staticmethod
    def _should_flag(normalized: float) -> bool:
        return 0.4 <= round(normalized, 4) <= 0.9

    # ------------------------------------------------------------------
    # Internal: build bias_analysis block from flagged candidates
    # ------------------------------------------------------------------
    @staticmethod
    def _build_bias_analysis(candidates: List[Dict]) -> Dict:
        scores     = [c["normalized_score"] for c in candidates]
        flagged_n  = sum(1 for c in candidates if c["bias_flag"])

        max_score  = round(max(scores), 2)
        min_score  = round(min(scores), 2)
        avg_norm   = round(sum(scores) / len(scores), 2) if scores else 0.0
        variance_i = round(max_score - avg_norm, 2)

        # Dynamic bias detection — NOT hardcoded
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


    # ------------------------------------------------------------------
    # Main method
    # ------------------------------------------------------------------
    def apply_fairness(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        candidates = job_data.get("candidates", [])

        if not candidates:
            return {
                "job_id":                   job_data.get("job_id"),
                "fairness_adjusted":        False,
                "normalization_method":     self.normalization_method,
                "bias_adjustment_method":   self.bias_adjustment_method,
                "candidates":               [],
                "bias_analysis": {
                    "bias_detected": False,
                    "reason":        "No candidates available for analysis.",
                    "method":        "min-max + rule-based adjustment"
                }
            }

        # ---------------------------------------------------------------
        # Step 1 — Extract original scores
        # ---------------------------------------------------------------
        raw = [c.get("original_score", c.get("final_score", 0.0))
               for c in candidates]

        max_s     = max(raw)
        min_s     = min(raw)
        rng       = max_s - min_s

        # ---------------------------------------------------------------
        # Step 2 — Min-Max normalization (per job)
        # ---------------------------------------------------------------
        processed = []
        for c in candidates:
            orig = c.get("original_score", c.get("final_score", 0.0))

            if rng > 0:
                norm = (orig - min_s) / rng
            else:
                # All scores equal → everyone gets 0.5
                norm = 0.5

            norm = round(norm, 4)

            processed.append({
                "candidate_id":    c.get("candidate_id"),
                "original_score":  orig,
                "normalized_score": norm,
            })

        # ---------------------------------------------------------------
        # Step 3 — Bias flag & rule-based adjustment
        #   bias_flag = True  → adjusted = min(normalized + 0.05, 1.0)
        #   bias_flag = False → adjusted = normalized
        # ---------------------------------------------------------------
        for c in processed:
            flag = self._should_flag(c["normalized_score"])
            c["bias_flag"] = flag

            if flag:
                adj = min(c["normalized_score"] + 0.05, 1.0)
            else:
                adj = c["normalized_score"]

            # Round to 2dp for ranking stability
            c["adjusted_score"]    = round(adj, 2)
            c["normalized_score"]  = round(c["normalized_score"], 2)

        # ---------------------------------------------------------------
        # Step 4 — Rank by adjusted_score (desc); tie-break original_score
        # ---------------------------------------------------------------
        sorted_c = sorted(
            processed,
            key=lambda x: (-x["adjusted_score"], -x["original_score"], x["candidate_id"])
        )

        # Assign unique sequential ranks (1, 2, 3...)
        final = []
        for i, c in enumerate(sorted_c):
            final.append({
                "candidate_id":     c["candidate_id"],
                "original_score":   c["original_score"],
                "normalized_score": c["normalized_score"],
                "adjusted_score":   c["adjusted_score"],
                "rank":             i + 1,
                "bias_flag":        c["bias_flag"],
            })

        # ---------------------------------------------------------------
        # Step 5 — Bias analysis block
        # ---------------------------------------------------------------
        bias_analysis = self._build_bias_analysis(final)

        return {
            "job_id":                 job_data.get("job_id"),
            "fairness_adjusted":      True,
            "normalization_method":   self.normalization_method,
            "bias_adjustment_method": self.bias_adjustment_method,
            "candidates":             final,
            "bias_analysis":          bias_analysis,
        }

    def process_all(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.apply_fairness(job) for job in data]
