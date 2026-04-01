import json
import os
import sys

# Add the current directory to sys.path to resolve imports correctly
# when running the script directly or as part of a package.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from embedder import Embedder
from scorer import Scorer
from evaluator import Evaluator

def main():
    """
    Main entry point for batch processing using segmented data files and parsed JDs.
    """
    # 1. Initialize core engine
    embedder = Embedder()
    scorer = Scorer(embedder)
    
    # Paths to actual data - Segmented Resumes & Parsed JDs
    resumes_dir = "data/samples/labeled/"
    jds_dir = "data/processed/jd_parsed_outputs/"
    
    # Also load the explicitly open nurse_jd.json if it exists
    default_jd_path = "data/samples/nurse_jd.json"
    
    # Target specific resumes as requested (5 total)
    target_resumes = [
        "Nurse_Resume_Anita_Mathew_segmented.json",
        "Rahul_segmented.json",
        "Reshma resume_segmented.json",
        "nurse_resume_segmented.json",
        "sample_2_segmented.json"
    ]
    
    resumes_files = [os.path.join(resumes_dir, f) for f in target_resumes if os.path.exists(os.path.join(resumes_dir, f))]
    
    if not resumes_files:
        print(f"None of the target segmented resumes were found in {resumes_dir}")
        return

    # Use explicitly provided nurse_jd.json only
    jds_files = []
    if os.path.exists(default_jd_path):
        jds_files = [default_jd_path]
    elif os.path.exists(jds_dir):
        # Fallback to current library if nurse_jd is missing, but prefer nurse_jd.json
        jds_files = [os.path.join(jds_dir, f) for f in os.listdir(jds_dir) if f.endswith(".json") and f != "README.md"][:1]

    if not jds_files:
        print("Required job description (nurse_jd.json) not found.")
        return

    print(f"Comparing {len(resumes_files)} Resumes against {len(jds_files)} Job Description(s).\n")

    # 2. Match loop
    output_dir = "outputs/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory at {output_dir}")

    all_matches_report = []

    for jd_path in jds_files[:5]: 
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_raw = json.load(f)
            
        jd_processed = {
            "job_title": jd_raw.get("job_title", "Unknown"),
            "required_skills": jd_raw.get("requirements", {}).get("skills", {}).get("mandatory", []) or jd_raw.get("requirements", {}).get("skills", []),
            "responsibilities": jd_raw.get("responsibilities", []),
            "description": jd_raw.get("job_summary", "") or jd_raw.get("summary", "")
        }
        
        print(f"--- Comparison with Job: {jd_processed['job_title']} ({os.path.basename(jd_path)}) ---")
        
        results = []
        for res_path in resumes_files:
            with open(res_path, "r", encoding="utf-8") as f:
                res_raw = json.load(f)
            
            candidate_name = os.path.basename(res_path).replace("_segmented.json", "")
            
            skills_raw = res_raw.get("skills", "")
            if isinstance(skills_raw, str):
                skills_list = [s.strip() for s in skills_raw.replace("\n", ",").split(",") if s.strip()]
            else:
                skills_list = skills_raw

            resume_processed = {
                "candidate_name": candidate_name,
                "skills": skills_list,
                "experience": [res_raw.get("work_experience", "")],
                "projects": [res_raw.get("projects", "")]
            }
            
            match_result = scorer.calculate_match_scores(resume_processed, jd_processed)
            results.append(match_result)

        # Rank results
        results.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Save results for this JD
        jd_filename = os.path.basename(jd_path).replace(".json", "_matches.json")
        res_output_path = os.path.join(output_dir, jd_filename)
        with open(res_output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)

        all_matches_report.append({
            "job_title": jd_processed['job_title'],
            "output_file": res_output_path,
            "top_candidate": results[0]['candidate_name'] if results else "None",
            "top_score": results[0]['final_score'] if results else 0
        })

        for i, res in enumerate(results):
            print(f"Rank {i+1}: {res['candidate_name']} | Score: {res['final_score']} | Match: {res['match_level']}")
        print("-" * 50 + "\n")

    # Save a master summary report
    master_report_path = os.path.join(output_dir, "master_match_summary.json")
    with open(master_report_path, "w", encoding="utf-8") as f:
        json.dump(all_matches_report, f, indent=4)
    print(f"Saved master summary report to {master_report_path}")

    # 3. Evaluation & Threshold Tuning (Example Data)
    print("\n----- EVALUATION & THRESHOLD TUNING -----\n")
    # Mock data [score, actual_label (1 = manual positive match, 0 = negative)]
    eval_data = [
        {"score": 0.82, "actual": 1},
        {"score": 0.55, "actual": 0},
        {"score": 0.74, "actual": 1},
        {"score": 0.61, "actual": 0}, 
        {"score": 0.88, "actual": 1},
        {"score": 0.40, "actual": 0}
    ]
    
    evaluator = Evaluator(thresholds=[0.5, 0.6, 0.7, 0.8])
    report = evaluator.generate_report(eval_data)
    print(report)

if __name__ == "__main__":
    # Ensure this script run correctly as a module if it has relative imports
    # or handle the path issue for local testing.
    # To run: python -m semantic_matching.main
    main()
