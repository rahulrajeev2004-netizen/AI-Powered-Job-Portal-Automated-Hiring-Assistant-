import os
import re

def split_jds(input_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find sections like "1. Staff Nurse", "2. Licensed Practical Nurse", etc.
    # It looks for a digit + dot + space at the beginning of a line.
    sections = re.split(r'\n(?=\d+\.\s)', content)
    
    # Handle the first section if it doesn't start with a newline
    if sections and not re.match(r'^\d+\.\s', sections[0]):
         # If it starts with "1. Staff Nurse" but no \n before it
         pass

    # Alternative split that handles the first one better
    # Find all start indices
    matches = list(re.finditer(r'(?:^|\n)(\d+)\.\s+(.*?)(?:\n|$)', content))
    
    for i in range(len(matches)):
        start_idx = matches[i].start()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(content)
        
        jd_text = content[start_idx:end_idx].strip()
        jd_title_raw = matches[i].group(2).strip()
        
        # Consistent naming with split_and_parse_jds.py but with numeric prefix for ordering
        # Strip parenthetical aliases e.g. "(Registered Nurse – RN)"
        clean_title = re.sub(r"\s*\(.*?\)", "", jd_title_raw).strip()
        # Build a safe filename
        safe_base = re.sub(r"[^\w\s-]", "", clean_title).strip().replace(" ", "_")
        
        # Add numeric prefix for ordering (e.g., 01_, 10_, 85_)
        job_num = int(matches[i].group(1))
        filename = f"{job_num:02d}_{safe_base}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as out_f:
            out_f.write(jd_text)
            
    print(f"Split {len(matches)} JDs into {output_dir}")

if __name__ == "__main__":
    input_path = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\data\samples\Nurse model.txt"
    output_path = r"c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\data\processed\individual_jds_txt"
    split_jds(input_path, output_path)
