import re
from typing import Dict, Any, List

class InterviewSummaryGenerator:
    """
    Advanced Summary Engine: Implements weighted scoring and narrative generation.
    Logic Mapping:
    - Weights: Communication (30%), Behavioral (30%), HR Performance (40%).
    - Thresholds: >=75 (Strong Hire), >=55 (Consider), <55 (Reject).
    """
    
    def __init__(self):
        self.grading_logic = {
            "excellent": 80,
            "substandard": 50,
            "confidence_floor": 60,
            "score_bands": [
                (75, "Strong Hire"),
                (55, "Consider"),
                (0, "Reject")
            ]
        }

    def _generate_narrative_flow(self, s: List[str], w: List[str], r: List[str], fit: str, decision: str) -> str:
        """Constructs a professional natural-language report."""
        parts = []
        
        # Strengths Section
        if s:
            parts.append(f"The candidate demonstrates {', '.join(s[:2])}.")
        else:
            parts.append("The candidate exhibits standard professional competencies.")
            
        # Weaknesses Section
        if w:
            parts.append(f"However, there are concerns such as {', '.join(w[:2])}.")
        else:
            parts.append("No significant technical or professional gaps were identified.")
            
        # Risks Section
        if r:
            parts.append(f"Risk factors include {', '.join(r)}.")
        else:
            parts.append("Risk assessment indicates a stable professional profile.")
            
        # Culture & Conclusion
        parts.append(f"Cultural fit is assessed as {fit}.")
        parts.append(f"Final Recommendation: {decision}.")
        
        return " ".join(parts)

    def generate_interview_summary(self, candidate_id: str, hr_scores: List[Dict], comm_data: Dict, behavior_data: Dict, answers: Any) -> Dict[str, Any]:
        """
        Synthesizes all interview signals into a recruiter-ready summary.
        """
        highlights = {"strengths": [], "weaknesses": [], "risks": [], "inconsistencies": []}
        
        # 1. Performance Analysis (HR Module)
        # Logic: Score >= 80 -> Strength | Score < 50 -> Weakness
        hr_raw_total = 0
        for item in hr_scores:
            val = item.get("final_score", 0)
            hr_raw_total += val
            q_ref = item.get("question_id", "General")
            
            if val >= self.grading_logic["excellent"]:
                highlights["strengths"].append(f"Strong performance in {q_ref}")
            elif val < self.grading_logic["substandard"]:
                highlights["weaknesses"].append(f"Weak response in {q_ref}")
                
        avg_hr = hr_raw_total / len(hr_scores) if hr_scores else 0
        
        # 2. Linguistic & Communication Analysis
        # Logic: Score >= 80 -> Strength | Score < 50 -> Weakness
        c_score = comm_data.get("communication_score", 0)
        if c_score >= self.grading_logic["excellent"]:
            highlights["strengths"].append("Excellent communication skills")
        elif c_score < self.grading_logic["substandard"]:
            highlights["weaknesses"].append("Poor communication clarity")
            
        # 3. Behavioral Integrity & Confidence
        # Logic: Confidence < 60 -> Risk | Contradiction -> Inconsistency
        b_score = behavior_data.get("behavioral_score", 0)
        conf_val = behavior_data.get("confidence", {}).get("confidence_score", 100)
        
        if conf_val < self.grading_logic["confidence_floor"]:
            highlights["risks"].append("Low confidence detected")
            
        if behavior_data.get("contradiction", False):
            highlights["inconsistencies"].append("Contradictory statements observed")
            
        # 4. Cultural Alignment (Keyword Search)
        # Logic: "team" presence -> Good | Else -> Moderate
        answer_pool = str(answers).lower()
        culture_fit = "Moderate"
        if "team" in answer_pool:
            culture_fit = "Good"
            highlights["strengths"].append("Shows teamwork orientation")
            
        # 5. Composite Final Scoring
        # Logic: (Comm * 0.3) + (Behavior * 0.3) + (HR Avg * 0.4)
        overall_score = (c_score * 0.3) + (b_score * 0.3) + (avg_hr * 0.4)
        
        # 6. Decision Mapping
        final_decision = "Reject"
        for threshold, label in self.grading_logic["score_bands"]:
            if overall_score >= threshold:
                final_decision = label
                break
                
        # 7. Final Assembly
        report = {
            "candidate_id": candidate_id,
            "overall_score": round(overall_score, 2),
            "decision": final_decision,
            "summary": {
                **highlights,
                "cultural_fit": culture_fit
            },
            "natural_language_summary": self._generate_narrative_flow(
                highlights["strengths"], 
                highlights["weaknesses"], 
                highlights["risks"], 
                culture_fit, 
                final_decision
            )
        }
        
        return report
