import os
import json
import argparse
from engines.skill_extractor.skill_extractor import SkillExtractor
from utils.logger import get_logger

logger = get_logger("run_skill_extractor", "logs/skill_extraction_run.log")

def run_skill_extraction(input_dir: str, output_dir: str, dictionary_path: str):
    """
    Process all segmented resume JSON files in input_dir and extract skills.
    Saves outputs to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize Skill Extractor
    logger.info(f"Initializing SkillExtractor with {dictionary_path}")
    extractor = SkillExtractor(dictionary_path)
    
    # Find all segmented JSON files
    input_files = [f for f in os.listdir(input_dir) if f.endswith("_segmented.json")]
    
    if not input_files:
        logger.warning(f"No segmented JSON files found in {input_dir}")
        print(f"No segmented JSON files found in {input_dir}")
        return

    print(f"\n{'='*70}")
    print(f"      ZECPATH - SKILL EXTRACTION ENGINE      ")
    print(f"{'='*70}")
    print(f"Found {len(input_files)} resumes to process.\n")
    
    total_processed = 0
    
    for filename in input_files:
        filepath = os.path.join(input_dir, filename)
        logger.info(f"Processing: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                segmented_resume = json.load(f)
            
            # Normalize keys to lowercase for robust lookup
            resume_lower = {k.lower(): v for k, v in segmented_resume.items()}
            
            # Identify the skills section or fallback to the whole document
            skills_text = resume_lower.get("skills", "")
            experience_text = resume_lower.get("work_experience", "") or resume_lower.get("experience", "")
            projects_text = resume_lower.get("projects", "")
            summary_text = resume_lower.get("summary", "")
            
            # Combine relevant sections for a richer extraction context
            context_text = f"{skills_text}\n\n{summary_text}\n\n{experience_text}\n\n{projects_text}"
            
            # Extract skills (passing 'skills' as the intended primary context)
            extracted = extractor.extract_skills(context_text, section_context="skills")
            
            # Strategy to extract name from contact_info string
            contact_str = resume_lower.get("contact_info", "")
            candidate_name = "Unknown"
            if contact_str and isinstance(contact_str, str):
                name_line = contact_str.strip().split('\n')[0]
                if len(name_line) < 50: # Sanity check for a name
                    candidate_name = name_line.strip()
            
            # Prepare output structure
            output_data = {
                "resume_file": filename,
                "candidate_name": candidate_name,
                "found_skills": extracted,
                "summary": {
                    "total_skills": len(extracted),
                    "categories": sorted(list(set(s["category"] for s in extracted))),
                    "high_confidence_skills": [s["skill"] for s in extracted if s["confidence"] >= 0.95]
                }
            }
            
            # Save results
            out_filename = filename.replace("_segmented.json", "_skills.json")
            out_path = os.path.join(output_dir, out_filename)
            
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"  [+] Processed: {filename}")
            print(f"      - Candidate: {output_data['candidate_name']}")
            print(f"      - Skills Found: {output_data['summary']['total_skills']}")
            print(f"      - Saved to: {out_path}")
            print("-" * 50)
            
            total_processed += 1
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            print(f"  [-] Failed: {filename} - See logs for details.")

    print(f"\n{'='*70}")
    print(f"SKILL EXTRACTION COMPLETE: {total_processed}/{len(input_files)} FILES PROCESSED")
    print(f"Outputs available in: {output_dir}")
    print(f"{'='*70}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zecpath Skill Extraction Pipeline")
    parser.add_argument("--input", default="data/samples/labeled", help="Dir containing segmented resume JSONs")
    parser.add_argument("--output", default="data/processed/extracted_skills", help="Dir to save skill results")
    parser.add_argument("--dict", default="data/skills/master_skills.json", help="Path to master skills JSON")
    
    args = parser.parse_args()
    run_skill_extraction(args.input, args.output, args.dict)
