from typing import Dict, Any

class UnifiedScoringEngine:
    """
    Manages the default and role-specific weights for computing the unified candidate score.
    """
    
    _BASE_DISTRIBUTION = {
        "ats_weight": 0.30,
        "screening_weight": 0.30,
        "hr_weight": 0.40
    }

    _PROFILE_DISTRIBUTIONS = {
        "fresher": {
            "ats_weight": 0.25,
            "screening_weight": 0.35,
            "hr_weight": 0.40
        },
        "experienced": {
            "ats_weight": 0.35,
            "screening_weight": 0.25,
            "hr_weight": 0.40
        },
        "technical": {
            "ats_weight": 0.40,
            "screening_weight": 0.30,
            "hr_weight": 0.30
        },
        "non_technical": {
            "ats_weight": 0.20,
            "screening_weight": 0.30,
            "hr_weight": 0.50
        }
    }

    @classmethod
    def determine_weights(cls, candidate_type: str = "") -> Dict[str, float]:
        """
        Identifies and returns the correct weight profile for a given candidate type.
        """
        normalized_type = candidate_type.lower().strip()
        
        for profile, weights in cls._PROFILE_DISTRIBUTIONS.items():
            if profile in normalized_type:
                return weights
                
        return cls._BASE_DISTRIBUTION

    @classmethod
    def compute_weighted_aggregate(cls, ats: float, screening: float, hr: float, candidate_type: str = "") -> Dict[str, Any]:
        """
        Aggregates individual round scores into a unified final score using appropriate weights.
        """
        active_weights = cls.determine_weights(candidate_type)
        
        # Ensure values don't exceed expected 0-100 range logically
        safe_ats = max(0.0, min(100.0, ats))
        safe_screening = max(0.0, min(100.0, screening))
        safe_hr = max(0.0, min(100.0, hr))

        ats_contrib = safe_ats * active_weights["ats_weight"]
        screening_contrib = safe_screening * active_weights["screening_weight"]
        hr_contrib = safe_hr * active_weights["hr_weight"]
        
        aggregate_score = round(ats_contrib + screening_contrib + hr_contrib, 2)
        
        return {
            "total_score": aggregate_score,
            "ats_contribution": ats_contrib,
            "screening_contribution": screening_contrib,
            "hr_contribution": hr_contrib,
            "applied_weights": active_weights
        }
