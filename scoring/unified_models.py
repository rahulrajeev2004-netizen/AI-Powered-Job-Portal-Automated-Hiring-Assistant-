from pydantic import BaseModel, Field
from typing import Dict

class CandidateScores(BaseModel):
    ats: float = Field(..., description="ATS score")
    screening: float = Field(..., description="Screening score")
    hr: float = Field(..., description="HR interview score")

class HiringFit(BaseModel):
    percentage: float = Field(..., description="Unified hiring fit percentage")
    category: str = Field(..., description="Fit category")

class UnifiedCandidateScore(BaseModel):
    candidate_id: str = Field(..., description="Resume filename")
    scores: CandidateScores = Field(..., description="Independent round scores")
    weights: Dict[str, float] = Field(..., description="Applied role weights")
    final_score: float = Field(..., description="Weighted aggregate score")
    decision: str = Field(..., description="Final hiring decision")
    hiring_fit: HiringFit = Field(..., description="Intelligence fit analysis")
