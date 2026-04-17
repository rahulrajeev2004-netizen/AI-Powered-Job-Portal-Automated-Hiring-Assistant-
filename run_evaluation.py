import os
import json
import sys
import hashlib
from typing import List, Dict

# Add project root to path
sys.path.append(os.getcwd())

from app.core import logic
from scoring.candidate_ranker import CandidateRanker

def run_evaluation():
    print("Starting Day 20 Production Evaluation...")
    
    demo_dir = "data/demo_resumes"
    job_description = """
    Job Title: Critical Care Nurse
    Description: We are looking for an experienced ICU Nurse to join our team.
    Requirements:
    - 5+ years of experience in critical care.
    - Mandatory Skills: ICU Care, Ventilator Management, Hemodynamic Monitoring, Patient Care.
    - Certifications: RN License, BLS, ACLS.
    - Education: Bachelor of Science in Nursing.
    """
    
    # 1. Load and Parse Demo Resumes
    resumes = []
    for filename in os.listdir(demo_dir):
        if filename.endswith(".txt"):
            path = os.path.join(demo_dir, filename)
            print(f"Parsing {filename}...")
            parsed = logic.parse_resume_task(path)
            
            # Simple mapping to candidate format
            resumes.append({
                "candidate_id": filename,
                "skills": parsed.get("extracted_skills", []),
                "experience_years": parsed.get("experience_years", 0.0),
                "education": str(parsed.get("education", "")),
                "resume_text": open(path, "r", encoding="utf-8").read()
            })
            
    # 2. Run Production Scoring
    print(f"Scoring {len(resumes)} candidates (including 1 duplicate)...")
    results = logic.score_candidates(resumes, job_description)
    
    # 3. Output Results
    output_path = "outputs/day20_production_eval.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Evaluation complete. Results saved to {output_path}")
    
    # 4. Basic Validation Printing
    print("\n--- Evaluation Summary ---")
    print(f"Total input resumes: {len(resumes)}")
    print(f"Final ranked candidates (after deduplication): {results['total_candidates']}")
    
    for i, cand in enumerate(results["ranked_candidates"]):
        print(f"Rank {cand['rank']}: {cand['candidate_id']} - Score: {cand['final_score']}")
        if "data_warning" in cand:
             print(f"  Warning: {cand['data_warning']['message']}")

if __name__ == "__main__":
    run_evaluation()
