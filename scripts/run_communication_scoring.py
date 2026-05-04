import os
import sys
import json
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from interview_ai.communication_scoring import calculate_communication_score

def extract_candidate_utterances(transcript_path: str) -> list:
    utterances = []
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line.startswith('**Candidate**: '):
                # Extract text after **Candidate**: 
                text = line[len('**Candidate**: '):].strip()
                # Remove action tags like **[Silence 5s]**
                text = re.sub(r'\*\*\[.*?\]\*\*', '', text).strip()
                if text:
                    utterances.append(text)
    except Exception as e:
        print(f"Error reading transcript: {e}")
        
    return utterances

def generate_sample_score():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    transcript_path = os.path.join(base_dir, 'outputs', 'sample_recruiter_call_transcript.md')
    output_path = os.path.join(base_dir, 'outputs', 'sample_communication_score.json')
    
    utterances = extract_candidate_utterances(transcript_path)
    print(f"Extracted {len(utterances)} utterances from candidate.")
    for u in utterances:
        print(f"- {u}")
        
    combined_text = " ".join(utterances)
    result = calculate_communication_score(combined_text)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)
        
    print(f"Communication score output saved to {output_path}")

if __name__ == "__main__":
    generate_sample_score()
