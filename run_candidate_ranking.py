import json
import os
from scoring.candidate_ranker import rank_candidates

def main():
    input_file = "outputs/consolidated_match_report.json"


    output_file = "outputs/ranked_candidates.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return
        
    # Standardize data to the required format
    # The exact keys in consolidated_match_report.json might differ, but we need
    # job_id, candidate_id, final_score
    formatted_data = []
    
    # Assuming data is a dictionary where keys are candidate_names and values are lists of job matches
    if isinstance(data, dict):
        for candidate_name, jobs in data.items():
            for item in jobs:
                job_id = item.get("job_title", "Unknown") # They use job_title instead of job_id in this file
                candidate_id = item.get("candidate_name", candidate_name)
                final_score = item.get("final_score", 0.0)
                
                formatted_data.append({
                    "job_id": job_id,
                    "candidate_id": candidate_id,
                    "final_score": final_score
                })

        
    if not formatted_data:
        print("No match records found or format mismatch.")
        return

    # Call the ranker function
    print("Ranking candidates...")
    ranked_output = rank_candidates(formatted_data)
    
    # Save the output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ranked_output, f, indent=2)
        
    print(f"Successfully ranked candidates and saved to {output_file}")


if __name__ == "__main__":
    main()
