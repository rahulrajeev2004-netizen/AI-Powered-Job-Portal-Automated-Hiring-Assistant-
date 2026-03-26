import os
import glob
from utils.logger import get_logger

logger = get_logger('file_handler', 'logs/extraction.log')

def get_all_resumes(directory: str) -> list[str]:
    """Retrieve all PDF and DOCX file paths from a given directory."""
    logger.info(f"Looking for resumes in: {directory}")
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    docx_files = glob.glob(os.path.join(directory, "*.docx"))
    all_files = pdf_files + docx_files
    
    logger.info(f"Found {len(all_files)} files.")
    return all_files

def save_text_to_file(text: str, source_path: str, output_dir: str):
    """Save cleaned text in processing dir alongside base filename."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    base_name = os.path.basename(source_path)
    file_name, ext = os.path.splitext(base_name)
    output_path = os.path.join(output_dir, f"{file_name}{ext.replace('.', '_')}_cleaned.txt")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
        
    logger.info(f"Saved cleaned text to {output_path}")

