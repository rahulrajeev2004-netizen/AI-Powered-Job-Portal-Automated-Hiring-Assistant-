import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from interview_ai.report_builder import RecruiterReportBuilder

def main():
    print("="*60)
    print("   RECRUITER-FRIENDLY REPORT BUILDER")
    print("="*60)

    # Define paths
    ANALYSIS_RESULTS = os.path.join("outputs", "answer_analysis_results.json")
    EVALUATION_REPORT = os.path.join("outputs", "automated_screening_report.json")
    BEHAVIORAL_REPORT = os.path.join("outputs", "behavioral_indicators_report.json")
    OUTPUT_DIR = "outputs"

    # Initialize Builder
    # Candidate ID is usually found in the evaluation report
    candidate_id = "cand_d7e57bdf" # Default fallback
    
    import json
    if os.path.exists(EVALUATION_REPORT):
        with open(EVALUATION_REPORT, 'r') as f:
            data = json.load(f)
            candidate_id = data.get("candidate_id", candidate_id)

    builder = RecruiterReportBuilder(candidate_id)
    
    print(f"[*] Loading data for candidate: {candidate_id}...")
    builder.load_data(ANALYSIS_RESULTS, EVALUATION_REPORT, BEHAVIORAL_REPORT)
    
    print("[*] Building recruiter report...")
    builder.build()
    
    print("[*] Saving exportable formats (JSON & Markdown)...")
    json_path, md_path = builder.save_report(OUTPUT_DIR)
    
    print("="*60)
    print(f"SUCCESS: Report Builder finished.")
    print(f"JSON Report: {json_path}")
    print(f"MD Report:   {md_path}")
    print("="*60)

if __name__ == "__main__":
    main()
