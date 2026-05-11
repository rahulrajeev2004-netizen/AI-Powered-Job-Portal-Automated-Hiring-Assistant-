import fitz  # PyMuPDF
import re
from typing import Dict, Any, List

class EnhancedResumeParser:
    """
    Enterprise-grade resume parser with section detection, multi-column support,
    and extraction validation.
    """
    
    SECTIONS = {
        "skills": [r"skills", r"technical skills", r"competencies", r"expertise", r"technologies"],
        "experience": [r"experience", r"work history", r"professional background", r"employment"],
        "education": [r"education", r"academic", r"qualification"],
        "projects": [r"projects", r"personal projects", r"key projects"],
        "certifications": [r"certifications", r"awards", r"achievements", r"licenses"]
    }

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.text = ""
        self.sections = {}
        self.confidence_score = 0.0

    def extract_text(self) -> str:
        """Extracts text with layout awareness."""
        try:
            doc = fitz.open(self.file_path)
            full_text = ""
            for page in doc:
                # get_text("blocks") helps with multi-column layouts
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (b[1], b[0])) # Sort by Y then X
                for b in blocks:
                    full_text += b[4] + "\n"
            
            self.text = full_text
            self._validate_extraction()
            self._identify_sections()
            return self.text
        except Exception as e:
            print(f"Error parsing PDF {self.file_path}: {e}")
            return ""

    def _validate_extraction(self):
        """Calculates parser confidence score."""
        if not self.text:
            self.confidence_score = 0.0
            return

        # Check for garbled text (very long words or lack of common English characters)
        words = self.text.split()
        if not words:
            self.confidence_score = 0.0
            return

        avg_word_len = sum(len(w) for w in words) / len(words)
        
        # Simple heuristic: meaningful text usually has avg word length between 3 and 12
        if 3 <= avg_word_len <= 12:
            self.confidence_score = min(1.0, 0.5 + (len(words) / 500))
        else:
            self.confidence_score = 0.3 # Likely poor extraction/scanned

    def _identify_sections(self):
        """Detects sections based on keywords."""
        lines = self.text.split('\n')
        current_section = "summary"
        
        for line in lines:
            line_clean = line.strip().lower()
            if not line_clean:
                continue
                
            found_header = False
            for section, keywords in self.SECTIONS.items():
                if any(re.search(r'^' + k + r'$', line_clean) for k in keywords):
                    current_section = section
                    self.sections[current_section] = self.sections.get(current_section, "")
                    found_header = True
                    break
            
            if not found_header:
                self.sections[current_section] = self.sections.get(current_section, "") + line + "\n"

    def get_structured_data(self) -> Dict[str, Any]:
        return {
            "full_text": self.text,
            "sections": self.sections,
            "parser_confidence": round(self.confidence_score, 2),
            "is_valid": self.confidence_score > 0.4
        }
