import os
from utils.logger import get_logger
from utils.file_handler import get_all_resumes, save_text_to_file
from utils.text_cleaner import clean_text
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx

logger = get_logger('main_pipeline', 'logs/extraction.log')

def main():
    logger.info("Starting Resume Text Extraction Engine Pipeline.")
    
    input_dir = os.path.join("data", "resumes")
    output_dir = os.path.join("data", "processed")
    
    # Ensure directories exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Fetch all resumes
    resumes = get_all_resumes(input_dir)
    
    if not resumes:
        logger.warning(f"No resumes found in {input_dir}. Please add some PDFs or DOCXs.")
        return
        
    for resume_path in resumes:
        logger.info(f"Processing: {resume_path}")
        
        # Determine extraction strategy based on file extension
        ext = os.path.splitext(resume_path)[1].lower()
        if ext == ".pdf":
            raw_text = extract_text_from_pdf(resume_path)
        elif ext == ".docx":
            raw_text = extract_text_from_docx(resume_path)
        else:
            logger.error(f"Unsupported file format: {ext} for {resume_path}")
            continue
            
        if not raw_text:
            logger.warning(f"Extraction failed or returned empty text for {resume_path}")
            continue
            
        # Clean text
        cleaned_text = clean_text(raw_text)
        
        # Save output
        save_text_to_file(cleaned_text, resume_path, output_dir)
        logger.info(f"Finished processing {os.path.basename(resume_path)}")
        
    logger.info("Pipeline Execution Complete.")

if __name__ == "__main__":
    main()
