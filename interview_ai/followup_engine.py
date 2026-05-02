import re
from typing import Optional

class FollowUpDetector:
    """Detects the quality of a candidate's answer based on length and sentiment."""
    
    UNCERTAINTY_PATTERNS = [
        r"\bnot sure\b", r"\bmaybe\b", r"\bi think\b", r"\bprobably\b", r"\bguess\b"
    ]

    @classmethod
    def evaluate_quality(cls, answer: str) -> str:
        clean_text = answer.strip().lower()
        
        if not clean_text:
            return "empty"
            
        word_count = len(clean_text.split())
        if word_count < 4:
            return "too_short"
            
        if any(re.search(pattern, clean_text) for pattern in cls.UNCERTAINTY_PATTERNS):
            return "uncertain"
            
        if word_count < 8:
            return "basic"
            
        return "good"


class FollowUpGenerator:
    """Generates an appropriate follow-up prompt based on answer quality."""
    
    RESPONSE_TEMPLATES = {
        "empty": "I'm sorry, I didn't quite catch your response. Could you please answer the question?",
        "too_short": "Could you expand a bit more on your answer regarding: '{question}'?",
        "uncertain": "You seem a bit uncertain. Could you clarify your thoughts on: '{question}'?",
        "basic": "That's a good start. Can you provide a specific, real-world example related to: '{question}'?"
    }

    @classmethod
    def create_prompt(cls, question: str, quality: str) -> Optional[str]:
        template = cls.RESPONSE_TEMPLATES.get(quality)
        if not template:
            return None
        return template.format(question=question)
