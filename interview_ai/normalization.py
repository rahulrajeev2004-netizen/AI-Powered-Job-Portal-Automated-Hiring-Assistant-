import re

class TranscriptNormalizer:
    def __init__(self):
        self.filler_words = r'\b(uh|um|like|you know|exactly)\b'
        
        # Simple word-to-number mapping for common explicit numerical constraints
        self.number_words = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", 
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", 
            "ten": "10", "eleven": "11", "twelve": "12", "point": "."
        }
        
    def remove_filler_words(self, text: str) -> str:
        cleaned = re.sub(self.filler_words, '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'[,]+', ',', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned.strip(', ')

    def convert_numbers_to_digits(self, text: str) -> str:
        words = text.split()
        converted = []
        for word in words:
            clean_word = word.lower().strip(".,!?")
            if clean_word in self.number_words:
                converted.append(word.replace(word.strip(".,!?"), self.number_words[clean_word]))
            else:
                converted.append(word)
        
        # Merge "4 . 5" to "4.5" if disconnected
        joined = ' '.join(converted)
        joined = re.sub(r'(\d)\s+\.\s+(\d)', r'\1.\2', joined)
        return joined

    def normalize(self, text: str) -> dict:
        """
        Applies Day-23 strict payload normalization.
        Returns a dictionary with the normalized text and the list of applied rules.
        """
        if not text:
            return {"text": "", "applied_rules": []}
            
        applied_rules = []
        current_text = text
        
        # 1. Remove filler words
        clean_filler = self.remove_filler_words(current_text)
        if clean_filler != current_text:
            applied_rules.append("filler_word_removal")
            current_text = clean_filler
            
        # 2. Convert numbers to digits
        clean_num = self.convert_numbers_to_digits(current_text)
        if clean_num != current_text:
            applied_rules.append("numeric_normalization")
            current_text = clean_num
            
        return {
            "text": current_text,
            "applied_rules": applied_rules
        }
