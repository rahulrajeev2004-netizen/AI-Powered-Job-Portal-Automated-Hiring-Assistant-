import re
from typing import List, Dict

class ScenarioEvaluator:
    """
    Evaluates situational judgment responses based on pattern matching.
    Logic:
    - Full match: 1.0
    - Partial match: 0.7
    - No match: 0.4
    """
    
    def __init__(self):
        self.reference_patterns = {
            "team_conflict": ["communicate", "understand", "resolve", "mediate", "listen"],
            "deadline_pressure": ["prioritize", "plan", "execute", "delegate", "time-management"],
            "learning": ["research", "practice", "apply", "learn", "study", "documentation"]
        }

    def analyze_response(self, text: str, scenario_type: str) -> float:
        """
        Calculates the pattern match score for a given scenario.
        """
        text_lower = text.lower()
        required_patterns = self.reference_patterns.get(scenario_type, [])
        
        if not required_patterns:
            return 0.5
            
        found_count = 0
        for pattern in required_patterns:
            # Match whole words only
            if re.search(rf'\b{pattern}\b', text_lower):
                found_count += 1
        
        # Original Logic: Full match = 1.0, Any match = 0.7, None = 0.4
        # We'll use the core patterns for the "Full match" logic (first 3 usually)
        core_patterns = required_patterns[:3]
        core_matches = sum(1 for p in core_patterns if re.search(rf'\b{p}\b', text_lower))
        
        if core_matches == len(core_patterns):
            return 1.0
        elif found_count > 0:
            return 0.7
        return 0.4

    def batch_evaluate(self, scenarios: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluates multiple scenario responses.
        """
        results = []
        for item in scenarios:
            score = self.analyze_response(item.get("text", ""), item.get("type", ""))
            results.append({
                "type": item.get("type"),
                "score": score
            })
        return {"scenario_results": results}
