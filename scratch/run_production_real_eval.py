import json
import os
import re
import sys
from typing import List, Dict, Any

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.eligibility_engine import EligibilityEngine

def parse_experience(experience_text: str) -> float:
    """Simple heuristic to extract years of experience."""
    if not experience_text:
        return 0.0
    # Look for patterns like "5+ years", "3 years", "experience in ... (2018-2020)"
    years = re.findall(r'(\d+)\+?\s*years?', experience_text, re.IGNORECASE)
    if years:
        return float(years[0])
    
    # Try to calculate from date ranges like (2018 - 2020)
    ranges = re.findall(r'\((\d{4})\s*[\-–]\s*(\d{4}|Present)\)', experience_text)
    total_years = 0
    for start, end in ranges:
        start_yr = int(start)
        if end.lower() == 'present':
            end_yr = 2026 # Assuming current year is 2026 per project context
        else:
            end_yr = int(end)
        total_years += (end_yr - start_yr)
    
    return float(total_years) if total_years > 0 else 0.5 # Default min if some text exists

def extract_location(contact_info: str) -> str:
    """Extract location from contact info."""
    if not contact_info:
        return "Unknown"
    # Look for "Location: Kochi, India" or similar
    # Sometimes it's just "Kochi, India" after a pipe
    parts = contact_info.split("|")
    for part in parts:
        if "location" in part.lower():
            return part.split(":")[-1].strip()
    
    # Fallback to last part if it looks like a city
    last_part = parts[-1].strip()
    if "," in last_part:
        return last_part
        
    return "Remote"

def run_production_eligibility():
    # 1. Load Day 20 Production Eval
    eval_path = "outputs/day20_production_eval.json"
    if not os.path.exists(eval_path):
        print(f"Error: {eval_path} not found.")
        return

    with open(eval_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    # 2. Load JDs for rules
    jd_summary_path = "data/processed/jd_parsed_outputs/SAMPLE_SUMMARY.json"
    with open(jd_summary_path, "r", encoding="utf-8") as f:
        all_jds = json.load(f)
    
    jd_map = {jd["job_id"]: jd for jd in all_jds}

    # 3. Cache Resumes
    resumes_dir = "data/samples/labeled"
    resume_map = {}
    for filename in os.listdir(resumes_dir):
        if filename.endswith("_segmented.json"):
            with open(os.path.join(resumes_dir, filename), "r", encoding="utf-8") as f:
                res_data = json.load(f)
                cid = filename.replace("_segmented.json", "")
                resume_map[cid] = res_data

    # 4. Process
    all_decisions = []
    
    # Use the locations found in resumes to populate allowed_locations if empty
    default_locations = ["kochi", "thiruvananthapuram", "india", "remote", "hospital"]

    for job_result in eval_data.get("results", []):
        job_id = job_result.get("job_id")
        job_title = job_result.get("job_title")
        
        actual_jd = jd_map.get(job_id, {})
        reqs = actual_jd.get("requirements", {})
        
        # Extract mandatory skills from JD data
        mandatory = reqs.get("skills", {}).get("mandatory", [])
        
        # Extract min experience if possible
        min_exp_req = 1.0 # Default
        exp_field = reqs.get("experience", {})
        if isinstance(exp_field, dict) and exp_field.get("min"):
            min_exp_req = float(exp_field.get("min"))
        elif isinstance(exp_field, (int, float)):
            min_exp_req = float(exp_field)
            
        job_rules = {
            "job_id": job_id,
            "job_title": job_title,
            "min_score": 0.65,
            "mandatory_skills": mandatory,
            "min_experience": min_exp_req,
            "max_experience": 20.0,
            "allowed_locations": default_locations, 
            "availability_required": False,
            "review_score_range": [0.40, 0.65] # Stricter rejection for low scores
        }
        
        engine = EligibilityEngine(job_rules)
        
        candidates_to_process = []
        for cand_eval in job_result.get("candidates", []):
            cid = cand_eval.get("candidate_id")
            res_info = resume_map.get(cid, {})
            
            # Combine skills from skills field and segmented text sections for better matching
            skills_field = res_info.get("skills", "")
            summary_field = res_info.get("summary", "")
            exp_field = res_info.get("work_experience", "")
            
            # Simple word-based skill extraction for mandatory check
            # This ensures if "Communication" is in summary but not in skills list, it's found
            full_text = f"{skills_field} {summary_field} {exp_field}".lower()
            
            # The engine expects a list of skills
            # We'll provide the exploded list plus words from text
            cand_skills_list = [s.strip().lower() for s in re.split(r'[,|\n]', skills_field) if s.strip()]
            
            experience_years = parse_experience(exp_field)
            location = extract_location(res_info.get("contact_info", ""))
            
            candidates_to_process.append({
                "candidate_id": cid,
                "final_score": cand_eval.get("final_score", 0.0),
                "skills": cand_skills_list + [word for word in full_text.split()], # Add words for fuzzy matching
                "experience": experience_years,
                "location": location,
                "available": True
            })
        
        job_decision = engine.process_batch(candidates_to_process)
        all_decisions.append(job_decision)

    # 5. Save
    final_output = {
        "batch_id": "PRODUCTION_ELIGIBILITY_DAY20_REFINED",
        "processed_at": "2026-04-20T10:50:00Z",
        "total_jobs": len(all_decisions),
        "results": all_decisions
    }
    
    output_path = "outputs/day20_eligibility_decisions_refined.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print(f"Refined decisions saved to: {output_path}")

if __name__ == "__main__":
    run_production_eligibility()
