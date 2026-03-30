import json
import os

def split_master_report():
    master_file = 'data/processed/master_experience_report.json'
    output_dir = 'data/processed/candidate_experience_reports'
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(master_file):
        print(f"Error: {master_file} not found.")
        return

    with open(master_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for res in data:
        # Clean the candidate name for a filename
        raw_name = res.get('candidate_name', 'Unknown_Candidate')
        safe_name = "".join([c if c.isalnum() else "_" for c in raw_name.split('\n')[0].strip()])
        
        out_path = os.path.join(output_dir, f"{safe_name}_Master_Matches.json")
        
        with open(out_path, 'w', encoding='utf-8') as out_f:
            json.dump(res, out_f, indent=2, ensure_ascii=False)
            
        print(f"Saved: {out_path}")

if __name__ == "__main__":
    split_master_report()
