
import re
from typing import Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger("resume_segmenter", "logs/resume_segmentation.log")

# ---------------------------------------------------------------------------
# NORMALIZED SECTION KEYS
# ---------------------------------------------------------------------------
# These are the canonical keys we want in our output dictionary.
CONTACT_INFO = "contact_info"
SUMMARY = "summary"
WORK_EXPERIENCE = "work_experience"
EDUCATION = "education"
SKILLS = "skills"
PROJECTS = "projects"
CERTIFICATIONS = "certifications"
LANGUAGES = "languages"
AWARDS = "awards"
MISCELLANEOUS = "miscellaneous"
DECLARATION = "declaration"

# ---------------------------------------------------------------------------
# SECTION HEADING PATTERNS
# ---------------------------------------------------------------------------
_SECTION_PATTERNS = {
    SUMMARY: r"(?i)^(?:summary|objective|career\s+objective|professional\s+profile|profile|about\s+me)$",
    WORK_EXPERIENCE: r"(?i)^(?:work\s+experience|experience|employment\s+history|professional\s+experience|internship|internships?\s*[/&]\s*experience|work\s+history|professional\s+background)$",
    EDUCATION: r"(?i)^(?:education|academic\s+background|academic\s+performance|academic\s+qualifications|educational\s+qualifications|scholastic\s+achievements?)$",
    SKILLS: r"(?i)^(?:tech(?:nical)?\s+skills|skills|core\s+competencies|competencies|areas\s+of\s+expertise|expertises|hard\s+skills|soft\s+skills|tech\s+stack)$",
    PROJECTS: r"(?i)^(?:projects|personal\s+projects|key\s+projects|academic\s+projects|notable\s+projects)$",
    CERTIFICATIONS: r"(?i)^(?:certifications|licenses|certifications\s*[/&]\s*licenses|courses|professional\s+certifications|extra\s+qualifications)$",
    LANGUAGES: r"(?i)^(?:languages|linguistic\s+skills)$",
    AWARDS: r"(?i)^(?:awards|honors|achievements|distinctions|accolades)$",
    DECLARATION: r"(?i)^(?:declaration)$",
}

# Add some variations for common sections encountered in resumes
_ADDITIONAL_PATTERNS = {
    SKILLS: [r"TECH SKILLS", r"HARD SKILLS", r"SOFT SKILLS", r"SKILLS & ABILITIES", r"TECHNICAL SKILLS"],
    WORK_EXPERIENCE: [r"PROFESSIONAL BACKGROUND", r"CAREER SUMMARY", r"EXPERIENCE HISTORY", r"INTERNSHIP /EXPERIENCE"],
    CERTIFICATIONS: [r"CERTIFICATIONS AND TRAININGS", r"EXTRA QUALIFICATIONS"],
}

# Pre-compile patterns for efficiency
COMPILED_PATTERNS = {k: re.compile(v) for k, v in _SECTION_PATTERNS.items()}

def _is_heading(line: str) -> Optional[str]:
    """
    Check if a line matches a section heading pattern.
    Returns the normalized section key or None.
    """
    stripped = line.strip().rstrip(":")
    if not stripped:
        return None
    
    # Check rule-based patterns
    for section, pattern in COMPILED_PATTERNS.items():
        if pattern.match(stripped):
            return section
            
    # Check additional hardcoded variations if any (case-insensitive)
    for section, variations in _ADDITIONAL_PATTERNS.items():
        for var in variations:
            if stripped.upper() == var.upper():
                return section
                
    # NLP-based Heuristic: All-caps, short, common heading indicators
    # (e.g. "EXPERIENCE", "PROJECTS" even if not in patterns)
    # This is a fallback for missing headings in patterns.
    if len(stripped) < 30 and stripped.isupper():
        # Look for keywords anyway to be safe
        keywords = ["EXPERIENCE", "SKILLS", "EDUCATION", "PROJECTS", "SUMMARY", "CONTACT", "AWARDS", "CERTIF", "VOLUNTEER"]
        for kw in keywords:
            if kw in stripped:
                # Map kw to section
                if "EXPERIENCE" in stripped: return WORK_EXPERIENCE
                if "SKILLS" in stripped: return SKILLS
                if "EDUCATION" in stripped: return EDUCATION
                if "PROJECTS" in stripped: return PROJECTS
                if "SUMMARY" in stripped: return SUMMARY
                if "CERTIF" in stripped: return CERTIFICATIONS
                if "AWARDS" in stripped: return AWARDS
                
    return None

def segment_resume(text: str) -> Dict[str, str]:
    """
    Segments raw resume text into major sections.
    """
    logger.info("Starting resume segmentation...")
    
    lines = text.split("\n")
    sections: Dict[str, List[str]] = {CONTACT_INFO: []}
    current_section = CONTACT_INFO
    
    for i, line in enumerate(lines):
        # Heuristic: Check if the line is a section header
        # Header candidates are usually short and on their own line.
        detected_section = _is_heading(line)
        
        if detected_section:
            # Check if it's actually a header or just text (heuristic)
            # Headers usually don't have many lowercase letters if they are all-caps,
            # or they are clearly separated.
            # For now, if _is_heading returns something, we trust it.
            current_section = detected_section
            if current_section not in sections:
                sections[current_section] = []
            logger.debug(f"Detected section header: '{line.strip()}' -> mapping to '{current_section}'")
            continue
            
        sections[current_section].append(line)
        
    # Post-process: Clean up sections and merge lines
    final_sections = {}
    for section, line_list in sections.items():
        joined_text = "\n".join(line_list).strip()
        if joined_text:
            final_sections[section] = joined_text
            
    logger.info(f"Segmentation complete. Found {len(final_sections)} sections: {list(final_sections.keys())}")
    return final_sections

if __name__ == "__main__":
    # Test with a sample string
    sample_text = """
    JOHN DOE
    Email: john.doe@example.com
    
    SUMMARY
    Experienced software engineer with a focus on cloud systems.
    
    EXPERIENCE
    Senior Engineer @ TechCorp
    2020 - Present
    - Led a team of 5.
    
    EDUCATION
    B.S. in Computer Science, MIT
    """
    
    segmented = segment_resume(sample_text)
    import json
    print(json.dumps(segmented, indent=2))
