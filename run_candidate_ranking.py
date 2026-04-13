import json
import os
from scoring.candidate_ranker import rank_candidates, CandidateRanker
from scoring.fairness_engine import FairnessEngine

def main():
    # Priority 1: Consolidated Production Report
    input_file = "outputs/production_85_jd_report_strict.json"
    if not os.path.exists(input_file):
        # Priority 2: Standard Consolidated Match Report
        input_file = "outputs/consolidated_match_report.json"
        
    output_file = "outputs/final_ranked_report.json"
    
    if not os.path.exists(input_file):
        print(f"Error: No input file found at {input_file}")
        return
        
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return
        
    ranker = CandidateRanker()
    
    # Check if data is job-wise (Production Format)
    if isinstance(data, dict) and "results" in data:
        print(f"Detected Production format in {input_file}...")
        processed_results = ranker.process_batch(data["results"])
    elif isinstance(data, list):
        print(f"Detected List format in {input_file}...")
        if len(data) > 0 and "job_id" in data[0]:
            processed_results = ranker.process_batch(data)
        else:
            processed_results = rank_candidates(data)
    elif isinstance(data, dict):
        print(f"Detected Candidate-centric format in {input_file}...")
        from collections import defaultdict
        jobs_map = defaultdict(list)
        for cand_name, match_list in data.items():
            for m in match_list:
                m["candidate_id"] = cand_name
                job_id = m.get("job_title", "Unknown Job")
                jobs_map[job_id].append(m)
        batch = [{"job_id": jid, "candidates": cands} for jid, cands in jobs_map.items()]
        processed_results = ranker.process_batch(batch)
    else:
        print("Unsupported data format.")
        return

    # Clean up duplicate job entries
    unique_jobs = {}
    
    # Hierarchy mappings for comparison
    status_rank = {"strong_candidate_pool": 3, "moderate_candidate_pool": 2, "weak_candidate_pool": 1}
    quality_rank = {"High": 3, "Moderate": 2, "Low": 1}
    
    for entry in processed_results:
        jid = entry.get("job_id")
        if jid not in unique_jobs:
            unique_jobs[jid] = entry
            continue
            
        existing = unique_jobs[jid]
        
        # Comparison logic
        s1 = status_rank.get(entry.get("job_match_status"), 0)
        s2 = status_rank.get(existing.get("job_match_status"), 0)
        
        q1 = quality_rank.get(entry.get("pool_quality"), 0)
        q2 = quality_rank.get(existing.get("pool_quality"), 0)
        
        t1 = entry.get("summary", {}).get("top_score", 0.0)
        t2 = existing.get("summary", {}).get("top_score", 0.0)
        
        # Decision point
        better = False
        if s1 > s2:
            better = True
        elif s1 == s2:
            if q1 > q2:
                better = True
            elif q1 == q2:
                if t1 >= t2: # >= handles the "Keep LAST" rule if top_score is equal
                    better = True
        
        if better:
            unique_jobs[jid] = entry

    final_output = {"results": list(unique_jobs.values())}

    # Save the initial ranked output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
        
    print(f"Successfully ranked candidates and saved to {output_file}")

    # Optional: Apply Fairness Adjustment if needed
    # (Note: Fairness engine might need updates to handle new job-summary structure)


if __name__ == "__main__":
    main()
