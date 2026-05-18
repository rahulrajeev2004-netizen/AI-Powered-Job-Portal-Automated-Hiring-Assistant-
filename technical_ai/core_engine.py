import json
import os
import sys
from typing import Dict, List, Any, Optional

# Add project root to path so we can import Zecpath modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Project-specific imports
from interview_ai.adaptive_engine import AdaptiveDifficultyManager, QuestionDifficulty, AdaptiveQuestionBuilder
from interview_ai.question_generator import QuestionGenerator

def load_system_config() -> Dict[str, Any]:
    file_path = os.path.join(os.path.dirname(__file__), 'question_hierarchy.json')
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

class ProfileAlignmentModule:
    """1. Profile Alignment Module - Interfaces with semantic_matching and ATS data."""
    def __init__(self, config: Dict[str, Any]):
        self.domain_matrix = config.get("domain_skill_matrix", {})

    def extract_competencies(self, applied_role: str) -> List[str]:
        role_key = applied_role.lower().replace(" ", "_")
        return self.domain_matrix.get(role_key, ["General Software Engineering Principles"])

class TechnicalPromptGenerator(QuestionGenerator):
    """2. Prompt Generation Module - Subclasses existing Zecpath QuestionGenerator."""
    def __init__(self, config: Dict[str, Any]):
        # We don't call super().__init__() here because we are overriding the bank source
        self.tier_profiles = config.get("tier_profiles", [])

    def determine_tier(self, years_exp: float) -> Dict[str, Any]:
        for profile in self.tier_profiles:
            min_yr, max_yr = profile["years_range"]
            if min_yr <= years_exp <= max_yr:
                return profile
        return self.tier_profiles[-1] if self.tier_profiles else {}

    def construct_prompt(self, competencies: List[str], tier_info: Dict[str, Any]) -> str:
        focus = tier_info.get("focus_areas", ["general topics"])[0]
        primary_skill = competencies[0] if competencies else "coding"
        return f"Describe your approach to {focus} using {primary_skill}."

from technical_ai.technical_scoring import TechnicalScorer, TechnicalReportGenerator

class AssessmentPipeline:
    """Orchestrates the technical execution pipeline, extending Zecpath CallFlowEngine concepts."""
    def __init__(self, candidate_info: Dict[str, Any]):
        config = load_system_config()
        self.candidate = candidate_info
        
        self.aligner = ProfileAlignmentModule(config)
        self.prompter = TechnicalPromptGenerator(config)
        self.scorer = TechnicalScorer()
        self.report_generator = TechnicalReportGenerator()
        
        # We use the existing Zecpath Adaptive Engine instead of a custom one!
        self.adaptive_manager = AdaptiveDifficultyManager()
        self.adaptive_builder = AdaptiveQuestionBuilder()

    def run(self, candidate_responses: List[str]) -> Dict[str, Any]:
        role = self.candidate.get("role", "generic")
        exp_years = self.candidate.get("experience_years", 0)
        
        competencies = self.aligner.extract_competencies(role)
        tier_data = self.prompter.determine_tier(exp_years)
        
        interview_transcript = []
        
        # Base Question generated from Hierarchy
        base_prompt = self.prompter.construct_prompt(competencies, tier_data)
        
        evaluations = []
        
        for idx, response in enumerate(candidate_responses):
            # Evaluate Response using the new TechnicalScorer
            analysis = self.scorer.evaluate_response(
                question_type="conceptual", 
                answer=response,
                difficulty=tier_data.get("tier", "mid_level")
            )
            evaluations.append(analysis)
            
            # Utilize Zecpath's Adaptive Engine to determine next difficulty step
            next_difficulty_mode = self.adaptive_manager.determine_level(
                quality=analysis["quality"], 
                confidence_score=analysis["confidence"]
            )
            
            # Rebuild the question dynamically using Zecpath's builder
            next_prompt = self.adaptive_builder.build(base_prompt, next_difficulty_mode)
            
            interview_transcript.append({
                "turn": idx + 1,
                "user_response": response,
                "evaluated_quality": analysis["quality"],
                "adapted_next_prompt": next_prompt,
                "scoring_details": analysis
            })

        # Generate the final skill-wise technical report
        report = self.report_generator.generate_report(
            candidate_name=self.candidate.get("name", "Unknown"),
            role=role,
            evaluations=evaluations,
            skills=competencies
        )
        
        return report

if __name__ == "__main__":
    candidate = {
        "name": "Jordan Lee",
        "role": "mern_fullstack",
        "experience_years": 4
    }
    
    mock_responses = [
        "I use React.", # Very short -> quality = too_short -> should trigger SIMPLIFY
        "I use React with hooks to manage state efficiently.", # quality = basic -> should trigger EXAMPLE
        "I use React context API alongside custom hooks for scalable state management. To improve performance, I utilize lazy loading and code splitting." # quality = good -> should trigger ADVANCED
    ]
    
    pipeline = AssessmentPipeline(candidate)
    result = pipeline.run(mock_responses)
    
    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    
    output_path = os.path.join("outputs", "technical_report.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
        
    print(f"Technical evaluation report successfully saved to {output_path}")
