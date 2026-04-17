import json
import os

def summarize_eval():
    file_path = "outputs/day20_production_eval.json"
    if not os.path.exists(file_path):
        print("Evaluation file not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If it's the large multi-JD report
    if isinstance(data, dict) and "results" in data:
        results = data["results"]
        total_jds = data["total_jds_evaluated"]
        total_resumes = data["resumes_processed"]
        
        summary = {
            "total_jds": total_jds,
            "total_resumes": total_resumes,
            "total_matches": total_jds * total_resumes,
            "performance": {},
            "top_candidates": {}
        }

        shortlist_count = 0
        review_count = 0
        rejected_count = 0

        for report in results:
            for cand in report["ranked_candidates"]:
                cid = cand["candidate_id"]
                score = cand["final_score"]
                
                if score >= 0.65: shortlist_count += 1
                elif score >= 0.40: review_count += 1
                else: rejected_count += 1
                
                if cid not in summary["top_candidates"]:
                    summary["top_candidates"][cid] = {"total_score": 0, "jd_count": 0, "max_score": 0}
                
                summary["top_candidates"][cid]["total_score"] += score
                summary["top_candidates"][cid]["jd_count"] += 1
                summary["top_candidates"][cid]["max_score"] = max(summary["top_candidates"][cid]["max_score"], score)

        summary["performance"] = {
            "shortlist_rate": round(shortlist_count / (total_jds * total_resumes) * 100, 2),
            "review_rate": round(review_count / (total_jds * total_resumes) * 100, 2),
            "rejection_rate": round(rejected_count / (total_jds * total_resumes) * 100, 2)
        }
        
        # Sort top candidates by average score
        sorted_candidates = sorted(
            summary["top_candidates"].items(),
            key=lambda x: x[1]["total_score"] / x[1]["jd_count"],
            reverse=True
        )
        
        with open("outputs/summary_stats.json", "w") as f:
            json.dump({
                "summary": summary,
                "leaderboard": sorted_candidates[:5]
            }, f, indent=2)
            
        print("Summary stats generated.")

if __name__ == "__main__":
    summarize_eval()
