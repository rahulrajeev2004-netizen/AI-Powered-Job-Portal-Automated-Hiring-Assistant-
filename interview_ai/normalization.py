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

    def normalize(self, text: str) -> str:
        """
        Applies Day-23 strict payload normalization.
        No grammar inferencing or context derivation is executed.
        """
        if not text:
            return ""
            
        current_text = text
        current_text = self.remove_filler_words(current_text)
        current_text = self.convert_numbers_to_digits(current_text)
        
        return current_text
