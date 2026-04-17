from app.core import logic
from app import models, database
from sqlalchemy.orm import Session

def test_logic():
    print("Testing logic.score_candidates...")
    mock_candidates = [
        {
            "candidate_id": "test_1",
            "resume_text": "Sample resume content",
            "skills": ["Python", "SQL"],
            "experience_years": 5.0,
            "education": "B.Tech"
        }
    ]
    job_desc = "Looking for a Python developer with SQL experience."
    
    try:
        result = logic.score_candidates(mock_candidates, job_desc)
        print("Success! Result keys:", result.keys())
    except Exception as e:
        print(f"FAILED with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_logic()
