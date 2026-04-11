import json

def apply_strict_corrections():
    # Load raw engine output
    with open("outputs/production_85_jd_report.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    new_results = []
    
    for job in data.get("results", []):
        candidates = job.get("candidates", [])
        if not candidates:
            continue

        # Extract stats for min-max
        scores = [c["final_score"] for c in candidates]
        max_s = max(scores) if scores else 0
        min_s = min(scores) if scores else 0
        
        # 3. FIX: Job classification rules based on MAX score
        if max_s >= 0.70:
            job_match_status = "strong_candidate_pool"
        elif max_s >= 0.50:
            job_match_status = "moderate_candidate_pool"
        else:
            job_match_status = "weak_candidate_pool"
            
        job["job_match_status"] = job_match_status
        job["ranking_mode"] = "strict" if max_s >= 0.50 else "low_confidence"

        # 1. FIX: Strict Linear Min-Max Normalization (Precision 3 decimals)
        for c in candidates:
            fs = c["final_score"]
            if max_s == min_s:
                ns = 1.0
            else:
                ns = (fs - min_s) / (max_s - min_s)
            
            # Rule 5: Round precision to 3 decimals
            c["normalized_score"] = round(ns, 3)

        # 4. FIX: Ensure Ranking reflects Score (Sorted by final_score DESC)
        candidates.sort(key=lambda x: x.get("candidate_id", "").lower()) # stable fallback
        candidates.sort(key=lambda x: x["final_score"], reverse=True)

        for i, c in enumerate(candidates):
            c["rank"] = i + 1
            fs = c["final_score"]
            
            # 2. FIX: Inconsistent match_level mapping (Strict Thresholds)
            if fs >= 0.75:
                match_level = "Strong Match"
            elif fs >= 0.50:
                match_level = "Moderate Match"
            elif fs >= 0.25:
                match_level = "Weak Match"
            else:
                match_level = "Poor Match"
            c["match_level"] = match_level

            # 4. SKILL CONSISTENCY (Handled by 60% weight in engine, but here ensures cleaning)
            smr = c.get("skill_match_ratio", 0.0)
            if "skill_details" in c:
                smr = c["skill_details"].get("skill_match_ratio", smr)
            c["skill_match_ratio"] = smr

            # Cleanup Fields (Day 18 Schema)
            allowed_keys = {
                "candidate_id", "final_score", "normalized_score", 
                "rank", "match_level", "skill_match_ratio",
                "below_minimum_threshold", "rank_warning"
            }
            
            if fs < 0.25:
                c["below_minimum_threshold"] = True
            
            if c["rank"] == 1 and fs < 0.30:
                c["rank_warning"] = ["Top candidate final_score < 0.30", "Low quality candidate pool"]
            
            # Final key scrub
            for k in list(c.keys()):
                if k not in allowed_keys:
                    del c[k]

        job["candidates"] = candidates
        
        # Clean job level
        job_allowed = {"job_id", "job_match_status", "ranking_mode", "candidates"}
        for k in list(job.keys()):
            if k not in job_allowed:
                del job[k]
                
        new_results.append(job)

    final_output = {"results": new_results}
    
    with open("outputs/production_85_jd_report_strict.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
    with open("outputs/production_85_jd_report.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

if __name__ == "__main__":
    apply_strict_corrections()
    print("Done")
