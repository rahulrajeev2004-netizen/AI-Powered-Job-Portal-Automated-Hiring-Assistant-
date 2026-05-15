import json
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interview_ai.pipeline import AIVoiceScreeningPipeline

def main():
    dataset_path = "demo/hr_demo_dataset.json"
    output_path = "outputs/hr_demo_pipeline_output.json"
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        demo_data = json.load(f)
        
    pipeline = AIVoiceScreeningPipeline()
    results = []
    
    for candidate in demo_data:
        print(f"Processing candidate: {candidate['candidate_id']} ({candidate['role']})")
        
        # Convert simple QA format into STT format expected by the pipeline
        stt_payload = []
        for i, ans in enumerate(candidate["answers"]):
            stt_payload.append({
                "question_id": f"Q_SKILL_{i+1:02d}", # Simulate skill intent
                "question_text": ans["question"],
                "raw_transcript": {
                    "text": ans["answer"],
                    "confidence": 0.95,
                    "duration_seconds": 15.0
                }
            })
            
        result = pipeline.process_stt_result(
            session_id=f"SESSION-{candidate['candidate_id']}",
            candidate_id=candidate["candidate_id"],
            job_id="JOB-DEMO-001",
            raw_stt_payload=stt_payload,
            classified_role=candidate["role"]
        )
        results.append(result)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nSuccessfully generated deliverable output at {output_path}")

if __name__ == "__main__":
    main()
