import json
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.eligibility_engine import EligibilityEngine

def run_test():
    # 1. Mock Job Rules Configuration
    job_rules = {
        "job_id": "JD-001",
        "job_title": "Senior AI Engineer",
        "min_score": 0.75,
        "mandatory_skills": ["Python", "PyTorch"],
        "min_experience": 3.0,
        "max_experience": 10.0,
        "allowed_locations": ["Remote", "New York", "San Francisco"],
        "availability_required": True,
        "review_score_range": [0.5, 0.75]
    }

    # 2. Mock ATS Candidate Output
    candidates = [
        {
            "candidate_id": "C-001",
            "final_score": 0.85,
            "skills": ["Python", "PyTorch", "NLP"],
            "experience": 5.0,
            "location": "Remote",
            "available": True
        },
        {
            "candidate_id": "C-002",
            "final_score": 0.80,
            "skills": ["Python", "SQL"], # Missing PyTorch
            "experience": 6.0,
            "location": "New York",
            "available": True
        },
        {
            "candidate_id": "C-003",
            "final_score": 0.60, # In review range
            "skills": ["Python", "PyTorch"],
            "experience": 4.0,
            "location": "San Francisco",
            "available": True
        },
        {
            "candidate_id": "C-004",
            "final_score": 0.90,
            "skills": ["Python", "PyTorch"],
            "experience": 12.0, # Too much experience
            "location": "London",
            "available": True
        },
        {
            "candidate_id": "C-005",
            "final_score": 0.82,
            "skills": ["Python", "PyTorch"],
            "experience": 4.5,
            "location": "Mumbai", # Location check fail -> Review
            "available": True
        },
        {
            "candidate_id": "C-006",
            "final_score": 0.40, # Below review range -> Rejected
            "skills": ["Python", "PyTorch"],
            "experience": 3.5,
            "location": "Remote",
            "available": True
        },
        {
            "candidate_id": "C-007",
            "final_score": 0.88,
            "skills": ["Python", "PyTorch"],
            "experience": 4.0,
            "location": "Remote",
            "available": False # Not available -> Review
        }
    ]

    # 3. Process Decisions
    engine = EligibilityEngine(job_rules)
    output = engine.process_batch(candidates)

    # 4. Save and Print Output
    output_path = os.path.join("outputs", "eligibility_decisions_test.json")
    os.makedirs("outputs", exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Eligibility decisions generated and saved to {output_path}")
    print("\nDecision Summary:")
    print(json.dumps(output["decision_summary"], indent=2))
    
    print("\nDetailed Decisions:")
    for cand in output["candidates"]:
        print(f"- {cand['candidate_id']}: {cand['eligibility_status']} | Action: {cand['next_action']}")
        print(f"  Reasons: {cand['reasons']}")

if __name__ == "__main__":
    run_test()
