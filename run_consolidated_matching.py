import os
import json
import sys

# Add project root and semantic_matching directory to path
project_root = os.path.dirname(os.path.abspath(__file__))
semantic_dir = os.path.join(project_root, "semantic_matching")
if project_root not in sys.path:
    sys.path.append(project_root)
if semantic_dir not in sys.path:
    sys.path.append(semantic_dir)

from embedder import Embedder
from scorer import Scorer
from similarity import (
    compute_skill_similarity,
    compute_experience_similarity,
    compute_project_similarity
)

def generate_consolidated_report():
    """
    Compares 5 authorized resumes against 85 JDs and saves everything in one file.
    Output: outputs/consolidated_match_report.json
    """
    # 1. Initialization
    embedder = Embedder()
    scorer = Scorer(embedder)
    
    resumes_dir = "data/samples/labeled"
    jds_txt_dir = "data/processed/individual_jds_txt"
    jds_json_dir = "data/processed/jd_parsed_outputs"
    output_path = "outputs/consolidated_match_report.json"
    
    os.makedirs("outputs", exist_ok=True)

    # 2. Authorized Resumes (5 only)
    allowed_resumes = {
        "Nurse_Resume_Anita_Mathew_segmented.json",
        "Rahul_segmented.json",
        "Reshma resume_segmented.json",
        "nurse_resume_segmented.json",
        "sample_2_segmented.json"
    }
    
    resume_files = [f for f in os.listdir(resumes_dir) if f in allowed_resumes]
    if not resume_files:
        print(f"Error: Authorized resumes not found in {resumes_dir}")
        return

    # 3. Load All 85 Job Descriptions
    # We prioritize the parsed JSON ones, fall back to raw text parsing for others
    jd_txt_files = sorted([f for f in os.listdir(jds_txt_dir) if f.endswith(".txt")])
    jds_to_process = []
    
    print(f"Collecting {len(jd_txt_files)} Job Descriptions...")
    
    # Try to find corresponding parsed JSONs first
    for jd_txt in jd_txt_files:
        # Check if parsed JSON exists with similar name
        jd_json_name = jd_txt.replace(".txt", ".json").replace(" ", "_")
        jd_json_path = os.path.join(jds_json_dir, jd_json_name)
        
        parsed_jd = None
        if os.path.exists(jd_json_path):
            with open(jd_json_path, 'r', encoding='utf-8') as f:
                parsed_jd = json.load(f)
        else:
            # Fallback: create mock parsed structure from text if not in parsed folder
            # (In production, we'd call the JD Parser here)
            with open(os.path.join(jds_txt_dir, jd_txt), 'r', encoding='utf-8') as f:
                raw_text = f.read()
            # Simple heuristic parse for missing ones
            parsed_jd = {
                "job_title": jd_txt.replace(".txt", "").replace("_", " "),
                "job_summary": raw_text[:200],
                "responsibilities": raw_text.split("\n")[:10],
                "requirements": {"skills": {"mandatory": []}}
            }
            
        jds_to_process.append(parsed_jd)

    print(f"Matched {len(jds_to_process)} JDs for comparison.")

    # 4. Processing
    consolidated_data = {}

    for res_name in resume_files:
        res_key = res_name.replace("_segmented.json", "")
        consolidated_data[res_key] = []
        
        with open(os.path.join(resumes_dir, res_name), 'r', encoding='utf-8') as f:
            res_raw = json.load(f)
            
        # Standardize Resume mapping
        skills_raw = res_raw.get("skills", "")
        if isinstance(skills_raw, str):
            skills_list = [s.strip() for s in skills_raw.replace("\n", ",").split(",") if s.strip()]
        else:
            skills_list = skills_raw

        resume_processed = {
            "candidate_name": res_key,
            "skills": skills_list,
            "experience": [res_raw.get("work_experience", "")],
            "projects": [res_raw.get("projects", "")]
        }

        print(f"  [+] Matching Candidate: {res_key}")

        for jd in jds_to_process:
            # Map JD structure for Scorer
            # Ensure we take the job_title from data, or filename heuristic
            raw_title = jd.get("job_title") or jd.get("job_id", "Unknown")
            
            jd_processed = {
                "job_title": raw_title,
                "required_skills": jd.get("requirements", {}).get("skills", {}).get("mandatory", []) or jd.get("requirements", {}).get("skills", []),
                "responsibilities": jd.get("responsibilities", []),
                "description": jd.get("job_summary", "") or jd.get("summary", "")
            }
            
            match_result = scorer.calculate_match_scores(resume_processed, jd_processed)
            
            # Format report as requested
            consolidated_data[res_key].append({
                "job_title": match_result["job_title"],
                "final_score": match_result["final_score"],
                "match_level": match_result["match_level"],
                "penalty_applied": match_result["penalty_applied"]
            })

    # Sort each candidate's list by score descending
    for res_key in consolidated_data:
        consolidated_data[res_key].sort(key=lambda x: x["final_score"], reverse=True)

    # 5. Save Output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, indent=2, ensure_ascii=False)

    print(f"\nFinal Consolidated Report Saved to: {output_path}")
    print(f"Processed 5 Resumes x 85 Job Descriptions.")

if __name__ == "__main__":
    generate_consolidated_report()
