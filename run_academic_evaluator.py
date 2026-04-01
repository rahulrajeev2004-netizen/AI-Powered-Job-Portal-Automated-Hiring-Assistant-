import os
import json
import argparse
from parsers.academic_parser import AcademicParser
from engines.academic_evaluator.academic_evaluator import AcademicEvaluator

def run_evaluation(resume_text: str, jd_json: dict):
    """
    Perform full academic extraction and relevance evaluation.
    """
    # 1. Parsing
    parser = AcademicParser()
    academic_profile = parser.parse_academic_profile(resume_text)
    
    # 2. Evaluation
    evaluator = AcademicEvaluator()
    relevance = evaluator.evaluate_relevance(academic_profile, jd_json)
    
    # 3. Combine Output
    output = {
        "education": academic_profile["education"],
        "certifications": academic_profile["certifications"],
        "education_relevance": relevance
    }
    
    return output

def main():
    parser = argparse.ArgumentParser(description="Zecpath Academic Evaluator Batch")
    parser.add_argument("--resume", help="Path to a single cleaned resume text file")
    parser.add_argument("--dir", help="Directory containing multiple cleaned resume text files")
    parser.add_argument("--jd", help="Path to JD JSON file")
    
    args = parser.parse_args()
    
    # 1. Collect Resumes (Filtered to 5 given candidates)
    target_files = {
        "Nurse_Resume_Anita_Mathew_pdf_cleaned.txt",
        "Rahul_pdf_cleaned.txt",
        "Reshma resume_pdf_cleaned.txt",
        "nurse_resume_pdf_cleaned.txt",
        "sample_resume_pdf_cleaned.txt"
    }

    if args.resume:
        resumes.append(args.resume)
    elif args.dir:
        resumes = [os.path.join(args.dir, f) for f in os.listdir(args.dir) if f in target_files]
    else:
        # Default fallback to processed directory
        default_dir = "data/processed"
        if os.path.exists(default_dir):
            resumes = [os.path.join(default_dir, f) for f in os.listdir(default_dir) if f in target_files]

    if not resumes:
        # Final fallback to requested file
        res_file = "data/processed/nurse_resume_pdf_cleaned.txt"
        if os.path.exists(res_file):
            resumes = [res_file]
        else:
            print("[]")
            return

    # 2. Load JD
    jd_path = args.jd or "data/samples/nurse_jd.json"
    try:
        with open(jd_path, 'r', encoding='utf-8') as f:
            jd_data = json.load(f)
            jd_json = jd_data[0] if isinstance(jd_data, list) else jd_data
    except Exception:
        jd_json = {
            "requirements": {
                "education": {
                    "min_degree": "bachelor",
                    "fields": ["nursing", "healthcare"],
                    "preferred_certifications": ["bls", "acls", "registered nurse"]
                }
            }
        }

    # 3. Process Batch
    results = []
    for r_path in resumes:
        try:
            with open(r_path, 'r', encoding='utf-8') as f:
                r_text = f.read()
            
            evaluation = run_evaluation(r_text, jd_json)
            results.append(evaluation)
            
            # Save individual result (quietly)
            out_dir = "outputs/academic_evals"
            os.makedirs(out_dir, exist_ok=True)
            resume_base = os.path.basename(r_path).replace(".txt", "").replace(".pdf", "").replace(".docx", "")
            out_path = os.path.join(out_dir, f"{resume_base}_eval.json")
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation, f, indent=2)
                
        except Exception:
            continue

    # 4. Output Consolidated Results
    if len(results) == 1:
        print(json.dumps(results[0], indent=2))
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
