import os
import json
import sys

sys.path.append(os.getcwd())
from engines.experience_analyzer.experience_analyzer import ExperienceAnalyzer
from parsers.jd_parser import parse_jd
from utils.logger import get_logger

logger = get_logger("txt_jd_match", "logs/master_match.log")


def run_txt_jd_match():
    """
    Compare all segmented resumes ONLY against user-provided TXT Job Descriptions.
    JD source: data/processed/individual_jds_txt/ (85 TXT files)
    """
    resume_dir = "data/samples/labeled"
    jd_txt_dir = "data/processed/individual_jds_txt"
    output_path = "data/processed/master_experience_report.json"
    split_dir = "data/processed/candidate_experience_reports"

    os.makedirs(split_dir, exist_ok=True)

    # 1. Load specific target resumes only (5 autorized)
    allowed_resumes = {
        "Nurse_Resume_Anita_Mathew_segmented.json",
        "Rahul_segmented.json",
        "Reshma resume_segmented.json",
        "nurse_resume_segmented.json",
        "sample_2_segmented.json"
    }

    resume_files = [f for f in os.listdir(resume_dir) if f in allowed_resumes]
    resumes = []
    for f in resume_files:
        with open(os.path.join(resume_dir, f), 'r', encoding='utf-8') as file:
            resumes.append({"filename": f, "data": json.load(file)})

    # 2. Parse ONLY the user-provided TXT Job Descriptions
    jd_txt_files = sorted([f for f in os.listdir(jd_txt_dir) if f.endswith(".txt")])
    jds = []
    print(f"Parsing {len(jd_txt_files)} TXT Job Descriptions...")
    for f in jd_txt_files:
        path = os.path.join(jd_txt_dir, f)
        with open(path, 'r', encoding='utf-8') as file:
            raw_text = file.read()
        parsed_jd = parse_jd(raw_text)
        # If parser couldn't extract a job title, use the filename
        if not parsed_jd.get("job_title"):
            parsed_jd["job_title"] = f.replace(".txt", "").replace("_", " ").strip()
            # Remove leading number prefix like "01 Staff Nurse" → "Staff Nurse"
            parsed_jd["job_title"] = " ".join(parsed_jd["job_title"].split()[1:])
        jds.append(parsed_jd)

    analyzer = ExperienceAnalyzer(current_date="2026-03")

    print(f"\nComparing {len(resumes)} Resumes vs {len(jds)} TXT JDs (ONLY user-provided)...")

    master_results = []

    for res in resumes:
        res_data = res["data"]

        # Extract candidate name
        contact_raw = str(res_data.get("contact_info", res["filename"]))
        res_name = contact_raw.split('\n')[0].strip()

        # Compute total_experience_months ONCE (propagated to ALL matches)
        resume_lower = {k.lower(): v for k, v in res_data.items()}
        exp_text = str(resume_lower.get("work_experience", "") or resume_lower.get("experience", ""))
        total_months = analyzer.extract_experience_months(exp_text)

        candidate_report = {
            "candidate_name": res_name,
            "total_experience_months": total_months,
            "jd_source": "data/processed/individual_jds_txt/ (85 TXT files only)",
            "matches": []
        }

        for jd in jds:
            match_data = analyzer.analyze(res_data, jd, total_exp_override=total_months)
            # Show ALL 85 results, no filters
            candidate_report["matches"].append(match_data)

        # Sort DESC - show ALL 85 JD comparisons (no limit)
        candidate_report["matches"].sort(key=lambda x: x["relevance_score"], reverse=True)

        top_title = candidate_report["matches"][0]["job_title"] if candidate_report["matches"] else "None"
        top_score = candidate_report["matches"][0]["relevance_score"] if candidate_report["matches"] else 0.0
        print(f"  [+] {res_name} | Exp: {total_months}m | Top: {top_title} ({top_score})")

        master_results.append(candidate_report)

        # Save individual report
        safe_name = "".join(c if c.isalnum() else "_" for c in res_name.split('\n')[0].strip())
        ind_path = os.path.join(split_dir, f"{safe_name}_Master_Matches.json")
        with open(ind_path, 'w', encoding='utf-8') as f:
            json.dump(candidate_report, f, indent=2, ensure_ascii=False)
        print(f"     Saved: {ind_path}")

    # Save master report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(master_results, f, indent=2, ensure_ascii=False)

    print(f"\nDone!")
    print(f"Master report: {output_path}")
    print(f"Individual reports: {split_dir}/")


if __name__ == "__main__":
    run_txt_jd_match()
