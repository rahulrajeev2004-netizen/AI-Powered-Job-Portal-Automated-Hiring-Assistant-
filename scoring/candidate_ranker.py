from typing import List, Dict, Any
from collections import defaultdict

def rank_candidates(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process candidate-job match results to generate ranked and classified output.
    
    Args:
        matches: List of dicts containing job_id, candidate_id, and final_score.
        
    Returns:
        List of job-wise results with ranked candidates.
    """
    # Group by job_id
    jobs_data = defaultdict(list)
    
    for record in matches:
        job_id = record.get("job_id")
        if not job_id:
            continue
        jobs_data[job_id].append({
            "candidate_id": record.get("candidate_id"),
            "final_score": record.get("final_score", 0.0)
        })
    
    grouped_results = []
    
    for job_id, candidates in jobs_data.items():
        # Sort candidates by final_score (desc) and candidate_id (asc) for consistency
        sorted_candidates = sorted(candidates, key=lambda x: (-x["final_score"], x["candidate_id"]))
        
        ranked_candidates = []
        current_rank = 0
        prev_score = None
        
        for candidate in sorted_candidates:
            score = candidate["final_score"]
            
            # If current score is different from previous, increment rank
            if score != prev_score:
                current_rank += 1
                prev_score = score
            
            # Determine status
            if score >= 0.75:
                status = "Shortlisted"
            elif 0.50 <= score < 0.75:
                status = "Review"
            else:
                status = "Rejected"
                
            ranked_candidates.append({
                "candidate_id": candidate["candidate_id"],
                "final_score": score,
                "rank": current_rank,
                "status": status
            })

            
        grouped_results.append({
            "job_id": job_id,
            "candidates": ranked_candidates
        })
        
    return grouped_results

if __name__ == "__main__":
    import json
    
    # Test data
    test_input = [
        {"job_id": "J1", "candidate_id": "C1", "final_score": 0.82},
        {"job_id": "J1", "candidate_id": "C2", "final_score": 0.52},
        {"job_id": "J2", "candidate_id": "C1", "final_score": 0.60},
        {"job_id": "J1", "candidate_id": "C3", "final_score": 0.52},
        {"job_id": "J2", "candidate_id": "C2", "final_score": 0.76}
    ]
    
    output = rank_candidates(test_input)
    print(json.dumps(output, indent=2))

