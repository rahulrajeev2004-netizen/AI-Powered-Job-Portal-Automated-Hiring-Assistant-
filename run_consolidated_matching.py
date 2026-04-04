import os
import json
import sys
import re

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from scoring.ats_scorer import candidate_score_generator

def read_text(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def parse_txt_jd_fallback(filepath):
    """
    Fallback parser for TXT JDs that aren't yet in JSON format.
    """
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
        "requirements": {
            "skills": {"mandatory": skills},
            "experience": {"min_years": 2},
            "education": {"min_degree": "Bachelor of Science in Nursing"}
        }
    }

def generate_comprehensive_report():
    """
    Compares all resumes against ALL 85 JDs using the Day 13 ATS Scorer.
    Output: outputs/comprehensive_match_report.json
    """
    resumes_dir = "data/samples/labeled"
    jds_txt_dir = "data/processed/individual_jds_txt"
    jds_json_dir = "data/processed/jd_parsed_outputs"
    output_path = "outputs/comprehensive_match_report.json"
    
    os.makedirs("outputs", exist_ok=True)

    # 1. Load All 85 Job Descriptions
    jd_txt_files = sorted([f for f in os.listdir(jds_txt_dir) if f.endswith(".txt")])
    jds_to_process = []
    
    print(f"Collecting all {len(jd_txt_files)} Job Descriptions...")
    for jd_file in jd_txt_files:
        # Check for JSON version first
        jd_json_name = jd_file.replace(".txt", ".json").replace(" ", "_")
        jd_json_path = os.path.join(jds_json_dir, jd_json_name)
        
        parsed_jd = None
        if os.path.exists(jd_json_path):
            with open(jd_json_path, 'r', encoding='utf-8') as f:
                parsed_jd = json.load(f)
        else:
            # Use Fallback Parser
            parsed_jd = parse_txt_jd_fallback(os.path.join(jds_txt_dir, jd_file))
            
        jds_to_process.append(parsed_jd)

    # 2. Authorized Resumes
    allowed_resumes = [f for f in os.listdir(resumes_dir) if f.endswith("_segmented.json")]
    
    # 3. Processing
    all_candidate_matches = {}

    for res_name in allowed_resumes:
        res_key = res_name.replace("_segmented.json", "")
        all_candidate_matches[res_key] = []
        
        with open(os.path.join(resumes_dir, res_name), 'r', encoding='utf-8') as f:
            res_raw = json.load(f)
            
        # Extract Resume Info
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

        print(f"  [+] Matching {res_key} against {len(jds_to_process)} JDs...")

        for jd in jds_to_process:
            jd_processed = {
                "job_title": jd.get("job_title", "Unknown Role"),
                "required_skills": jd.get("requirements", {}).get("skills", {}).get("mandatory", []) or jd.get("requirements", {}).get("skills", []),
                "experience_required": jd.get("requirements", {}).get("experience", {}).get("min_years", 2),
                "education_required": jd.get("requirements", {}).get("education", {}).get("min_degree", "Bachelors"),
                "critical_skills": (jd.get("requirements", {}).get("skills", {}).get("mandatory", []) or [])[:2]
            }
            
            semantic_score = 0.85 if any(k in jd_processed["job_title"].lower() for k in ["nurse", "clinical", "health"]) else 0.2
            match_result = candidate_score_generator(resume_processed, jd_processed, semantic_score)
            all_candidate_matches[res_key].append(match_result)

        # Sort matches for this candidate: By Level priority then by Score
        # Match Level Hierarchy: Strong=3, Moderate=2, Weak=1
        def sort_key(x):
            level_map = {"Strong Match": 3, "Moderate Match": 2, "Weak Match": 1}
            return (level_map.get(x.get("match_level", "Weak Match"), 0), x.get("final_score", 0.0))
            
        all_candidate_matches[res_key].sort(key=sort_key, reverse=True)

    # 4. Save DUAL OUTPUT (Consolidated + Individual)
    # Master Consolidated Report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_candidate_matches, f, indent=2, ensure_ascii=False)
    
    # Individual Reports (Synced)
    individual_dir = "outputs/ats_individual"
    os.makedirs(individual_dir, exist_ok=True)
    for res_key, matches in all_candidate_matches.items():
        indiv_path = os.path.join(individual_dir, f"{res_key.upper()}.json")
        with open(indiv_path, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)

    print(f"\nCOMPLETED. {len(allowed_resumes)} candidates compared with {len(jds_to_process)} job descriptions.")
    print(f"Master Master Report: {output_path}")
    print(f"Individual Reports Synced in: {individual_dir}")

if __name__ == "__main__":
    generate_comprehensive_report()
