from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class APIResponse(BaseModel):
    status: str
    data: Optional[Any] = None
    error: Optional[Dict] = None

class ResumeUploadResponse(BaseModel):
    resume_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    type: str

class CandidateResult(BaseModel):
    candidate_id: str
    original_score: float
    normalized_score: float
    adjusted_score: float
    rank: int

class ShortlistRequest(BaseModel):
    threshold: float
