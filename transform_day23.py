import json
import re

def transform():
    with open('outputs/bulk_resumes_voice_eval.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    out_data = []
    filler_words = r'\b(uh|um|like|you know|exactly)\b'
    
    for c in data:
        new_transcript = []
        qa_list = c.get('qa_breakdown', [])
        
        for q in qa_list:
            score_block = q.get('score', {})
            stt_conf = score_block.get('confidence')
            
            raw = q.get('answer_raw', '')
            norm = q.get('answer_normalized', '')
            
            if not norm:
                norm = re.sub(filler_words, '', raw, flags=re.IGNORECASE)
                norm = re.sub(r'[,]+', ',', norm)
                norm = re.sub(r'\s+', ' ', norm).strip()
                norm = norm.strip(', ')
                
            new_transcript.append({
                "question_id": q.get('question_id', ''),
                "timestamp": q.get('start_time', ''),
                "raw_transcript": raw,
                "normalized_text": norm,
                "stt_confidence": stt_conf
            })
            
        new_c = {
            "application": {
                "candidate_id": c.get('application', {}).get('candidate_id', ''),
                "job_id": c.get('application', {}).get('job_id', ''),
                "session_id": c.get('application', {}).get('session_id', ''),
                "timestamp": c.get('application', {}).get('timestamp', '')
            },
            "interaction_summary": {
                "total_questions_answered": c.get('interaction_summary', {}).get('total_questions_answered', 0),
                "total_duration_seconds": c.get('interaction_summary', {}).get('total_duration_seconds', 0.0),
                "average_stt_confidence": c.get('interaction_summary', {}).get('average_stt_confidence', 0.0)
            },
            "transcript": new_transcript
        }
        out_data.append(new_c)
        
    with open('outputs/bulk_resumes_voice_eval.json', 'w', encoding='utf-8') as f:
        json.dump(out_data, f, indent=4)

if __name__ == "__main__":
    transform()
