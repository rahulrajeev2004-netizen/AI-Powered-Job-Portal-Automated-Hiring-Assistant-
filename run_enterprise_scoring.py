import os
import json
from parsers.enhanced_parser import EnhancedResumeParser
from scoring.hiring_fit_calculator import HiringIntelligenceSystem

def run_enterprise_analysis():
    resumes_dir = "data/resumes"
    output_dir = "outputs"
    output_file = os.path.join(output_dir, "unified_candidate_scores.json")
    
    # Mock Job Requirements
    job_requirements = {
        "mandatory_skills": ["Python", "SQL", "Communication"],
        "min_years": 2,
        "min_degree": "Bachelor"
    }

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    resume_files = [f for f in os.listdir(resumes_dir) if f.endswith('.pdf')]
    
    final_report = []
    
    print(f"Processing {len(resume_files)} resumes with Enterprise Intelligence Engine...")

    for resume_name in resume_files:
        file_path = os.path.join(resumes_dir, resume_name)
        
        # 1. Enhanced Parsing
        parser = EnhancedResumeParser(file_path)
        parser.extract_text()
        structured_data = parser.get_structured_data()
        
        # 2. Role Determination (Demonstration)
        role = "default"
        if "developer" in resume_name.lower():
            role = "software engineer"
        elif "analyst" in resume_name.lower():
            role = "data analyst"
        elif "nurse" in resume_name.lower():
            role = "hr role" # Just to test the weight profile for communication-heavy roles

        # 3. Full Intelligence Processing
        unified_score = HiringIntelligenceSystem.process_candidate(
            candidate_filename=resume_name,
            job_role=role,
            structured_data=structured_data,
            job_reqs=job_requirements
        )
        
        final_report.append(unified_score.model_dump())
        print(f" - {resume_name}: Score {unified_score.final_score} ({unified_score.decision})")

    # Save to output
    with open(output_file, "w") as f:
        json.dump(final_report, f, indent=2)
        
    print(f"\nSUCCESS: Enterprise Intelligence Report generated at {output_file}")

if __name__ == "__main__":
    run_enterprise_analysis()
