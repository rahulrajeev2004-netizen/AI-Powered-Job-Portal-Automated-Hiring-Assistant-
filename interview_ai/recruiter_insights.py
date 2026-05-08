import re
import random
from typing import Dict, Any, List

class RecruiterInsightGenerator:
    """
    Enterprise Insight Engine: Converts raw AI scores into recruiter-ready professional narratives.
    """
    
    def __init__(self):
        self.cultural_fit_markers = {
            "collaboration": ["team", "colleague", "collaborate", "together", "mentor", "help", "share", "feedback", "group", "partnership"],
            "growth_mindset": ["learn", "improve", "feedback", "growth", "challenge", "new", "curious", "adaptive", "upskill", "evolve"],
            "ownership": ["responsible", "lead", "drove", "delivered", "outcome", "impact", "accountable", "took charge", "result"],
            "adaptability": ["flexible", "change", "pivoted", "adjusted", "fast-paced", "ambiguity", "versatile", "evolve"]
        }

    def _get_jitter(self) -> float:
        return random.uniform(-0.02, 0.02)

    def generate_strengths_weaknesses(self, scores: Dict[str, Any], behavioral: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extracts structured strengths and weaknesses based on score thresholds and behavioral signals."""
        strengths = []
        weaknesses = []
        
        # Strengths Logic
        if scores.get("technical_skills", 0) >= 80:
            strengths.append("Exceptional technical domain expertise validated through multi-layered evidence.")
        if scores.get("communication", 0) >= 80:
            strengths.append("High-clarity communicator with strong verbal precision and professional delivery.")
        if scores.get("consistency", 0) >= 90:
            strengths.append("Demonstrates impeccable factual reliability and alignment across all session segments.")
        if behavioral.get("behavioral_summary", {}).get("confidence_level") == "High":
            strengths.append("Maintains significant composure and executive presence during high-pressure questioning.")
            
        # Weaknesses Logic
        if scores.get("technical_skills", 0) < 65:
            weaknesses.append("Technical depth markers are below target; suggests a need for deeper core skill validation.")
        if scores.get("consistency", 0) < 75:
            weaknesses.append("Detected subtle informational variance, recommending secondary background verification.")
        if behavioral.get("behavioral_summary", {}).get("stress_level") == "High":
            weaknesses.append("Exhibits elevated stress markers in complex scenarios, which may impact performance in highly volatile roles.")
        if scores.get("communication", 0) < 60:
            weaknesses.append("Communication clarity is impacted by hesitation; may require additional support in client-facing interactions.")

        return {
            "strengths": strengths if strengths else ["No standout strengths detected in the current session."],
            "weaknesses": weaknesses if weaknesses else ["No critical professional weaknesses identified."]
        }

    def analyze_cultural_fit(self, qa_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes cultural fit indicators based on linguistic marker density."""
        text = " ".join([qa.get("answer", "") for qa in qa_data]).lower()
        
        indicators = {}
        for category, markers in self.cultural_fit_markers.items():
            matches = sum(1 for marker in markers if re.search(rf'\b{marker}\b', text))
            if matches >= 3:
                indicators[category] = "High"
            elif matches >= 1:
                indicators[category] = "Medium"
            else:
                indicators[category] = "Low"
            
        # Cultural Alignment Narrative
        if indicators["collaboration"] == "High" and indicators["growth_mindset"] == "High":
            narrative = "Strong cultural alignment: Candidate demonstrates a collaborative spirit and a proactive, learning-oriented mindset."
        elif indicators["ownership"] == "High":
            narrative = "Results-driven profile: Candidate emphasizes individual accountability and outcome-based delivery."
        elif indicators["adaptability"] == "High":
            narrative = "Agile professional: Candidate shows strong comfort with change and evolving requirements."
        else:
            narrative = "Standard professional alignment: Demonstrates baseline workplace etiquette and task-oriented focus."
            
        return {
            "category_ratings": indicators,
            "culture_fit_narrative": narrative
        }

    def generate_executive_summary(self, candidate_name: str, final_score: int, strengths: List[str], culture_narrative: str) -> str:
        """Generates a professional natural-language executive summary."""
        band = "Strong Candidate" if final_score >= 80 else ("Qualified" if final_score >= 65 else "Review Required")
        
        primary_strength = strengths[0] if strengths else "standard professional performance"
        
        summary = (
            f"Candidate {candidate_name} is currently classified as '{band}' with an aggregate score of {final_score}/100. "
            f"The primary driver for this evaluation is {primary_strength.lower().replace('.', '')}. "
            f"{culture_narrative} Overall, the candidate presents as a viable professional with {band.lower()} potential for the target role."
        )
        return summary

    def get_structured_template(self) -> str:
        """Returns the structured summary template for recruiters."""
        return """
## 📋 RECRUITER INSIGHT TEMPLATE

### 🎯 Executive Overview
- **Decision:** [Priority / Shortlist / Hold]
- **Rating:** [X/100]
- **Key Takeaway:** [One-sentence professional summary]

### 💪 Key Strengths
- [Strength 1]
- [Strength 2]

### 📉 Areas for Development
- [Weakness 1]
- [Weakness 2]

### 🤝 Cultural Alignment
- **Narrative:** [Cultural fit summary]
- **Markers:** [Collaboration: High | Growth: Med | Ownership: High]
"""
