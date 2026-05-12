from typing import List

class RefinedScoringPipeline:
    """
    A pipeline for normalizing raw scores and calibrating them against 
    system confidence metrics to reduce automated evaluation bias.
    """

    @staticmethod
    def apply_min_max_scaling(raw_scores: List[float], target_max: float = 100.0) -> List[float]:
        """
        Normalizes a distribution of scores to a 0-target_max scale.
        Handles zero-variance edge cases gracefully to avoid DivisionByZero.
        """
        if not raw_scores:
            return []
            
        min_val = min(raw_scores)
        max_val = max(raw_scores)
        
        # Fallback for identical scores (zero variance)
        if max_val == min_val:
            fallback = target_max if max_val > 0 else 0.0
            return [fallback for _ in raw_scores]
            
        return [round(((s - min_val) / (max_val - min_val)) * target_max, 2) for s in raw_scores]

    @staticmethod
    def calibrate_with_confidence(score: float, confidence_level: float) -> float:
        """
        Adjusts a score based on the confidence of the evaluation.
        Uses a proportional weighting mechanism rather than a flat addition,
        assuming score and confidence_level are on a 0-100 scale.
        """
        normalized_confidence = min(max(confidence_level, 0.0), 100.0) / 100.0
        
        # Base retention of the original score is 85%.
        # The remaining 15% is scaled by the confidence level.
        # This penalizes low-confidence scores proportionally without flat offsets.
        base_retention = 0.85
        confidence_modifier = 0.15 * normalized_confidence
        
        calibrated = score * (base_retention + confidence_modifier)
        return round(calibrated, 2)

    def execute_pipeline(self, raw_scores: List[float], confidences: List[float]) -> List[float]:
        """
        Executes the full refinement pipeline: Normalization -> Confidence Calibration.
        """
        if len(raw_scores) != len(confidences):
            raise ValueError("Mismatched list lengths: scores and confidences must be equal length.")
            
        scaled_scores = self.apply_min_max_scaling(raw_scores)
        
        final_calibrated_scores = []
        for scaled, conf in zip(scaled_scores, confidences):
            final_calibrated_scores.append(self.calibrate_with_confidence(scaled, conf))
            
        return final_calibrated_scores
