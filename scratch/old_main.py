import os
import shutil
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import models, schemas, database
from app.core import logic

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ats_api")

app = FastAPI(
    title="Applicant Tracking System API",
    description="Production-ready backend for ATS with Resume Parsing and Fairness-aware Scoring",
    version="1.0.0"
)

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Ensure upload directory exists
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Helper for standard response
def standard_response(status="success", data=None, error=None):
    return {
        "status": status,
        "data": data,
        "error": error
    }

# Background Tasks
async def parse_resume_background(resume_id: str, queue_id: str, db: Session):
    try:
        job_item = db.query(models.JobQueue).filter(models.JobQueue.id == queue_id).first()
        if job_item:
            job_item.status = "processing"
            db.commit()

        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
        if not resume:
            logger.error(f"Resume {resume_id} not found for parsing")
            return

        resume.status = "processing"
        db.commit()

        logger.info(f"Starting parsing for resume {resume_id}")
        parsed_results = logic.parse_resume_task(resume.file_path)
        
        # Save parsed data
        parsed_data = models.ParsedData(
            resume_id=resume_id,
            skills=parsed_results.get("extracted_skills", []),
            experience=parsed_results.get("work_experience", ""),
            education=parsed_results.get("education", ""),
            experience_years=parsed_results.get("experience_years", 0.0)
        )
        db.add(parsed_data)
        
        resume.status = "completed"
        if job_item:
            job_item.status = "completed"
        db.commit()
        logger.info(f"Successfully parsed resume {resume_id}")

    except Exception as e:
        logger.error(f"Error parsing resume {resume_id}: {str(e)}")
        db.rollback()
        resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
        if resume:
            resume.status = "failed"
        job_item = db.query(models.JobQueue).filter(models.JobQueue.id == queue_id).first()
        if job_item:
            job_item.status = "failed"
        db.commit()

async def score_candidates_background(job_id: str, queue_id: str, db: Session):
    try:
        job_item = db.query(models.JobQueue).filter(models.JobQueue.id == queue_id).first()
        job_item.status = "processing"
        db.commit()

        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Get all completed resumes
        resumes = db.query(models.Resume).filter(models.Resume.status == "completed").all()
        if not resumes:
            logger.warning(f"No completed resumes found for scoring job {job_id}")
            job_item.status = "completed"
            db.commit()
            return

        # Prepare parsed data for logic
        parsed_resumes = []
        for r in resumes:
            if r.parsed_data:
                parsed_resumes.append({
                    "candidate_id": r.candidate_id,
                    "resume_id": r.id,
                    "skills": r.parsed_data.skills, # This is a list from SkillExtractor
                    "experience_years": r.parsed_data.experience_years or 0.0,
                    "education": str(r.parsed_data.education)
                })

        logger.info(f"Scoring {len(parsed_resumes)} candidates for job {job_id}")
        results = logic.score_candidates(parsed_resumes, job.job_description)

        # Clear old scores for this job
        db.query(models.Score).filter(models.Score.job_id == job_id).delete()

        # Save new scores
        for res in results:
            # Match resume_id from candidate_id
            resume_ref = next((r for r in resumes if r.candidate_id == res["candidate_id"]), None)
            if not resume_ref: continue

            score_entry = models.Score(
                resume_id=resume_ref.id,
                job_id=job_id,
                original_score=res["original_score"],
                normalized_score=res["normalized_score"],
                adjusted_score=res["adjusted_score"],
                rank=res["rank"]
            )
            db.add(score_entry)

        job_item.status = "completed"
        db.commit()
        logger.info(f"Successfully scored candidates for job {job_id}")

    except Exception as e:
        logger.error(f"Error scoring job {job_id}: {str(e)}")
        job_item = db.query(models.JobQueue).filter(models.JobQueue.id == queue_id).first()
        if job_item:
            job_item.status = "failed"
            db.commit()

# --- API Endpoints ---

