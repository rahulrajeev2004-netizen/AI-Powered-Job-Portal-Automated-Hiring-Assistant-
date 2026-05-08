import re
from typing import Dict, Any

class AptitudeScorer:
    """
    Evaluates candidate logic, problem-solving, and decision-making clarity.
    Logic:
    - Structure Detection (35%): Measures logical sequencing markers.
    - Problem-Solving (35%): Detects solution-oriented vocabulary.
    - Decision Quality (30%): Analyzes indicators of critical thinking.
    """
    
    def __init__(self):
        self.struct_markers = {
            "sequencing": ["first", "second", "then", "next", "finally", "subsequently", "initially"],
            "causality": ["because", "therefore", "consequently", "as a result", "hence", "thus"]
        }
        
        self.problem_markers = ["solution", "approach", "resolve", "fix", "strategy", "methodology", "mitigate", "tackle"]
        self.decision_markers = ["consider", "analyze", "evaluate", "compare", "weigh", "assess", "choice", "reasoning"]

    def _count_matches(self, text: str, keywords: list) -> int:
        """Helper to count occurrences of keywords with word boundary protection."""
        text_lower = text.lower()
        count = 0
        for word in keywords:
            # Using regex to ensure we match whole words only
            if re.search(rf'\b{word}\b', text_lower):
                count += 1
        return count

    def get_structure_rating(self, text: str) -> float:
        """
        Logic: 3+ markers = 1.0, 1+ markers = 0.7, 0 markers = 0.4
        """
        all_markers = self.struct_markers["sequencing"] + self.struct_markers["causality"]
        matches = self._count_matches(text, all_markers)
        
        if matches >= 3:
            return 1.0
        if matches >= 1:
            return 0.7
        return 0.4

    def get_problem_solving_rating(self, text: str) -> float:
        """
        Logic: Specific keywords = 1.0, Long descriptive answer = 0.7, Short/vague = 0.4
        """
        matches = self._count_matches(text, self.problem_markers)
        if matches >= 1:
            return 1.0
            
        word_count = len(text.split())
        if word_count > 10:
            return 0.7
        return 0.4

    def get_decision_rating(self, text: str) -> float:
        """
        Logic: Analytical keywords = 1.0, Attempt keywords ('try') = 0.7, Minimal = 0.4
        """
        matches = self._count_matches(text, self.decision_markers)
        if matches >= 1:
            return 1.0
            
        if "try" in text.lower():
            return 0.7
        return 0.4

    def score_response(self, text: str) -> Dict[str, Any]:
        """
        Calculates final aptitude score based on 35/35/30 weighting.
        """
        s_score = self.get_structure_rating(text)
        p_score = self.get_problem_solving_rating(text)
        d_score = self.get_decision_rating(text)
        
        # Weighted calculation
        final_val = (s_score * 0.35) + (p_score * 0.35) + (d_score * 0.30)
        
        return {
            "aptitude_score": round(final_val * 100, 2),
            "breakdown": {
                "logical_structure": round(s_score, 2),
                "problem_solving": round(p_score, 2),
                "decision_quality": round(d_score, 2)
            }
        }
