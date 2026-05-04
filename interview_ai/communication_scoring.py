import re
from typing import Dict, Any

class CommunicationEvaluator:
    """
    Evaluates candidate communication based on heuristics for fluency, grammar, 
    vocabulary, clarity, and structure. Applies penalties for filler words.
    """
    
    FILLER_TERMS = {"um", "uh", "like", "you know", "actually", "basically"}
    CONNECTIVE_PHRASES = {"because", "for example", "therefore", "however"}
    
    def __init__(self, text: str):
        self.text = text.strip()
        self.words = self.text.split()
        self.word_count = len(self.words)
        self.lower_text = self.text.lower()
        
    def _evaluate_fluency(self) -> float:
        """Measures sentence continuity based on valid sentence counts."""
        if not self.text:
            return 0.3
            
        # Split by common sentence terminators
        raw_sentences = re.split(r'[.!?]+', self.text)
        # A valid sentence is defined as having more than 3 words
        valid_count = sum(1 for sentence in raw_sentences if len(sentence.split()) > 3)
        
        if valid_count >= 2:
            return 1.0
        if valid_count == 1:
            return 0.6
        return 0.3

    def _evaluate_grammar(self) -> float:
        """Heuristic check for basic grammar rules and sentence length."""
        if not self.text:
            return 0.4
            
        starts_upper = self.text[0].isupper()
        ends_with_punct = self.text.endswith(('.', '?', '!'))
        
        if starts_upper and ends_with_punct:
            return 1.0
        if self.word_count > 5:
            return 0.7
        return 0.4

    def _evaluate_vocabulary(self) -> float:
        """Scores based on lexical richness (Type-Token Ratio)."""
        if self.word_count == 0:
            return 0.4
            
        unique_count = len(set(word.lower() for word in self.words))
        type_token_ratio = unique_count / (self.word_count + 1)
        
        if type_token_ratio > 0.6:
            return 1.0
        if unique_count > 5:
            return 0.7
        return 0.4

    def _evaluate_clarity(self) -> float:
        """Scores clarity based on utterance length."""
        if self.word_count > 12:
            return 1.0
        if self.word_count > 6:
            return 0.7
        return 0.4

    def _evaluate_structure(self) -> float:
        """Checks for the presence of logical connectors or sufficient length."""
        if any(phrase in self.lower_text for phrase in self.CONNECTIVE_PHRASES):
            return 1.0
        if self.word_count > 6:
            return 0.7
        return 0.4

    def _calculate_penalty(self) -> float:
        """Calculates deductions for excessive use of filler words."""
        filler_count = sum(self.lower_text.count(filler) for filler in self.FILLER_TERMS)
        return min(filler_count * 0.1, 0.5)

    def generate_report(self) -> Dict[str, Any]:
        """Aggregates all metrics into a final score report."""
        metrics = {
            "fluency": self._evaluate_fluency(),
            "grammar": self._evaluate_grammar(),
            "vocabulary": self._evaluate_vocabulary(),
            "clarity": self._evaluate_clarity(),
            "structure": self._evaluate_structure()
        }
        
        penalty = self._calculate_penalty()
        
        # Each metric is weighted equally (20%)
        base_score = sum(val * 0.2 for val in metrics.values())
        final_score = max(base_score - penalty, 0.0)
        
        return {
            "communication_score": round(final_score * 100, 2),
            "breakdown": {k: round(v, 2) for k, v in metrics.items()},
            "penalty_applied": round(penalty, 2)
        }

def calculate_communication_score(text: str) -> Dict[str, Any]:
    """Helper function to instantiate the evaluator and get the score."""
    evaluator = CommunicationEvaluator(text)
    return evaluator.generate_report()
