import json
import os
import sys

# Add project root to sys.path
project_root = r'C:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath'
sys.path.append(project_root)

from interview_ai.transcript_processor import BulkTranscriptProcessor

def upgrade_dataset_v4():
    input_path = os.path.join(project_root, 'outputs', 'bulk_resumes_voice_eval.json')
    output_path = os.path.join(project_root, 'outputs', 'cleaned_transcripts_20260422.json')
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
        
    processor = BulkTranscriptProcessor(stt_provider="mock")
    
    upgraded_sessions = []
    for cand in candidates:
        cand_id = cand['application'].get('candidate_id')
        print(f"Upgrading session for Candidate: {cand_id} to Semantic Intelligence v4.0")
        session_v4 = processor.process_session(cand)
        upgraded_sessions.append(session_v4)
        
    final_output = {
        "metadata": {
            "engine": "AI Transcript Processing Engine v4.0 (Semantic Session Intelligence)",
            "project": "Project Zecpath",
            "generated_at": "2026-04-22T09:04:00Z",
            "source_file": "bulk_resumes_voice_eval.json",
            "schema_version": "transcript_processed_v4.0_semantic"
        },
        "sessions": upgraded_sessions
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4)
        
    print(f"Successfully upgraded dataset to v4.0 schema. Saved to: {output_path}")

if __name__ == "__main__":
    upgrade_dataset_v4()
