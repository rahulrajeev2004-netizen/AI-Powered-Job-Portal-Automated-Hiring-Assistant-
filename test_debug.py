import json
import os
import sys

# Add current directory to sys.path
sys.path.append(os.getcwd())

from scoring.ats_scorer import candidate_score_generator
from ats_engine_optimizer import _extract_skill_list, _extract_experience_years

def test_rahul():
    with open("data/samples/labeled/Rahul_segmented.json", "r", encoding="utf-8") as f:
        resume = json.load(f)
    
    jd_processed = {
        "job_title": "Staff Nurse",
        "required_skills": ["patient care", "clinical documentation"],
        "experience_required": 2.0
    }
    
    resume_processed = {
        "candidate_id": "Rahul",
        "skills": _extract_skill_list(resume.get("skills", [])),
        "experience_years": _extract_experience_years(resume),
        "education": resume.get("education", "Bachelors"),
        "resume_text": "sample text",
    }
    
    print(f"Processing candidate: {resume_processed['candidate_id']}")
    try:
        res = candidate_score_generator(resume_processed, jd_processed)
        print("Success!")
        # print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rahul()
