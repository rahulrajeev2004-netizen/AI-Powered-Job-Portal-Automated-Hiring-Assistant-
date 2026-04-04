import json
import os
import sys
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from scoring.ats_scorer import candidate_score_generator

def read_text(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def parse_txt_jd_fallback(filepath):
    text = read_text(filepath)
    lines = text.split('\n')
    title = lines[0].split('.', 1)[-1].strip() if lines else "Unknown Role"
    skills = []
    
    in_skills = False
    for line in lines:
        if 'skills required' in line.lower():
            in_skills = True
            continue
        if in_skills and line.strip().startswith('•'):
            skills.append(line.replace('•', '').strip())
            
    return {
        "job_title": title,
        "required_skills": skills,
        "experience_required": 2,
        "education_required": "Bachelor of Science in Nursing",
        "critical_skills": skills[:2]
    }

def generate_individual_cross_reports():
    print("Generating Individual Refined Candidate Reports (Strict JSON)...")
    
    output_dir = "outputs/ats_individual"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load All 85 JDs
    jds_txt_dir = "data/processed/individual_jds_txt"
    jds_json_dir = "data/processed/jd_parsed_outputs"
    jd_txt_files = sorted([f for f in os.listdir(jds_txt_dir) if f.endswith(".txt")])
    all_jds = []
    
    print(f"Loading all {len(jd_txt_files)} Job Descriptions...")
    for jd_file in jd_txt_files:
        jd_json_name = jd_file.replace(".txt", ".json").replace(" ", "_")
        jd_json_path = os.path.join(jds_json_dir, jd_json_name)
        
        parsed_jd = None
        if os.path.exists(jd_json_path):
            with open(jd_json_path, 'r', encoding='utf-8') as f:
                raw_jd = json.load(f)
                parsed_jd = {
                    "job_title": raw_jd.get("job_title", "Unknown Role"),
                    "required_skills": raw_jd.get("requirements", {}).get("skills", {}).get("mandatory", []) or raw_jd.get("requirements", {}).get("skills", []),
                    "experience_required": raw_jd.get("requirements", {}).get("experience", {}).get("min_years", 2),
                    "education_required": raw_jd.get("requirements", {}).get("education", {}).get("min_degree", "Bachelors"),
                    "critical_skills": (raw_jd.get("requirements", {}).get("skills", {}).get("mandatory", []) or [])[:2]
                }
        else:
            parsed_jd = parse_txt_jd_fallback(os.path.join(jds_txt_dir, jd_file))
        all_jds.append(parsed_jd)
    
    # 2. Load Candidates
    resumes_dir = "data/samples/labeled"
    allowed_resumes = [f for f in os.listdir(resumes_dir) if f.endswith("_segmented.json")]
    
    for res_name in allowed_resumes:
        res_key = res_name.replace("_segmented.json", "")
        with open(os.path.join(resumes_dir, res_name), 'r', encoding='utf-8') as f:
            res_raw = json.load(f)
            
        # Parse Info
        skills_raw = res_raw.get("skills", "")
        skills_list = [s.strip() for s in skills_raw.replace("\n", ",").split(",") if s.strip()] if isinstance(skills_raw, str) else skills_raw
        
        certs_raw = res_raw.get("certifications", "")
        if certs_raw:
            skills_list.extend([c.strip() for c in certs_raw.replace("\n", ",").split(",") if c.strip()])

        exp_search = re.search(r'(\d+)\+?\s*years?', (res_raw.get("summary", "") + " " + res_raw.get("work_experience", "")), re.IGNORECASE)
        exp_years = int(exp_search.group(1)) if exp_search else 2

        resume_processed = {
            "name": res_key,
            "skills": list(set(skills_list)),
            "experience_years": exp_years,
            "education": res_raw.get("education", "Bachelors"),
            "resume_text": res_raw.get("summary", "")
        }

        print(f"  [+] Matching Candidate: {res_key} against 85 JDs...")
        
        cand_matches = []
        for jd in all_jds:
            semantic_score = 0.85 if any(k in jd["job_title"].lower() for k in ["nurse", "clinical", "health"]) else 0.2
            result = candidate_score_generator(resume_processed, jd, semantic_score)
            cand_matches.append(result)
            
        # Sort matches for this candidate: By Level priority then by Score
        def sort_key(x):
            priority = {"Strong Match": 3, "Moderate Match": 2, "Weak Match": 1}
            return (priority.get(x["match_level"], 0), x["final_score"])
            
        cand_matches.sort(key=sort_key, reverse=True)
        
        # Save One File per Candidate (Requirement: individual files in order)
        output_file = os.path.join(output_dir, f"{res_key.upper()}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cand_matches, f, indent=2, ensure_ascii=False)
            
    print(f"\nCOMPLETED. Refined individual reports saved to: {output_dir}")

if __name__ == "__main__":
    generate_individual_cross_reports()
