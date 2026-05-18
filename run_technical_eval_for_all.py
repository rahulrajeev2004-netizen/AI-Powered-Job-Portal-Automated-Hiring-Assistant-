import os
import json
import re
from typing import Dict, List, Any

# Ensure project root is in sys.path
import sys
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from technical_ai.core_engine import AssessmentPipeline

def get_candidate_role_and_transcript(name: str) -> tuple:
    """
    Simulates domain-specific interview responses based on the candidate's profile.
    This demonstrates the engine's ability to evaluate conceptual depth, reasoning,
    and real-world applicability.
    """
    name_lower = name.lower()
    
    if "rahul" in name_lower:
        # Data Science & ML profile
        role = "ml_data_science"
        responses = [
            "I use Python for machine learning models.", # Shallow (Q1)
            "I use Python along with Pandas and NumPy for preprocessing, and train models like Decision Trees.", # Moderate (Q2)
            "I implement end-to-end ML pipelines including feature engineering with Scikit-learn, training linear models, and tuning hyperparameters to optimize accuracy and prevent overfitting." # Deep (Q3)
        ]
    elif "anita" in name_lower:
        # Nurse Manager -> evaluating clinical systems / MERN dashboards
        role = "mern_fullstack"
        responses = [
            "I use React.", # Shallow (Q1)
            "I build healthcare dashboards using React and Node.js to show patient metrics.", # Moderate (Q2)
            "I design scalable clinical dashboards using React hooks and Node.js microservices, optimizing data queries to minimize database latency and ensure HIPAA-compliant secure storage." # Deep (Q3)
        ]
    elif "reshma" in name_lower:
        # Nurse with basic IT concepts
        role = "mern_fullstack"
        responses = [
            "I know some Javascript.", # Shallow (Q1)
            "I use CSS and HTML to design basic clinical logs.", # Shallow (Q2)
            "I have used basic JavaScript to create simple form validations for scheduling systems." # Moderate (Q3)
        ]
    elif "nurse" in name_lower:
        # Nurse with minimal coding
        role = "mern_fullstack"
        responses = [
            "I don't have much coding experience.", # Shallow (Q1)
            "I used simple syntax in Excel.", # Shallow (Q2)
            "I have basic understanding of syntax and database concepts." # Shallow (Q3)
        ]
    else:
        # Fallback profile (e.g. Cloud/DevOps for sample_2)
        role = "cloud_devops"
        responses = [
            "I deploy apps on cloud platforms.", # Shallow (Q1)
            "I use Docker to containerize services.", # Moderate (Q2)
            "I orchestrate microservices with Kubernetes, defining YAML manifests for automated rolling updates and container self-healing to maintain high availability in production." # Deep (Q3)
        ]
        
    return role, responses

def evaluate_all_candidates():
    labeled_dir = "data/samples/labeled"
    
    # Identify all segmented resume files representing the resumes in data/resumes
    segmented_files = [f for f in os.listdir(labeled_dir) if f.endswith("_segmented.json")]
    
    if not segmented_files:
        print("No segmented resume files found in data/samples/labeled.")
        return
        
    all_reports = []
    
    print(f"Starting bulk technical evaluation for {len(segmented_files)} candidates...\n")
    
    for filename in segmented_files:
        filepath = os.path.join(labeled_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            resume_data = json.load(f)
            
        # Extract candidate name
        contact_str = resume_data.get("contact_info", "")
        candidate_name = filename.replace("_segmented.json", "").replace("_", " ")
        if contact_str and isinstance(contact_str, str):
            name_line = contact_str.strip().split('\n')[0].strip()
            if len(name_line) < 40:
                candidate_name = name_line
                
        # Parse experience years
        exp_text = (resume_data.get("summary", "") + " " + resume_data.get("work_experience", "")).lower()
        exp_search = re.search(r'(\d+)\+?\s*years?', exp_text)
        exp_years = int(exp_search.group(1)) if exp_search else 2
        
        # Determine appropriate role and simulate interview responses
        role, responses = get_candidate_role_and_transcript(candidate_name)
        
        candidate_info = {
            "name": candidate_name,
            "role": role,
            "experience_years": exp_years
        }
        
        print(f"  [+] Evaluating: {candidate_name} ({role}, {exp_years} years exp)")
        
        pipeline = AssessmentPipeline(candidate_info)
        report = pipeline.run(responses)
        
        # Override mock ID with dynamic name mapping if desired, otherwise let scorer assign
        report["candidate_id"] = f"C_{filename.replace('_segmented.json', '').upper()}"
        
        all_reports.append(report)
        
    # Save the consolidated final reports to outputs/technical_report.json
    os.makedirs("outputs", exist_ok=True)
    output_path = "outputs/technical_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)
        
    print(f"\nCOMPLETED. Bulk evaluations saved directly to {output_path}")

if __name__ == "__main__":
    evaluate_all_candidates()
