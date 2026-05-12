import math
from typing import List, Dict, Union

class StableHREngine:
    """
    Provides statistically stable evaluation metrics by filtering outliers
    and applying consistent decision thresholds.
    """
    
    def __init__(self, hire_threshold: float = 75.0, review_threshold: float = 55.0):
        self.hire_threshold = hire_threshold
        self.review_threshold = review_threshold

    def calculate_robust_average(self, scores: List[float]) -> float:
        """
        Calculates a smoothed average by removing statistical outliers 
        using standard deviation instead of fixed distance.
        """
        if not scores:
            return 0.0
        
        n = len(scores)
        if n <= 2:
            return round(sum(scores) / n, 2)
            
        mean = sum(scores) / n
        variance = sum((x - mean) ** 2 for x in scores) / n
        std_dev = math.sqrt(variance)
        
        # Filter scores within 1.5 standard deviations (typical statistical outlier boundary)
        # Ensure a minimum absolute variance of 5.0 to prevent over-filtering tight clusters
        allowed_variance = max(1.5 * std_dev, 5.0)
        valid_scores = [s for s in scores if abs(s - mean) <= allowed_variance]
        
        if not valid_scores:
            return round(mean, 2)
            
        robust_avg = sum(valid_scores) / len(valid_scores)
        return round(robust_avg, 2)

    def determine_category(self, final_score: float) -> str:
        """Maps a numerical score to a stable categorical decision."""
        if final_score >= self.hire_threshold:
            return "Strong Hire"
        elif final_score >= self.review_threshold:
            return "Hold for Review"
        return "Do Not Proceed"

    def evaluate_candidate(self, round_scores: List[float]) -> Dict[str, Union[float, str]]:
        """
        End-to-end stable evaluation generating a final report dictionary.
        """
        stabilized_score = self.calculate_robust_average(round_scores)
        
        return {
            "calibrated_score": stabilized_score,
            "recommendation": self.determine_category(stabilized_score),
            "data_points_analyzed": len(round_scores)
        }
