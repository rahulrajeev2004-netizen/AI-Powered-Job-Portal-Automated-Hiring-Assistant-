
import os
import json
from parsers.resume_segmenter import (
    segment_resume, CONTACT_INFO, SUMMARY, WORK_EXPERIENCE, 
    EDUCATION, SKILLS, PROJECTS, LANGUAGES, DECLARATION, CERTIFICATIONS
)
from parsers.pdf_parser import extract_text_from_pdf
from utils.logger import get_logger

logger = get_logger("run_resume_segmentation", "logs/resume_segmentation.log")

# Definitions for Ground Truth (expected sections for samples)
EXPECTED_SECTIONS = {
    "sample_resume_pdf_cleaned.txt": [
        CONTACT_INFO, SUMMARY, WORK_EXPERIENCE, PROJECTS, SKILLS, EDUCATION, LANGUAGES, DECLARATION
    ],
    "sample_resume.pdf": [
        CONTACT_INFO, SUMMARY, WORK_EXPERIENCE, PROJECTS, SKILLS, EDUCATION, LANGUAGES, DECLARATION
    ],
    "sample_2.txt": [
        CONTACT_INFO, SUMMARY, SKILLS, WORK_EXPERIENCE, EDUCATION
    ],
    "Reshma resume.pdf": [
        CONTACT_INFO, SUMMARY, EDUCATION, SKILLS, CERTIFICATIONS, LANGUAGES
    ]
}

def run_comprehensive_test():
    """
    Runs resume segmentation on all resumes in the data directory and evaluates accuracy.
    """
    resumes_dir = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\data\resumes"
    processed_dir = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\data\processed" # For pre-extracted txt
    output_dir = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\data\samples\labeled"
    os.makedirs(output_dir, exist_ok=True)
    
    # Collect all resumes to process
    resumes_to_process = []
    
    # Check resumes folder
    if os.path.exists(resumes_dir):
        for f in os.listdir(resumes_dir):
            if f.endswith(".pdf") or f.endswith(".txt"):
                resumes_to_process.append({"name": f, "path": os.path.join(resumes_dir, f)})
    
    # Check processed folder for specific cleaned text files
    if os.path.exists(processed_dir):
        for f in os.listdir(processed_dir):
            if f == "sample_resume_pdf_cleaned.txt":
                resumes_to_process.append({"name": f, "path": os.path.join(processed_dir, f)})

    report_data = []

    print("\n" + "="*60)
    print("RESUME SECTION SEGMENTATION REPORT")
    print("="*60)

    for sample in resumes_to_process:
        filename = sample["name"]
        filepath = sample["path"]
        
        logger.info(f"Processing: {filename}")
        
        # Extract text based on file type
        raw_text = ""
        if filename.endswith(".pdf"):
            raw_text = extract_text_from_pdf(filepath)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()
            
        if not raw_text:
            logger.warning(f"Failed to extract text from {filename}")
            continue
            
        # Segment the resume
        segmented_content = segment_resume(raw_text)
        
        # Save labeled output
        output_name = filename.replace(".pdf", "").replace(".txt", "") + "_segmented.json"
        output_file = os.path.join(output_dir, output_name)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(segmented_content, f, indent=2, ensure_ascii=False)
            
        # Evaluate accuracy
        found_sections = set(segmented_content.keys())
        expected_sections = set(EXPECTED_SECTIONS.get(filename, []))
        
        if not expected_sections:
            accuracy = 1.0 
            status_msg = " [!] Ground truth not defined, showing found sections."
        else:
            correct = found_sections.intersection(expected_sections)
            accuracy = len(correct) / len(expected_sections)
            status_msg = ""
            
        print(f"\nProcessing: {filename}")
        print(f"  - Sections Found: {len(found_sections)}")
        print(f"  - Accuracy: {accuracy:.1%}{status_msg}")
        
        if expected_sections:
            missing = expected_sections - found_sections
            unexpected = found_sections - expected_sections
            if missing:
                print(f"  - Missing: {', '.join(missing)}")
            if unexpected:
                print(f"  - Extra: {', '.join(unexpected)}")
            
        report_data.append({
            "sample": filename,
            "accuracy": accuracy,
            "found": list(found_sections),
            "expected": list(expected_sections)
        })

    # Calculations for summary
    total_samples = len(report_data)
    avg_accuracy = sum(r["accuracy"] for r in report_data) / total_samples if total_samples > 0 else 0

    # Save summary report as JSON
    report_file_json = os.path.join(output_dir, "segmentation_accuracy_report.json")
    with open(report_file_json, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    
    # Save summary report as human-readable TXT
    report_file_txt = os.path.join(output_dir, "accuracy_summary.txt")
    with open(report_file_txt, "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write("Resume Section Detection Report\n")
        f.write("-" * 31 + "\n")
        f.write(f"Total Samples: {total_samples}\n")
        f.write(f"Average Accuracy: {avg_accuracy:.2f}\n")
        f.write("="*60 + "\n\n")
        
        f.write("Detailed Results per Resume:\n")
        f.write("-" * 28 + "\n")
        for r in report_data:
            f.write(f"Filename: {r['sample']}\n")
            f.write(f"  - Sections Found: {len(r['found'])}\n")
            f.write(f"  - Accuracy Score: {r['accuracy']:.2f}\n")
            f.write(f"  - Sections: {', '.join(r['found'])}\n\n")
            
    print("\n" + "="*60)
    print("Resume Section Detection Report")
    print("-------------------------------")
    print(f"Total Samples: {total_samples}")
    print(f"Average Accuracy: {avg_accuracy:.2f}")
    print("="*60 + "\n")
    print(f"Summary saved to: {report_file_txt}")
    print(f"Detailed output kept in: {output_dir}")

if __name__ == "__main__":
    run_comprehensive_test()
