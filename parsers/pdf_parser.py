import fitz  # PyMuPDF
from utils.logger import get_logger

logger = get_logger('pdf_parser', 'logs/extraction.log')

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
                # 'blocks' returns a list of text blocks. Sorting by y0, then x0 keeps reading order.
                # However, PyMuPDF's sort=True in get_text("text") usually handles columns better.
                page_text = page.get_text("text", sort=True)
                
                if page_text.strip():
                    text_content.append(page_text)
                else:
                    logger.debug(f"Page {page_num + 1} of {file_path} is empty or unextractable.")
                    
        full_text = "\n".join(text_content)
        logger.info(f"Successfully extracted {len(full_text)} characters from {file_path}")
        return full_text
    
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return ""
