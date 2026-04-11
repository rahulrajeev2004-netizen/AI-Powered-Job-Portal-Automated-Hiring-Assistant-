"""
Day 18 Final Validation - Minimal Schema & Scoring Consistency
"""
import json

def validate():
    with open("outputs/production_85_jd_report.json", encoding="utf-8") as f:
        report = json.load(f)

    results = report.get("results", [])
    print(f"Total Unique JDs in report: {len(results)}")

    errors = []
    pool_dist = {}

    for job in results:
        jid = job.get("job_id", "Missing ID")
        status = job.get("job_match_status", "Missing")
        pool_dist[status] = pool_dist.get(status, 0) + 1
        
        candidates = job.get("candidates", [])
        if not candidates:
            continue
            
        scores = [c["final_score"] for c in candidates]
        n_scores = [c["normalized_score"] for c in candidates]
        
        # Check Rank & Score monotonicity
        for i in range(len(candidates) - 1):
            curr = candidates[i]
            nxt = candidates[i+1]
            if curr["normalized_score"] < nxt["normalized_score"]:
                errors.append(f"[RANK-ORDER] {jid}: rank {i+1} score {curr['normalized_score']} < rank {i+2} score {nxt['normalized_score']}")
            if curr["rank"] != i + 1:
                errors.append(f"[RANK-INDEX] {jid}: expected rank {i+1}, got {curr['rank']}")

        # Check Match Level consistency with thresholds
        for c in candidates:
            fs = c["final_score"]
            ml = c["match_level"]
            
            if fs >= 0.70:
                expected = "Strong Match"
            elif fs >= 0.40:
                expected = "Moderate Match"
            elif fs >= 0.20:
                expected = "Weak Match"
            else:
                expected = "Poor Match"
                
            # Rule 4: Skill cap check
            smr = c.get("skill_match_ratio", 0.0)
            if smr == 0 and fs <= 0.75:
                 if expected in ["Strong Match", "Moderate Match"]:
                     expected = "Weak Match"
                
            if ml != expected:
                errors.append(f"[MATCH-LEVEL] {jid}|{c['candidate_id']}: score {fs} should be {expected}, got {ml}")

        # Check Pool Detection (Request #15: Max-Score Based)
        max_s = max(scores) if scores else 0
        if max_s >= 0.70:
            expected_pool = "strong_candidate_pool"
        elif max_s >= 0.40:
            expected_pool = "moderate_candidate_pool"
        else:
            expected_pool = "weak_candidate_pool"
            
        if status != expected_pool:
            errors.append(f"[POOL-CLASS] {jid}: max={max_s:.2f} should be {expected_pool}, got {status}")

    print(f"\nPool Distribution:")
    for k, v in sorted(pool_dist.items()):
        print(f"  {k}: {v}")

    if errors:
        print(f"\n[FAIL] {len(errors)} issues found:")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors)-20} more")
    else:
        print(f"\n[PASS] All Day 18 scoring and ranking rules validated across {len(results)} JDs.")

if __name__ == "__main__":
    validate()
