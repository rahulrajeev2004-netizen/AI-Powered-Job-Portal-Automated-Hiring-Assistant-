import os
import sys
import json
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from interview_ai.communication_scoring import calculate_communication_score
from interview_ai.behavioral_analyzer import BehavioralAnalyzer
from interview_ai.answer_understanding import AIAnswerUnderstandingEngine
from interview_ai.hr_scoring_engine import HREvaluationProcessor

def extract_qa_pairs(transcript_path: str) -> list:
    qa_pairs = []
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_question = ""
        current_answer = ""
        is_candidate = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('**AI System**: '):
                if current_question and current_answer:
                    qa_pairs.append({
                        "question_id": f"Q_{len(qa_pairs)+1}",
                        "question": current_question,
                        "answer": current_answer
                    })
                current_question = line[len('**AI System**: '):].strip()
                current_answer = ""
                is_candidate = False
            elif line.startswith('**Candidate**: '):
                text = line[len('**Candidate**: '):].strip()
                text = re.sub(r'\*\*\[.*?\]\*\*', '', text).strip()
                current_answer = text
                is_candidate = True
            elif is_candidate and line:
                current_answer += " " + line
                
        if current_question and current_answer:
            qa_pairs.append({
                "question_id": f"Q_{len(qa_pairs)+1}",
                "question": current_question,
                "answer": current_answer
            })
    except Exception as e:
        print(f"Error reading transcript: {e}")
        
    return qa_pairs

def generate_hr_score_report():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    transcript_path = os.path.join(base_dir, 'outputs', 'sample_recruiter_call_transcript.md')
    output_path = os.path.join(base_dir, 'outputs', 'candidate_hr_score_report.json')
    
    qa_pairs = extract_qa_pairs(transcript_path)
    if not qa_pairs:
        print("No Q&A pairs found or file not found. Creating mock data.")
        qa_pairs = [
            {"question_id": "Q_1", "question": "Can you tell me about your experience in Python?", "answer": "I have about 4 years of experience using Python for backend development."},
            {"question_id": "Q_2", "question": "What are your salary expectations?", "answer": "I am looking for around 20 lpa."},
            {"question_id": "Q_3", "question": "Are you willing to relocate to Thiruvananthapuram?", "answer": "Yes, I am completely open to relocating."}
        ]
        
    print(f"Extracted {len(qa_pairs)} Q&A pairs.")
    
    # 1. Answer Relevance
    answer_engine = AIAnswerUnderstandingEngine()
    relevance_scores = []
    for qa in qa_pairs:
        result = answer_engine.analyze_answer(qa["question"], "general", qa["answer"], qa["question_id"])
        relevance_scores.append(result.get("confidence_score", 0.5))
        
    # 2. Communication Score
    combined_answers = " ".join([qa["answer"] for qa in qa_pairs])
    comm_result = calculate_communication_score(combined_answers)
    comm_score = comm_result.get("communication_score", 50.0)
    
    # 3. Behavioral Consistency & Confidence
    behavioral_engine = BehavioralAnalyzer()
    
    behavioral_qa_format = [{"question_id": qa["question_id"], "answer": qa["answer"]} for qa in qa_pairs]
    behavioral_result = behavioral_engine.analyze_candidate(behavioral_qa_format)
    
    # Confidence is inside detailed_metrics -> communication_strength_index or confidence
    # Or average confidence from results
    conf_sum = sum([r["uncertainty"]["uncertainty_score"] for r in behavioral_result.get("question_level_breakdown", [])])
    avg_uncertainty = conf_sum / len(qa_pairs) if qa_pairs else 0.5
    confidence_score = 1.0 - avg_uncertainty
    
    # Consistency
    overall_risk = behavioral_result.get("risk_analysis", {}).get("overall_risk_score", 0.5)
    consistency_score = 1.0 - overall_risk
    
    
    # Determine experience level and instantiate processor
    candidate_type = "experienced" if any("years of experience" in qa["answer"].lower() for qa in qa_pairs) else "fresher"
    hr_processor = HREvaluationProcessor(candidate_experience_level=candidate_type)

    # 4. Score per answer using the processor
    scored_answers = []
    for i, qa in enumerate(qa_pairs):
        # Format the answer object correctly
        answer_data = {
            "question_id": qa["question_id"],
            "relevance_score": relevance_scores[i],
            "communication_score": comm_score,
            "confidence_score": confidence_score * 100, # Assuming scale is 0-100 inside
            "contradiction": False, # Mock value for consistency
            "is_vague": False
        }
        scored = hr_processor.process_single_answer(answer_data)
        scored_answers.append(scored)
        
    final_report = hr_processor.format_hr_report(scored_answers, candidate_id="cand_99fb956a")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=4)
        
    print(f"Candidate HR score report generated at {output_path}")

if __name__ == "__main__":
    generate_hr_score_report()
