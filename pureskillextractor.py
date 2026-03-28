import json
import os
import re
from parsers.pdf_parser import extract_text_from_pdf

# 1. Define Skill Dictionary (Master Skill -> Synonyms)
SKILL_DICTIONARY = {
    "python": ["python", "py", "python3", "python programming"],
    "sql": ["sql", "mysql", "postgresql", "structured query language"],
    "aws": ["aws", "amazon web services", "s3", "ec2", "lambda"],
    "java": ["java", "j2ee", "core java", "java programming"],
    "javascript": ["javascript", "js", "ecmascript", "es6"],
    "react": ["react", "reactjs", "react.js"],
    "node.js": ["node.js", "nodejs", "node"],
    "django": ["django", "django framework", "drf"],
    "flask": ["flask", "flask framework", "flask api"],
    "pandas": ["pandas", "pandas library"],
    "numpy": ["numpy", "numpy library"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "machine learning": ["machine learning", "ml", "ml/ai"],
    "deep learning": ["deep learning", "dl", "neural networks"],
    "docker": ["docker", "docker containerization"],
    "kubernetes": ["k8s", "kubernetes", "kube"],
    "git": ["git", "github", "version control"],
    "project management": ["project management", "pm", "project mgmt"],
    "leadership": ["leadership", "led teams", "people management"],
    "agile": ["agile", "scrum", "kanban", "agile methodology"],
    "communication": ["communication", "verbal communication", "written communication"],
    "problem solving": ["problem solving", "analytical thinking", "critical thinking"],
    "polymer synthesis": ["polymer synthesis fundamentals", "polymer characterization", "polymer synthesis"],
    "chemical analysis": ["chemical analysis techniques", "analytical chemistry", "chemical analysis"],
    "laboratory skills": ["laboratory documentation", "laboratory techniques", "lab reporting"]
}

def load_resumes_from_folder(folder_path):
    """Step 1: Load Resume files from the given folder."""
    resumes_to_process = []
    if not os.path.exists(folder_path):
        print(f"Error: Folder not found at {folder_path}")
        return []
        
    for f in os.listdir(folder_path):
        if f.endswith(".pdf") or f.endswith(".txt"):
            resumes_to_process.append({"name": f, "path": os.path.join(folder_path, f)})
    return resumes_to_process

def extract_skills_with_confidence(text):
    """Step 4, 5, 6: Skill Matching, Frequency, and Confidence Scoring."""
    found_skills = []
    text_lower = text.lower()
    
    for standard_name, variants in SKILL_DICTIONARY.items():
        total_freq = 0
        for variant in variants:
            # Word-boundary safe check
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(variant.lower()) + r"(?![a-zA-Z0-9])"
            matches = re.findall(pattern, text_lower)
            total_freq += len(matches)
        
        if total_freq > 0:
            # Confidence Scoring based on frequency
            if total_freq > 2:
                confidence = 0.95
            elif total_freq == 2:
                confidence = 0.85
            else: # freq == 1
                confidence = 0.75
            
            found_skills.append({
                "name": standard_name,
                "confidence": confidence
            })
            
    return found_skills

def save_output(skills, filename, output_dir):
    """Step 8: Save skill JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    out_name = filename.replace(".pdf", "").replace(".txt", "") + "_skills.json"
    filepath = os.path.join(output_dir, out_name)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=2)
    return filepath

def run_extraction_pipeline(input_folder, output_dir):
    """Main pipeline for parsing and matching."""
    resumes = load_resumes_from_folder(input_folder)
    
    print("="*60)
    print("      Skill Extraction Engine - Processing Actual Resumes      ")
    print("="*60)

    for sample in resumes:
        filename = sample["name"]
        filepath = sample["path"]
        print(f"\n[*] Processing: {filename}")
        
        # Step 2: Extract and clean text
        raw_text = ""
        if filename.endswith(".pdf"):
            raw_text = extract_text_from_pdf(filepath)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()

        if not raw_text.strip():
            print(f"  [!] Skipped: No text found in {filename}.")
            continue
            
        # Step 3, 4, 5, 6: Process skills
        skills = extract_skills_with_confidence(raw_text)
        
        # Step 9: Logging
        if not skills:
            print("  - No skills recognized from dictionary.")
        else:
            print(json.dumps(skills, indent=2))
        
        # Step 8: Save
        save_output(skills, filename, output_dir)

    print("\n" + "="*60)
    print("      Day 9 Task: Completed Successfully      ")
    print("="*60)

if __name__ == "__main__":
    RESUMES_FOLDER = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\data\resumes"
    OUTPUT_FOLDER = "outputs/skills"
    
    run_extraction_pipeline(RESUMES_FOLDER, OUTPUT_FOLDER)

