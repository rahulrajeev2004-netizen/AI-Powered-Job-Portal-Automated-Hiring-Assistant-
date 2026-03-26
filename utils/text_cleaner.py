import re
from utils.logger import get_logger

logger = get_logger('text_cleaner', 'logs/extraction.log')

# Standardized section headings
STD_HEADINGS = {
    'experience': ['experience', 'work experience', 'employment history', 'professional experience'],
    'education': ['education', 'academic background', 'academic history'],
    'skills': ['skills', 'technical skills', 'core competencies', 'technologies'],
    'summary': ['summary', 'profile', 'professional summary', 'objective'],
    'certifications': ['certifications', 'licenses', 'courses']
}

def clean_text(raw_text: str) -> str:
    """
    Cleans extracted resume text.
    - Removes noise / symbols
    - Normalizes whitespace
    - Standardizes headings
    """
    logger.debug("Cleaning text...")
    
    # 1. Normalize whitespace (remove excessive blank lines/tabs)
    # Replace weird newlines
    text = re.sub(r'[\r\n]+', '\n', raw_text)
    # Replace non-breaking spaces and tabs with space
    text = re.sub(r'[\t\xa0]', ' ', text)
    # Reduce multiple spaces to single space
    text = re.sub(r' +', ' ', text)
    
    # 2. Remove noise and non-ASCII characters that aren't typical punctuation
    # Allow letters, numbers, punctuation, spaces, newlines
    text = re.sub(r'[^\w\s\.,;:!?@#\$%\^&*\(\)\[\]\{\}\-\+=<>\'\"/\|\\~`]', '', text)

    lines = []
    for line in text.split('\n'):
        # Strip trailing/leading spaces
        line = line.strip()
        if not line:
            continue
            
        # 3. Clean headings
        cleaned_line = _normalize_heading(line)
        lines.append(cleaned_line)

    # Re-join with single newlines
    cleaned_output = '\n'.join(lines)
    logger.debug(f"Cleaned output generated ({len(cleaned_output)} chars).")
    return cleaned_output

def _normalize_heading(line: str) -> str:
    """
    Normalizes known headings by making them uppercase and standardized to match
    the JSON schema fields essentially, or at least a standard form.
    E.g., "Work Experience" -> "EXPERIENCE"
    """
    line_lower = line.lower()
    # Handle pure headings (short length, no trailing punctuation other than colon)
    if len(line) < 35 and not line.endswith('.') and not line.endswith(','):
        # Remove trailing colon for check
        clean_lower = line_lower.rstrip(': ').strip()
        
        for std_head, vars_list in STD_HEADINGS.items():
            if clean_lower in vars_list:
                return std_head.upper()
                
    # Otherwise return original
    return line
