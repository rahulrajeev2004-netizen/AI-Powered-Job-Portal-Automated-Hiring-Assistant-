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

class ScoreDetail(BaseModel):
    score: float
    details: Optional[Dict[str, Any]] = None

class DomainRelevanceComponents(BaseModel):
    skill_overlap: float
    experience_alignment: float
    certification_match: float
    role_keyword_match: float

class DomainRelevanceDetail(BaseModel):
    computed_value: bool = True
    formula: str
    score: float
    components: DomainRelevanceComponents

class ScoreBreakdown(BaseModel):
    skills: float
    experience: float
    education: float
    domain_relevance: float

class NormalizationDetails(BaseModel):
    method: str
    original_range: Dict[str, float]
    factor: float

class CandidateResult(BaseModel):
    candidate_id: str
    final_score: float
    rank: int
    score_breakdown: ScoreBreakdown
    domain_relevance_detail: DomainRelevanceDetail
    fairness_adjustment: Dict[str, Any]
    matched_skills: List[str]
    missing_skills: List[str]
    audit_trace: Dict[str, Any]
    explanation: str

class RankingMetadata(BaseModel):
    tie_breaking_rule: str
    scoring_formula: str
    experience_scaling: str
    normalization: str
    fairness_application: str
    model_version: str = "v3.4 final production ATS"

class PipelineMetrics(BaseModel):
    processing_time_ms: float
    ranking_stability: str
    system_confidence: float

class ATSFinalResponse(BaseModel):
    job_summary: Dict[str, Any]
    total_candidates: int
    ranked_candidates: List[CandidateResult]
    ranking_metadata: RankingMetadata
    metrics: PipelineMetrics
    data_warning: Optional[str] = None

class ShortlistRequest(BaseModel):
    threshold: float
