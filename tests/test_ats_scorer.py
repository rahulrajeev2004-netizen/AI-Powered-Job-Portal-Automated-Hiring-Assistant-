import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scoring.ats_scorer import candidate_score_generator, batch_rank_jobs

def test_single_candidate_match():
    print("Testing Single Candidate Match...")
    
    candidate = {
        "name": "Jane Doe",
        "skills": ["Python", "Machine Learning", "Data Science", "SQL"],
        "experience_years": 5,
        "education": "Master of Computer Science",
        "resume_text": "Experienced data scientist with Python skills."
    }
    
    job = {
        "job_title": "AI Engineer",
        "required_skills": ["Python", "Machine Learning", "PyTorch", "NLP"],
        "experience_required": 4,
        "education_required": "Master",
        "job_text": "Seeking an AI engineer with Python and ML experience."
    }
    
    semantic_score = 0.85
    
    result = candidate_score_generator(candidate, job, semantic_score)
    print(f"Match Results: {json.dumps(result, indent=2)}")
    
    assert "final_score" in result
    assert result["match_level"] in ["Strong Match", "Moderate Match", "Weak Match"]
    print("Single Match Test Passed!\n")

def test_batch_processing():
    print("Testing Batch Processing...")
    
    candidate = {
        "name": "John Doe",
        "skills": ["Nurse", "Patient Care", "EMR"],
        "experience_years": 3,
        "education": "Bachelors in Nursing",
        "resume_text": "Registered nurse with patient care experience."
    }
    
    jobs = [
        {
            "job_title": "Senior Nurse",
            "required_skills": ["Nurse", "ICU", "Leadership"],
            "experience_required": 10,
            "education_required": "Master",
            "job_text": "Senior nurse role with ICU requirements."
        },
        {
            "job_title": "Registered Nurse",
            "required_skills": ["Nurse", "Patient Care"],
            "experience_required": 2,
            "education_required": "Bachelors",
            "job_text": "Entry-level registered nurse role."
        }
    ]
    
    semantic_scores = [0.4, 0.9]
    
    ranked_jobs = batch_rank_jobs(candidate, jobs, semantic_scores)
    print(f"Ranked Jobs: {json.dumps(ranked_jobs, indent=2)}")
    
    assert len(ranked_jobs) == 2
    assert ranked_jobs[0]["job_title"] == "Registered Nurse"
    print("Batch Processing Test Passed!\n")

if __name__ == "__main__":
    try:
        test_single_candidate_match()
        test_batch_processing()
        print("All tests passed successfully!")
    except Exception as e:
        print(f"Tests failed: {e}")
        sys.exit(1)
