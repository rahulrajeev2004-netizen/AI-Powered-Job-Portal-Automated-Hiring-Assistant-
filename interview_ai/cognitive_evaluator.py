import random
from typing import Dict, Any, List
from .aptitude_scoring import AptitudeScorer
from .scenario_evaluator import ScenarioEvaluator

class CognitiveEvaluator:
    """
    Unified Engine for Cognitive and Situational Evaluation.
    Integrates AptitudeScorer and ScenarioEvaluator.
    """
    
    def __init__(self):
        self.aptitude_engine = AptitudeScorer()
        self.scenario_engine = ScenarioEvaluator()
        
        # Scenario questions for the interview flow
        self.question_bank = {
            "SIT_1": {"type": "deadline_pressure", "text": "You discover a critical bug in production right before a major client demo. Your team lead is unreachable. What steps do you take?"},
            "SIT_2": {"type": "team_conflict", "text": "Two key stakeholders have completely conflicting requirements for a feature you are building. How do you resolve this?"},
            "SIT_3": {"type": "learning", "text": "You are assigned a project with a technology you have never used before and the deadline is tight. How do you proceed?"}
        }

    def design_reasoning_question(self, role_type: str = "general") -> Dict[str, Any]:
        """Selects a situational scenario from the bank."""
        scenario_id = random.choice(list(self.question_bank.keys()))
        scenario = self.question_bank[scenario_id]
        return {
            "scenario_id": scenario_id,
            "type": scenario["type"],
            "question_text": scenario["text"]
        }

    def evaluate_candidate_cognition(self, candidate_id: str, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main entry point to evaluate cognitive and situational judgment.
        answers: list of dicts with 'scenario_id' and 'answer_text'
        """
        results = []
        total_score = 0.0
        
        for ans in answers:
            s_id = ans.get("scenario_id", "SIT_3")
            text = ans.get("answer_text", "")
            
            # 1. Evaluate specific scenario pattern matching
            scenario_info = self.question_bank.get(s_id, {"type": "learning"})
            scenario_score = self.scenario_engine.analyze_response(text, scenario_info["type"])
            
            # 2. Evaluate general aptitude logic (Structure, Problem Solving, Decision Quality)
            aptitude_metrics = self.aptitude_engine.score_response(text)
            
            # Combine scores (Scenario match is heavily weighted for situational judgment)
            # Final composite score for this specific answer
            answer_logic_score = (scenario_score * 0.5) + (aptitude_metrics["aptitude_score"] / 100.0 * 0.5)
            
            results.append({
                "scenario_id": s_id,
                "scenario_type": scenario_info["type"],
                "aptitude_breakdown": aptitude_metrics["breakdown"],
                "scenario_match_score": scenario_score,
                "composite_logic_score": round(answer_logic_score, 3)
            })
            total_score += answer_logic_score
            
        avg_score = round(total_score / len(answers), 3) if answers else 0.0
        
        # Categorization logic
        if avg_score > 0.75:
            band, insight = "Excellent", "Candidate demonstrates highly structured logic and strong situational judgment."
        elif avg_score > 0.55:
            band, insight = "Adequate", "Candidate shows functional reasoning but could improve structural clarity."
        else:
            band, insight = "Needs Improvement", "Candidate struggles with structured problem-solving and key situational patterns."
            
        return {
            "candidate_id": candidate_id,
            "cognitive_summary": {
                "overall_aptitude_score": avg_score,
                "cognitive_band": band,
                "insight": insight
            },
            "detailed_evaluations": results
        }
