import re
from typing import Optional

class FollowUpDetector:
    """Detects the quality of a candidate's answer based on length, sentiment, and completeness."""
    
    UNCERTAINTY_PATTERNS = [
        r"\bnot sure\b", r"\bmaybe\b", r"\bi think\b", r"\bprobably\b", r"\bguess\b",
        r"\bsort of\b", r"\bkind of\b", r"\bi don't know\b", r"\bi am not sure\b"
    ]
    
    COMPLETENESS_KEYWORDS = ["because", "since", "example", "instance", "result", "outcome", "led to"]

    @classmethod
    def evaluate_quality(cls, answer: str) -> str:
        clean_text = answer.strip().lower()
        
        if not clean_text or len(clean_text) < 5:
            return "empty"
            
        words = clean_text.split()
        word_count = len(words)
        
        if word_count < 5:
            return "too_short"
            
        has_uncertainty = any(re.search(pattern, clean_text) for pattern in cls.UNCERTAINTY_PATTERNS)
        has_elaboration = any(kw in clean_text for kw in cls.COMPLETENESS_KEYWORDS)
        
        if has_uncertainty and word_count < 15:
            return "uncertain"
            
        if word_count < 10:
            return "basic"
            
        if word_count < 20 and not has_elaboration:
            return "shallow"
            
        return "good"


class FollowUpGenerator:
    """Generates an appropriate follow-up prompt based on answer quality."""
    
    RESPONSE_TEMPLATES = {
        "empty": "I didn't quite get that. Could you please provide an answer to the question?",
        "too_short": "That's a bit brief. Could you elaborate more on your experience with: '{question}'?",
        "uncertain": "You mentioned being unsure. Could you try to explain your best understanding or a similar experience regarding: '{question}'?",
        "basic": "I see. Can you provide a specific example or more context about: '{question}'?",
        "shallow": "That makes sense. Could you go deeper into the 'why' or the specific results achieved regarding: '{question}'?"
    }

    @classmethod
    def create_prompt(cls, question: str, quality: str) -> Optional[str]:
        template = cls.RESPONSE_TEMPLATES.get(quality)
        if not template:
            return None
        return template.format(question=question)
