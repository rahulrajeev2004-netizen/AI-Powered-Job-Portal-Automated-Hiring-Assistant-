import json
from enum import Enum, auto
from typing import Dict, Any, List, Optional

class InterviewState(Enum):
    INIT = auto()
    INTRO = auto()
    EXP_ASSESSMENT = auto()
    CONCEPTUAL_ASSESSMENT = auto()
    SCENARIO_ASSESSMENT = auto()
    CLOSING = auto()
    EVALUATION = auto()

class ExperienceLevel(Enum):
    JUNIOR = "0-2 years" # Fundamentals, basics
    INTERMEDIATE = "3-5 years" # Best practices, optimization
    ADVANCED = "5+ years" # Architecture, System Design

class DifficultyLevel(Enum):
    LEVEL_1 = 1 # Warm-up
    LEVEL_2 = 2 # Applied
    LEVEL_3 = 3 # Analytical
    LEVEL_4 = 4 # Architectural

class TechnicalInterviewEngine:
    """
    State machine-based engine for conducting technical AI interviews.
    Follows the Technical Interview AI Blueprint.
    """
    def __init__(self, candidate_context: Dict[str, Any]):
        """
        Initialize the interview with candidate context.
        context should contain 'name', 'role', 'experience_years', 'skills'
        """
        self.context = candidate_context
        self.state = InterviewState.INIT
        self.experience_level = self._map_experience(self.context.get('experience_years', 0))
        self.domain = self._map_role_to_domain(self.context.get('role', 'Generic'))
        
        # State tracking
        self.current_difficulty = DifficultyLevel.LEVEL_1
        self.history = []
        self.score_breakdown = {
            "experience": 0,
            "conceptual": 0,
            "scenario": 0
        }
        
    def _map_experience(self, years: float) -> ExperienceLevel:
        if years <= 2:
            return ExperienceLevel.JUNIOR
        elif years <= 5:
            return ExperienceLevel.INTERMEDIATE
        else:
            return ExperienceLevel.ADVANCED

    def _map_role_to_domain(self, role: str) -> str:
        role = role.lower()
        if "mern" in role or "react" in role or "node" in role:
            return "Web Engineering"
        elif "java" in role or "spring" in role or "backend" in role:
            return "Backend Systems"
        elif "devops" in role or "sre" in role:
            return "Cloud & Infrastructure"
        elif "data" in role or "machine learning" in role or "ai" in role:
            return "ML & Analytics"
        elif "frontend" in role or "ui" in role or "ux" in role:
            return "UI/UX Engineering"
        return "General Software Engineering"

    def transition(self) -> str:
        """Execute state transition and return AI prompt/action."""
        if self.state == InterviewState.INIT:
            self.state = InterviewState.INTRO
            return f"System Initialized. Context Loaded for {self.context.get('name')}. Role: {self.context.get('role')}. Experience: {self.experience_level.value}."
            
        elif self.state == InterviewState.INTRO:
            self.state = InterviewState.EXP_ASSESSMENT
            return f"Hello {self.context.get('name')}, I am your AI interviewer. Today we will discuss your experience with {self.domain}, explore some technical concepts, and solve a scenario together. Shall we begin with your past experience?"
            
        elif self.state == InterviewState.EXP_ASSESSMENT:
            # In a real flow, we'd stay here until satisfied. Transitioning to next for demo.
            self.state = InterviewState.CONCEPTUAL_ASSESSMENT
            if self.experience_level == ExperienceLevel.JUNIOR:
                return f"Based on your {self.experience_level.value} experience, can you explain the foundational tools you used in your last project?"
            elif self.experience_level == ExperienceLevel.INTERMEDIATE:
                return f"With your {self.experience_level.value} experience, can you describe a time you optimized performance or debugged a complex issue?"
            else:
                return f"Given your {self.experience_level.value} experience, how have you approached system design and architecture in your recent roles?"

        elif self.state == InterviewState.CONCEPTUAL_ASSESSMENT:
            self.state = InterviewState.SCENARIO_ASSESSMENT
            return f"Let's move to some conceptual questions in {self.domain}. Question (Difficulty {self.current_difficulty.name}): Explain a core concept relevant to this domain."

        elif self.state == InterviewState.SCENARIO_ASSESSMENT:
            self.state = InterviewState.CLOSING
            return f"Now for a practical scenario. Imagine a system failure in a {self.domain} environment. How would you troubleshoot and resolve it?"

        elif self.state == InterviewState.CLOSING:
            self.state = InterviewState.EVALUATION
            return "That concludes the technical portion. Do you have any questions for me?"

        elif self.state == InterviewState.EVALUATION:
            return "Interview complete. Generating report..."
            
    def adjust_difficulty(self, answer_quality: float):
        """
        Adjust question difficulty based on answer quality (0.0 to 1.0).
        """
        if answer_quality >= 0.8 and self.current_difficulty.value < 4:
            self.current_difficulty = DifficultyLevel(self.current_difficulty.value + 1)
        elif answer_quality < 0.4 and self.current_difficulty.value > 1:
            self.current_difficulty = DifficultyLevel(self.current_difficulty.value - 1)
            
    def process_answer(self, user_answer: str) -> str:
        """
        Process the user's answer, log it, adjust state/difficulty, and return next prompt.
        """
        self.history.append({
            "state": self.state.name,
            "answer": user_answer
        })
        
        # Mocking evaluation quality
        answer_quality = 0.85 # Assume a good answer
        self.adjust_difficulty(answer_quality)
        
        return self.transition()

    def generate_report(self) -> Dict[str, Any]:
        """Generate final technical blueprint report."""
        if self.state != InterviewState.EVALUATION:
            return {"error": "Interview not complete"}
            
        return {
            "candidate": self.context.get('name'),
            "role": self.context.get('role'),
            "domain": self.domain,
            "experience_level": self.experience_level.value,
            "final_difficulty_reached": self.current_difficulty.name,
            "score_breakdown": self.score_breakdown,
            "recommendation": "Hire" if self.current_difficulty.value >= 3 else "No Hire"
        }

if __name__ == "__main__":
    # Example usage
    context = {
        "name": "Jane Doe",
        "role": "Java Backend Developer",
        "experience_years": 4.5
    }
    engine = TechnicalInterviewEngine(context)
    
    print("--- Technical Interview Flow ---")
    print(engine.transition()) # INIT
    print(engine.transition()) # INTRO
    print(engine.process_answer("Yes, let's start.")) # EXP
    print(engine.process_answer("I optimized database queries...")) # CONCEPTUAL
    print(engine.process_answer("A thread pool manages...")) # SCENARIO
    print(engine.process_answer("I would check the logs and...")) # CLOSING
    print(engine.process_answer("No questions.")) # EVAL
    print("\n--- Final Report ---")
    print(json.dumps(engine.generate_report(), indent=2))
