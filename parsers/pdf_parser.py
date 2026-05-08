import fitz  # PyMuPDF
import re
from utils.logger import get_logger 
##

logger = get_logger('pdf_parser', 'logs/extraction.log')

def clean_resume_text(text: str) -> str:
    """
    Cleans and normalizes extracted resume text.
    Handles broken spacing for medical abbreviations, unicode normalization,
    and whitespace collapsing.
    """
    if not text:
        return ""
        
    # Lowercase
    text = text.lower()
    
    # Normalize unicode characters
    text = text.replace("•", " ")  # Bullets
    text = text.replace("–", "-")  # En dash
    text = text.replace("—", "-")  # Em dash
    text = text.replace("“", '"').replace("”", '"') # Smart quotes
    text = text.replace("‘", "'").replace("’", "'") # Smart single quotes
    
    # Fix medical abbreviation splitting (e.g., "I C U" -> "icu")
    replacements = {
        "i c u": "icu",
        "b l s": "bls",
        "a c l s": "acls",
        "c p r": "cpr",
        "r n": "rn",
        "e c g": "ecg",
        "e k g": "ekg"
    }
    
    for broken, fixed in replacements.items():
        # Use regex to replace the broken abbreviations while maintaining word boundaries
        text = re.sub(r'\b' + re.escape(broken) + r'\b', fixed, text)

    # Normalize whitespace/newlines
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file, handling multi-page and keeping layout roughly intact.
    Ignores images (PyMuPDF get_text doesn't extract images as text by default).
    Handles tables / columns to some extent via block sorting.
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    text_content = []
    
    try:
        with fitz.open(file_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # PyMuPDF's sort=True in get_text("text") usually handles columns better.
                page_text = page.get_text("text", sort=True)
                
                if page_text.strip():
                    text_content.append(page_text)
                else:
                    logger.debug(f"Page {page_num + 1} of {file_path} is empty or unextractable.")
                    
        full_text = "\n".join(text_content)
        
        # Apply healthcare-specific normalization
        full_text = clean_resume_text(full_text)
        
        # Quality check
        if len(full_text.split()) < 30:
            logger.warning(f"Low extraction quality detected for {file_path}")
            
        logger.info(f"Successfully extracted {len(full_text)} characters from {file_path}")
        return full_text
    
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return ""
