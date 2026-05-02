from enum import Enum

class QuestionDifficulty(Enum):
    SIMPLIFY = "simplify"
    EXAMPLE = "example"
    ADVANCED = "advanced"
    NORMAL = "normal"


class AdaptiveDifficultyManager:
    """Determines the next question difficulty based on the candidate's previous answer quality."""
    
    @staticmethod
    def determine_level(quality: str, confidence_score: float) -> QuestionDifficulty:
        if quality in ("empty", "too_short"):
            return QuestionDifficulty.SIMPLIFY
            
        if quality == "basic":
            return QuestionDifficulty.EXAMPLE
            
        if quality == "good" and confidence_score > 0.7:
            return QuestionDifficulty.ADVANCED
            
        return QuestionDifficulty.NORMAL


class AdaptiveQuestionBuilder:
    """Rebuilds the base question to match the desired difficulty level."""
    
    PREFIXES = {
        QuestionDifficulty.SIMPLIFY: "Let's break this down. In simpler terms: ",
        QuestionDifficulty.EXAMPLE: "Could you share a practical, real-world example illustrating: ",
        QuestionDifficulty.ADVANCED: "Let's dive deeper. How would you handle a complex, high-stakes scenario involving: "
    }

    @classmethod
    def build(cls, base_question: str, mode: QuestionDifficulty) -> str:
        prefix = cls.PREFIXES.get(mode)
        if prefix:
            return f"{prefix}{base_question}"
        return base_question