@app.post("/api/v1/resumes/upload", response_model=schemas.APIResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    try:
        resume_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{resume_id}{file_ext}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_resume = models.Resume(
            id=resume_id,
            candidate_id=f"C_{resume_id[:8]}", # Simple mapping
            file_path=file_path,
            status="pending"
        )
        db.add(new_resume)
        db.commit()
        
        logger.info(f"Resume uploaded: {resume_id}")
        return standard_response(data={"resume_id": resume_id, "status": "uploaded"})
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=standard_response(status="error", error={"code": "UPLOAD_FAILED", "message": str(e)})
        )

@app.post("/api/v1/resumes/{resume_id}/parse", response_model=schemas.APIResponse)
async def trigger_parsing(resume_id: str, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.status == "processing":
        return standard_response(data={"status": "already processing"})

    # Track in JobQueue for status checks
    queue_id = str(uuid.uuid4())
    job_queue_item = models.JobQueue(
        id=queue_id,
        job_id=resume_id,
        status="pending",
        type="parse"
    )
    db.add(job_queue_item)
    db.commit()

    background_tasks.add_task(parse_resume_background, resume_id, queue_id, db)
    return standard_response(data={"resume_id": resume_id, "queue_id": queue_id, "status": "parsing started"})

@app.post("/api/v1/jobs/", response_model=schemas.APIResponse)
async def create_job(job_description: str, db: Session = Depends(database.get_db)):
    job_id = str(uuid.uuid4())
    new_job = models.Job(id=job_id, job_description=job_description)
    db.add(new_job)
    db.commit()
    return standard_response(data={"job_id": job_id})

@app.post("/api/v1/jobs/{job_id}/score", response_model=List[schemas.CandidateResult])
async def run_scoring(job_id: str, db: Session = Depends(database.get_db)):
    logger.info(f"Starting scoring for job_id: {job_id}")
    
    # 1. Fetch Job
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        logger.error(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # 2. Fetch Candidates (Completed Resumes)
    resumes = db.query(models.Resume).filter(models.Resume.status == "completed").all()
    if not resumes:
        logger.warning(f"No candidates found for job: {job_id}")
        raise HTTPException(status_code=400, detail="No completed candidates available for scoring")

    # 3. Prepare data for service layer
    parsed_resumes = []
    for r in resumes:
        if r.parsed_data:
            parsed_resumes.append({
                "candidate_id": r.candidate_id,
                "resume_id": r.id,
                "skills": r.parsed_data.skills,
                "experience_years": r.parsed_data.experience_years or 0.0,
                "education": str(r.parsed_data.education)
            })

    if not parsed_resumes:
        raise HTTPException(status_code=400, detail="Found candidates but they have no parsed data")

    # 4. Use service layer for scoring, normalization, bias adjustment, and ranking
    try:
        results = logic.score_candidates(parsed_resumes, job.job_description)
    except Exception as e:
        logger.error(f"Scoring failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scoring logic failed: {str(e)}")

    # 5. Persist scores for future shortlisting
    # Clear old scores for this job
    db.query(models.Score).filter(models.Score.job_id == job_id).delete()
    for res in results:
        resume_ref = next((r for r in resumes if r.candidate_id == res["candidate_id"]), None)
        if not resume_ref: continue
        
        score_entry = models.Score(
            resume_id=resume_ref.id,
            job_id=job_id,
            original_score=res["original_score"],
            normalized_score=res["normalized_score"],
            adjusted_score=res["adjusted_score"],
            rank=res["rank"]
        )
        db.add(score_entry)
    db.commit()

    logger.info(f"Successfully completed scoring for job_id: {job_id}. Candidates scored: {len(results)}")
    
    # Return STRICT List of results as requested
    return [
        schemas.CandidateResult(
            candidate_id=res["candidate_id"],
            original_score=res["original_score"],
            normalized_score=res["normalized_score"],
            adjusted_score=res["adjusted_score"],
            rank=res["rank"]
        ) for res in results
    ]

@app.post("/api/v1/jobs/{job_id}/shortlist", response_model=schemas.APIResponse)
async def shortlist_candidates(job_id: str, req: schemas.ShortlistRequest, db: Session = Depends(database.get_db)):
    # Use threshold from request or fallback to mandatory 0.6
    THRESHOLD = req.threshold if req.threshold > 0 else 0.6
    logger.info(f"Filtering shortlist for job {job_id} with threshold {THRESHOLD}")
    
    # 1. Fetch ALL scores for this job to compute filtering
    all_scores = db.query(models.Score).filter(models.Score.job_id == job_id).order_by(models.Score.adjusted_score.desc()).all()
    if not all_scores:
        raise HTTPException(status_code=404, detail="No scores found for this job. Run /score first.")

    # 2. Filter by threshold
    shortlisted = [s for s in all_scores if s.adjusted_score >= THRESHOLD]
    
    # 3. EDGE CASE: If no candidates meet threshold -> Return TOP 1
    if not shortlisted and all_scores:
        logger.info("No candidates met threshold. Falling back to top 1 candidate.")
        shortlisted = all_scores[:1]

    # MANDATORY DEBUG LOGGING
    print(f"\n[DEBUG SHORTLIST] Job: {job_id}")
    print(f"Total candidates: {len(all_scores)}")
    print(f"Shortlisted: {len(shortlisted)}")

    results = []
    for i, s in enumerate(shortlisted):
        results.append({
            "candidate_id": s.resume.candidate_id,
            "original_score": s.original_score,
            "normalized_score": s.normalized_score,
            "adjusted_score": s.adjusted_score,
            "rank": i + 1
        })

    print(f"[DEBUG SHORTLIST] End\n")

    return standard_response(data={"candidates": results})

@app.get("/api/v1/jobs/{job_id}/results", response_model=List[schemas.CandidateResult])
async def get_scoring_results(job_id: str, db: Session = Depends(database.get_db)):
    """Retrieve already computed scoring results for a job."""
    scores = db.query(models.Score).filter(models.Score.job_id == job_id).order_by(models.Score.rank).all()
    if not scores:
        raise HTTPException(status_code=404, detail="No scores found for this job. Run /score first.")

    return [
        schemas.CandidateResult(
            candidate_id=s.resume.candidate_id,
            original_score=s.original_score,
            normalized_score=s.normalized_score,
            adjusted_score=s.adjusted_score,
            rank=s.rank
        ) for s in scores
    ]

@app.get("/api/v1/jobs/status/{job_id}", response_model=schemas.APIResponse)
async def check_job_status(job_id: str, db: Session = Depends(database.get_db)):
    # 1. Check JobQueue for recent background tasks
    job_queue_items = db.query(models.JobQueue).filter(models.JobQueue.job_id == job_id).order_by(models.JobQueue.id.desc()).all()
    if job_queue_items:
        item = job_queue_items[0]
        return standard_response(data={"job_id": job_id, "status": item.status, "type": item.type})

    # 2. Check if job_id is actually a resume_id and return its status
    resume = db.query(models.Resume).filter(models.Resume.id == job_id).first()
    if resume:
        return standard_response(data={"job_id": job_id, "status": resume.status, "type": "parse"})

    # 3. Check if there are scores for this job (for synchronous scoring fallback)
    scores_count = db.query(models.Score).filter(models.Score.job_id == job_id).count()
    if scores_count > 0:
        return standard_response(data={"job_id": job_id, "status": "completed", "type": "score"})

    # 4. Final fallback error
    logger.warning(f"Status requested for unknown ID: {job_id}")
    raise HTTPException(status_code=404, detail="Status not found for the given ID")

# Swagger UI fallback
@app.get("/", include_in_schema=False)
async def docs_redirect():
    return JSONResponse(status_code=200, content={"message": "Visit /docs for API documentation"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
