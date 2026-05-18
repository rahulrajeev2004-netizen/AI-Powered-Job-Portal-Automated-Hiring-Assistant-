import json
from typing import Dict, List, Any, Tuple

class TechnicalScorer:
    """
    Evaluates depth of technical knowledge beyond surface-level answers.
    Handles accuracy, depth, logical reasoning, and real-world applicability.
    """
    def __init__(self):
        # Define scoring rubric per question type
        self.rubrics = {
            "conceptual": {
                "accuracy": 0.4,
                "depth": 0.4,
                "reasoning": 0.1,
                "real_world": 0.1
            },
            "scenario": {
                "accuracy": 0.2,
                "depth": 0.3,
                "reasoning": 0.3,
                "real_world": 0.2
            },
            "coding": {
                "accuracy": 0.5,
                "depth": 0.1,
                "reasoning": 0.2,
                "real_world": 0.2
            }
        }
        
    def _detect_shallow_vs_deep(self, answer: str) -> Tuple[float, str]:
        """
        Detects if an answer is shallow or deep based on technical elaboration.
        Returns (depth_score, explanation)
        """
        words = len(answer.split())
        # Simplified detection based on length and keywords (simulating NLP depth analysis)
        technical_keywords = [
            "because", "therefore", "however", "in contrast", "optimize", 
            "complexity", "trade-off", "scale", "performance", "pattern", 
            "architecture", "manage", "efficient", "lazy", "splitting"
        ]
        keyword_count = sum(1 for kw in technical_keywords if kw in answer.lower())
        
        if words < 15 and keyword_count == 0:
            return 0.2, "Surface-level answer. Lacks technical elaboration and detail."
        elif words < 30 and keyword_count < 2:
            return 0.5, "Moderate depth. Provides basic concepts but lacks detailed technical nuance."
        else:
            return 0.9, "Deep technical answer. Explains concepts with strong technical vocabulary and elaboration."

    def _evaluate_accuracy(self, answer: str) -> float:
        """Simulates checking factual accuracy. In production, this uses an LLM."""
        words = len(answer.split())
        if words > 10:
            return 0.85
        return 0.4

    def _evaluate_reasoning(self, answer: str) -> float:
        """Simulates evaluating logical reasoning and thought process."""
        keywords = ["if", "then", "because", "lead to", "results in", "therefore", "manage", "efficiently"]
        return min(1.0, sum(0.2 for kw in keywords if kw in answer.lower()) + 0.3)

    def _evaluate_real_world(self, answer: str) -> float:
        """Simulates evaluating real-world applicability and practical knowledge."""
        keywords = ["production", "scale", "user", "load", "database", "latency", "deployment", "experience", "performance"]
        return min(1.0, sum(0.2 for kw in keywords if kw in answer.lower()) + 0.1)

    def _normalize_score(self, raw_score: float, difficulty: str) -> float:
        """Normalizes scores across difficulty levels."""
        multipliers = {
            "entry_level": 0.85,  # Basic questions capped/penalized slightly
            "mid_level": 1.0,     # Baseline
            "senior_level": 1.15  # Complex questions receive a multiplier
        }
        mult = multipliers.get(difficulty, 1.0)
        return min(1.0, raw_score * mult)

    def evaluate_response(self, question_type: str, answer: str, difficulty: str = "mid_level") -> Dict[str, Any]:
        """Evaluates a single answer and returns detailed explainable scoring."""
        rubric = self.rubrics.get(question_type, self.rubrics["conceptual"])
        
        accuracy = self._evaluate_accuracy(answer)
        depth, depth_explanation = self._detect_shallow_vs_deep(answer)
        reasoning = self._evaluate_reasoning(answer)
        real_world = self._evaluate_real_world(answer)
        
        raw_score = (
            accuracy * rubric["accuracy"] +
            depth * rubric["depth"] +
            reasoning * rubric["reasoning"] +
            real_world * rubric["real_world"]
        )
        
        normalized_score = self._normalize_score(raw_score, difficulty)
        
        # Determine quality marker for adaptive engine
        quality = "empty"
        if normalized_score > 0.75: quality = "good"
        elif normalized_score > 0.4: quality = "basic"
        elif normalized_score > 0: quality = "too_short"
        
        return {
            "parameters": {
                "accuracy": round(accuracy, 2),
                "depth": round(depth, 2),
                "logical_reasoning": round(reasoning, 2),
                "real_world_applicability": round(real_world, 2)
            },
            "explanations": {
                "depth_analysis": depth_explanation,
                "rubric_applied": question_type
            },
            "raw_score": round(raw_score, 2),
            "normalized_score": round(normalized_score, 2),
            "difficulty_level": difficulty,
            "question_type": question_type,
            "quality": quality,
            "confidence": 0.90 # Simulated transcription/extraction confidence
        }

class TechnicalReportGenerator:
    """Generates the final Technical Evaluation Report and Skill-wise breakdown."""
    
    def generate_report(self, candidate_name: str, role: str, evaluations: List[Dict[str, Any]], skills: List[str]) -> Dict[str, Any]:
        """Builds a structured output report for the candidate's technical round."""
        if not evaluations:
            return {}
            
        total_score = sum(ev["normalized_score"] for ev in evaluations) / len(evaluations)
        
        # Format breakdown array
        breakdown = []
        for i, ev in enumerate(evaluations):
            depth_val = ev["parameters"]["depth"]
            depth_label = "deep" if depth_val >= 0.7 else ("moderate" if depth_val >= 0.4 else "shallow")
            breakdown.append({
                "question_id": f"Q{i+1}",
                "score": round(ev["normalized_score"] * 100, 1),
                "depth": depth_label,
                "explanation": ev["explanations"]["depth_analysis"]
            })
            
        # Format skills dictionary
        skill_dict = {}
        for idx, skill in enumerate(skills):
            # In a real scenario, map specific questions to specific skills.
            variance = (idx % 3 - 1) * 0.05
            skill_score = min(1.0, max(0.0, total_score + variance))
            skill_dict[skill] = round(skill_score * 100, 1)
            
        # Dynamic strengths and weaknesses based on average parameters
        strengths = []
        weaknesses = []
        avg_reasoning = sum(ev["parameters"]["logical_reasoning"] for ev in evaluations) / len(evaluations)
        avg_real_world = sum(ev["parameters"]["real_world_applicability"] for ev in evaluations) / len(evaluations)
        
        if avg_reasoning > 0.5:
            strengths.append("Strong problem-solving")
        else:
            weaknesses.append("Needs improvement in logical reasoning")
            
        if avg_real_world > 0.4:
            strengths.append("Good system thinking")
        else:
            weaknesses.append("Limited optimization discussion")
            
        if not strengths:
            strengths.append("Basic syntax understanding")
            
        # Format Decision
        if total_score >= 0.8:
            decision = "Strong Technical Fit"
        elif total_score >= 0.6:
            decision = "Technical Fit"
        else:
            decision = "Not a Technical Fit"
            
        return {
            "candidate_id": "C3001",
            "technical_score": round(total_score * 100, 1),
            "decision": decision,
            "breakdown": breakdown,
            "skills": skill_dict,
            "strengths": strengths,
            "weaknesses": weaknesses
        }
