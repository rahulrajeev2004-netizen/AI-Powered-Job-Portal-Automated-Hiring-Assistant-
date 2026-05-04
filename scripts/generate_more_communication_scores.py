import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from interview_ai.communication_scoring import calculate_communication_score

def process_transcripts():
    input_path = os.path.join(base_dir, 'outputs', 'cleaned_transcripts_20260428.json')
    output_path = os.path.join(base_dir, 'outputs', 'sample_communication_scores_batch.json')
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    results = {}
    
    for session in data.get('sessions', []):
        candidate_name = session.get('candidate_profile', {}).get('candidate_name', 'Unknown')
        
        # Extract evidence text
        utterances = []
        strengths = session.get('session_summary', {}).get('score_explanation', {}).get('top_strengths', [])
        for s in strengths:
            evidence = s.get('evidence', '')
            if evidence:
                # Remove quotes if present
                evidence = evidence.strip('"')
                utterances.append(evidence)
                
        if utterances:
            combined_text = " ".join(utterances)
            score_data = calculate_communication_score(combined_text)
            
            results[candidate_name] = {
                "combined_text": combined_text,
                "score_evaluation": score_data
            }
            
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print(f"Generated {len(results)} sample scores in {output_path}")

if __name__ == '__main__':
    process_transcripts()
