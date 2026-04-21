import json
import os
from .pipeline import AIVoiceScreeningPipeline

def main():
    pipeline = AIVoiceScreeningPipeline()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load dataset
    dataset_path = os.path.join(project_root, "data", "output", "hr_screening_dataset.json")
    with open(dataset_path, "r", encoding='utf-8') as f:
        dataset = json.load(f)
        
    se_questions = dataset['conversation_flow']['role_based_flow']['Software Engineer']
    q_bank = {q['question_id']: q['question_text']['en'] for q in dataset['question_bank']}
    
    # Mock voice transcripts based on John Doe's resume
    # John Doe: SE, 10+ years exp in AWS/Azure, Master's from Stanford
    mock_stt = [
        {
            "question_id": "Q_INTRO_01",
            "question_text": q_bank.get("Q_INTRO_01"),
            "raw_transcript": {
                "text": "Uh, hi, I am John. I have about, um, ten years of experience in Cloud Architecture mostly with AWS and Azure.",
                "confidence": 0.94,
                "duration_seconds": 15.0
            }
        },
        {
            "question_id": "Q_EDU_01",
            "question_text": q_bank.get("Q_EDU_01"),
            "raw_transcript": {
                "text": "I got my Master of Science in Computer Science from Stanford University back in, uh, 2012.",
                "confidence": 0.98,
                "duration_seconds": 10.0
            }
        },
        {
            "question_id": "Q_EXP_01",
            "question_text": q_bank.get("Q_EXP_01"),
            "raw_transcript": {
                "text": "Like I said I have over ten years of professional experience.",
                "confidence": 0.95,
                "duration_seconds": 5.0
            }
        },
        {
            "question_id": "Q_SKILL_05",
            "question_text": q_bank.get("Q_SKILL_05"),
            "raw_transcript": {
                "text": "Yes, I have worked heavily with DevOps tools, so I use Docker and Kubernetes daily.",
                "confidence": 0.92,
                "duration_seconds": 8.0
            }
        }
    ]

    output = pipeline.process_stt_result(
        session_id="sess_johndoe_001",
        candidate_id="cand_john_doe",
        job_id="ROLE_SW_ENG",
        raw_stt_payload=mock_stt
    )
    
    output_path = os.path.join(project_root, "outputs", "resume_based_voice_eval.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=4)
        
    print(f"Output generated successfully at {output_path}")

if __name__ == "__main__":
    main()
