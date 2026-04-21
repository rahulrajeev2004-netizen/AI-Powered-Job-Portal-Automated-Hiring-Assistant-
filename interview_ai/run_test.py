import json
from .pipeline import AIVoiceScreeningPipeline

def main():
    pipeline = AIVoiceScreeningPipeline()
    
    # Mock raw STT payload from a voice ingestion mechanism
    mock_raw_stt = [
        {
            "question_id": "Q-EXP-04",
            "question_text": "Can you describe your experience with Docker and APIs?",
            "raw_transcript": {
                "text": "I was, um, working on the, uh, database migration. I built I built the API using Python and Docker.",
                "confidence": 0.92,
                "duration_seconds": 25.5
            }
        },
        {
            "question_id": "Q-BEH-01",
            "question_text": "What do you do when a project gets blocked?",
            "raw_transcript": {
                "text": "We was gonna deploy it, but it got blocked. So I communicated with the team.",
                "confidence": 0.88,
                "duration_seconds": 15.0
            }
        }
    ]
    
    # Run pipeline
    output = pipeline.process_stt_result(
        session_id="sess_12345",
        candidate_id="cand_98765",
        job_id="JOB-DEV-001",
        raw_stt_payload=mock_raw_stt
    )
    
    # Save the output to outputs folder
    output_path = "../outputs/voice_screening_final_output.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=4)
        
    print(f"Output generated successfully at {output_path}")

if __name__ == "__main__":
    main()
