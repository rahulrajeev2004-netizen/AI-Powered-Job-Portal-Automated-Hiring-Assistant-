import os
import json
import argparse
import sys

# Ensure current directory is in sys.path
sys.path.append(os.getcwd())
from engines.experience_analyzer.experience_analyzer import ExperienceAnalyzer
from parsers.jd_parser import parse_jd
from utils.logger import get_logger

logger = get_logger("run_experience_analyzer", "logs/experience_run.log")

def run_analysis(resume_json_path: str, jd_path: str, current_date: str = "2026-03"):
    """
    Perform experience analysis with dynamic JD parsing support.
    """
    try:
        # 1. Load Resume (JSON format required, usually segmented)
        if not os.path.exists(resume_json_path):
            raise FileNotFoundError(f"Resume JSON not found: {resume_json_path}")
        with open(resume_json_path, 'r', encoding='utf-8') as f:
            resume_data = json.load(f)
            
        # 2. Load or Parse JD Data
        if not os.path.exists(jd_path):
            raise FileNotFoundError(f"JD file not found: {jd_path}")
            
        if jd_path.lower().endswith('.txt'):
            # Parse raw text on the fly
            with open(jd_path, 'r', encoding='utf-8') as f:
                jd_raw_text = f.read()
            jd_data = parse_jd(jd_raw_text)
            logger.info(f"Parsed text JD: {jd_path}")
        else:
            # Load existing JSON
            with open(jd_path, 'r', encoding='utf-8') as f:
                jd_data_raw = json.load(f)
                jd_data = jd_data_raw[0] if isinstance(jd_data_raw, list) else jd_data_raw
            logger.info(f"Loaded JSON JD: {jd_path}")

        # 3. Use Experience from Resume
        # Section key search for 'work_experience' or 'experience'
        resume_lower = {k.lower(): v for k, v in resume_data.items()}
        experience_text = resume_lower.get("work_experience", "") or resume_lower.get("experience", "")
        
        # 4. Initialize and Analyze
        analyzer = ExperienceAnalyzer(current_date=current_date)
        results = analyzer.analyze(experience_text, jd_data)
        
        # 5. Output Result (STRICT JSON ONLY)
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        # Standard error JSON conforming to schema
        error_json = {
          "total_experience_months": 0,
          "meets_experience_requirement": False,
          "final_relevance_score": 0.0,
          "domain_match": False,
          "experiences": [],
          "gaps": [],
          "overlaps": [],
          "error": str(e)
        }
        print(json.dumps(error_json, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zecpath Experience Analysis Engine")
    parser.add_argument("--resume", default="data/samples/labeled/sample_resume_segmented.json", 
                        help="Path to the segmented resume JSON")
    parser.add_argument("--jd", default="data/samples/sample_jds.json", 
                        help="Path to the JD JSON or TXT file")
    parser.add_argument("--date", default="2026-03", help="Simulation date (YYYY-MM)")
    
    args = parser.parse_args()
    
    run_analysis(args.resume, args.jd, args.date)
