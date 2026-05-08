from typing import Dict, Any, List
import math
from .cognitive_evaluator import CognitiveEvaluator

class HREvaluationProcessor:
    """
    Evaluates candidate HR responses based on relevance, communication, 
    confidence, and consistency. Includes length normalization and explainability.
    """
    
    ROLE_WEIGHT_PROFILES = {
        "fresher": {
            "relevance": 0.20,
            "communication": 0.25,
            "confidence": 0.20,
            "consistency": 0.15,
            "aptitude": 0.20
        },
        "experienced": {
            "relevance": 0.30,
            "communication": 0.15,
            "confidence": 0.20,
            "consistency": 0.15,
            "aptitude": 0.20
        }
    }

    def __init__(self, candidate_experience_level: str = "fresher"):
        """Initialize with appropriate weights for the candidate's level."""
        profile = candidate_experience_level.lower()
        if profile not in self.ROLE_WEIGHT_PROFILES:
            profile = "fresher"
        self.active_weights = self.ROLE_WEIGHT_PROFILES[profile]
        self.cognitive_evaluator = CognitiveEvaluator()

    def _evaluate_consistency(self, answer_data: Dict[str, Any]) -> float:
        """Determines consistency score based on contradictions and vagueness."""
        has_contradiction = answer_data.get("contradiction", False)
        is_vague = answer_data.get("is_vague", False)
        
        if has_contradiction:
            return 0.3
        if is_vague:
            return 0.6
        return 1.0

    def process_single_answer(self, answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates the weighted HR score for a single question response."""
        
        # Extract metrics (normalizing communication and confidence to 0-1 scale)
        metrics = {
            "relevance": answer_data.get("relevance_score", 0.7),
            "communication": answer_data.get("communication_score", 70.0) / 100.0,
            "confidence": answer_data.get("confidence_score", 70.0) / 100.0,
            "consistency": self._evaluate_consistency(answer_data),
            "aptitude": answer_data.get("aptitude_score", 70.0) / 100.0
        }
        
        # Calculate the weighted total
        weighted_total = sum(
            metrics[metric_name] * weight_value 
            for metric_name, weight_value in self.active_weights.items()
        )
        
        return {
            "question_id": answer_data.get("question_id", "Q_UNKNOWN"),
            "component_scores": {k: round(v, 2) for k, v in metrics.items()},
            "answer_final_score": round(weighted_total * 100, 2)
        }

    def _get_explanation(self, metric: str, value: float) -> str:
        """Generates a human-readable explanation for a specific metric score."""
        if metric == "relevance":
            if value > 0.8: return "Highly relevant answers aligned with HR signals."
            if value > 0.5: return "Moderately relevant answers, missing some key context."
            return "Vague or irrelevant answers to HR questions."
        if metric == "communication":
            if value > 0.8: return "Clear, fluent, and well-structured communication."
            if value > 0.5: return "Acceptable communication, but may have some filler usage."
            return "Poor communication, high hesitation or grammar issues."
        if metric == "confidence":
            if value > 0.8: return "High confidence with minimal hedging or stress."
            if value > 0.5: return "Moderate confidence, some signs of uncertainty."
            return "Low confidence, frequent hesitations or stress indicators."
        if metric == "consistency":
            if value > 0.8: return "Strong consistency across answers, no contradictions."
            if value > 0.5: return "Minor inconsistencies or vague statements detected."
            return "Major contradictions or severe inconsistencies detected."
        return ""

    def _normalize_length(self, score: float, interview_length: int, optimal_length: int = 15) -> float:
        """
        Normalize score based on interview length (e.g. number of QA turns).
        Penalizes extremely short interviews while slightly scaling shorter ones.
        """
        if interview_length == 0:
            return 0.0
        
        # Heavy penalty for extremely short interviews
        if interview_length < 3:
            return round(score * 0.8, 2)  # 20% penalty
            
        # Logarithmic normalization
        length_factor = min(1.0, math.log1p(interview_length) / math.log1p(optimal_length))
        normalized = score * (0.9 + 0.1 * length_factor)
        
        return round(min(100.0, max(0.0, normalized)), 2)

    def _get_decision(self, score: float) -> str:
        if score >= 85: return "Strong Hire"
        elif score >= 70: return "Hire"
        elif score >= 50: return "Review"
        else: return "Reject"

    def format_hr_report(self, processed_answers: List[Dict[str, Any]], candidate_id: str = "UNKNOWN") -> Dict[str, Any]:
        """Builds the final HR score report in the requested standardized structure."""
        if not processed_answers:
            return {
                "candidate_id": candidate_id,
                "hr_interview_score": 0.0,
                "decision": "Reject",
                "breakdown": [],
                "summary": {
                    "avg_relevance": 0.0,
                    "avg_communication": 0.0,
                    "avg_confidence": 0.0,
                    "avg_consistency": 0.0
                }
            }
            
        interview_length = len(processed_answers)
        
        # Compute averages for the summary
        avg_relevance = sum(a["component_scores"]["relevance"] for a in processed_answers) / interview_length
        avg_communication = sum(a["component_scores"]["communication"] for a in processed_answers) / interview_length
        avg_confidence = sum(a["component_scores"]["confidence"] for a in processed_answers) / interview_length
        avg_consistency = sum(a["component_scores"]["consistency"] for a in processed_answers) / interview_length
        avg_aptitude = sum(a["component_scores"].get("aptitude", 0.0) for a in processed_answers) / interview_length
        
        # Generate cognitive report from raw answers
        cognitive_answers = []
        for ans in processed_answers:
            if "answer_text" in ans:
                cognitive_answers.append({
                    "scenario_id": ans.get("question_id"),
                    "answer_text": ans["answer_text"]
                })
        
        cognitive_report = self.cognitive_evaluator.evaluate_candidate_cognition(candidate_id, cognitive_answers)
        
        # Compute raw aggregate score
        total_accumulated = sum(ans["answer_final_score"] for ans in processed_answers)
        raw_score = total_accumulated / interview_length
        
        # Apply normalization
        normalized_score = self._normalize_length(raw_score, interview_length)
        
        # Build breakdown array
        breakdown = []
        for ans in processed_answers:
            breakdown.append({
                "question_id": ans["question_id"],
                "final_score": ans["answer_final_score"],
                "scores": ans["component_scores"]
            })
            
        return {
            "candidate_id": candidate_id,
            "hr_interview_score": normalized_score,
            "decision": self._get_decision(normalized_score),
            "breakdown": breakdown,
            "cognitive_evaluation": cognitive_report,
            "summary": {
                "avg_relevance": round(avg_relevance, 2),
                "avg_communication": round(avg_communication, 2),
                "avg_confidence": round(avg_confidence, 2),
                "avg_consistency": round(avg_consistency, 2),
                "avg_aptitude": round(avg_aptitude, 2)
            }
        }

    def compute_aggregate_score(self, processed_answers: List[Dict[str, Any]]) -> float:
        """Legacy compatibility wrapper for getting just the raw score."""
        if not processed_answers:
            return 0.0
        total_accumulated = sum(ans["answer_final_score"] for ans in processed_answers)
        return round(total_accumulated / len(processed_answers), 2)
