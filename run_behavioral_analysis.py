import json
import os
from interview_ai.behavioral_analyzer import BehavioralAnalyzer
from datetime import datetime

def run_analysis():
    input_file = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\outputs\automated_screening_report.json"
    output_dir = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\outputs"
    output_file = os.path.join(output_dir, "behavioral_indicators_report.json")

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Prepare QA data for v3 engine
    timestamp = datetime.now().isoformat() + "Z"
    qa_input = []
    for qa in data.get("question_analysis", []):
        qa_input.append({
            "candidate_id": data.get("candidate_id"),
            "job_role": data.get("job_role"),
            "question_id": qa.get("question_id"),
            "answer": qa.get("answer"),
            "timestamp": timestamp
        })

    if not qa_input:
        print("No question analysis data found in the report.")
        return

    analyzer = BehavioralAnalyzer()
    
    # Run analysis - Returns the v3-production-hard report object
    report = analyzer.analyze_candidate(qa_input)

    # Final save
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Behavioral Intelligence Report (v3-Hard) generated: {output_file}")

if __name__ == "__main__":
    run_analysis()
