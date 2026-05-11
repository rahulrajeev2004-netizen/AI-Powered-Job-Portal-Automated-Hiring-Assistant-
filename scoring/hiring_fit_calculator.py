from typing import Dict, Any, Optional
from .unified_models import UnifiedCandidateScore, CandidateScores, HiringFit
from .intelligence_engine import IntelligenceEngine

class HiringIntelligenceSystem:
    """
    Main entry point for the improved Hiring Intelligence Scoring System.
    Coordinates parsing, independent scoring, and final fit calibration.
    """
    
    ROLE_WEIGHTS = {
        "software engineer": {"ats": 0.25, "screening": 0.50, "hr": 0.25},
        "hr role": {"ats": 0.20, "screening": 0.20, "hr": 0.60},
        "data analyst": {"ats": 0.35, "screening": 0.40, "hr": 0.25},
        "default": {"ats": 0.30, "screening": 0.30, "hr": 0.40}
    }

    @classmethod
    def process_candidate(
        cls,
        candidate_filename: str,
        job_role: str,
        structured_data: Dict[str, Any],
        job_reqs: Dict[str, Any]
    ) -> UnifiedCandidateScore:
        """
        Processes a candidate through the full intelligence pipeline.
        """
        # 1. Independent ATS Scoring
        ats_result = IntelligenceEngine.calculate_ats_score(structured_data, job_reqs)
        ats_score = ats_result["score"]
        
        # 2. Independent Screening Scoring
        screening_score = IntelligenceEngine.calculate_screening_score(candidate_filename, job_role)
        
        # 3. Independent HR Scoring
        hr_score = IntelligenceEngine.calculate_hr_score(candidate_filename)
        
        # 4. Role-based Weight Selection
        weights = cls.ROLE_WEIGHTS.get(job_role.lower(), cls.ROLE_WEIGHTS["default"])
        
        # 5. Final Score Calculation
        final_score = (
            (ats_score * weights["ats"]) +
            (screening_score * weights["screening"]) +
            (hr_score * weights["hr"])
        )
        final_score = round(final_score, 2)
        
        # 6. Hiring Fit Intelligence
        fit_result = IntelligenceEngine.calculate_hiring_fit(final_score, ats_result["details"], hr_score)
        
        # Construct the unified object with ONLY requested fields
        return UnifiedCandidateScore(
            candidate_id=candidate_filename,
            scores=CandidateScores(
                ats=ats_score,
                screening=screening_score,
                hr=hr_score
            ),
            weights=weights,
            final_score=final_score,
            decision=fit_result["category"],
            hiring_fit=HiringFit(
                percentage=fit_result["percentage"],
                category=fit_result["category"]
            )
        )
