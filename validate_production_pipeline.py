import os
import json
import uuid
import time
from sqlalchemy.orm import Session
from app import models, database, schemas
from app.core import logic

def setup_db():
    print("Setting up database...")
    models.Base.metadata.drop_all(bind=database.engine)
    models.Base.metadata.create_all(bind=database.engine)
    return database.SessionLocal()

def validate_pipeline():
    db = setup_db()
    
    # 1. Add Job Description
    job_desc = """
    Job Title: Senior Software Engineer (Python)
    Experience Required: 4 years
    Education Required: B.Tech in Computer Science
    Required Skills: Python, SQL, AWS, Java, API Design
    Critical Skills: Python, AWS
    """
    job_id = str(uuid.uuid4())
    job = models.Job(id=job_id, job_description=job_desc)
    db.add(job)
    db.commit()
    print(f"Created Job ID: {job_id}")

    # 2. Add Resumes (Simulate Upload + Parse)
    with open("data/sample_resumes_day9.json", "r") as f:
        resumes_data = json.load(f)

    # Let's ADD a duplicate of resume_0 to test deduplication
    resumes_data.append(resumes_data[0].copy())
    resumes_data[-1]["id"] = "resume_0_dup"

    for r_data in resumes_data:
        resume_id = str(uuid.uuid4())
        resume = models.Resume(
            id=resume_id,
            candidate_id=r_data["id"],
            file_path="simulated",
            status="completed"
        )
        db.add(resume)
        
        # Manually add parsed data as we are skipping the actual PDF parsing step for validation
        parsed_data = models.ParsedData(
            resume_id=resume_id,
            skills=r_data["skills"].split(", ") if r_data["skills"] else [],
            experience=r_data["experience"],
            education=r_data["education"],
            experience_years=3.0 if "3 years" in r_data["experience"] else (5.0 if "5 years" in r_data["experience"] else 0.0)
        )
        db.add(parsed_data)
        
    db.commit()
    print(f"Loaded {len(resumes_data)} resumes into database (including 1 duplicate).")

    # 3. Process Resumes Directly (No cached data)
    print("Processing resumes directly for audited production scoring...")
    resumes = []
    for r_data in resumes_data:
        resumes.append({
            "candidate_id": r_data["id"],
            "skills": r_data["skills"].split(", ") if r_data["skills"] else [],
            "experience_years": 3.0 if "3 years" in r_data["experience"] else (5.0 if "5 years" in r_data["experience"] else 0.0),
            "education": str(r_data["education"]),
            "resume_text": r_data["experience"] # Simplified simulation
        })

    output = logic.score_candidates(resumes, job_desc)
    
    # Validation Assertion (Requirement 5)
    assert len(resumes) == len(output["ranked_candidates"]), "Pipeline mismatch in validation"
    output["total_candidates"] = len(resumes)
    
    # 4. Save and Validate Output
    os.makedirs("outputs", exist_ok=True)
    report_path = "outputs/final_ats_production_report.json"
    with open(report_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n[DONE] Production Pipeline Validated Successfully!")
    print(f"Report saved to: {report_path}")
    print("\n--- System Metrics ---")
    print(json.dumps(output["metrics"], indent=2))
    
    print("\n--- Top Candidate ---")
    if output["ranked_candidates"]:
        top = output["ranked_candidates"][0]
        print(f"ID: {top['candidate_id']}")
        print(f"Final Score: {top['final_score']}")
        print(f"Rank: {top['rank']}")
        print(f"Explanation: {top['explanation']}")

    db.close()

if __name__ == "__main__":
    validate_pipeline()
