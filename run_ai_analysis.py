import json
import os
from datetime import datetime, timezone
from interview_ai.answer_understanding import AIAnswerUnderstandingEngine

def main():
    # Setup paths
    INPUT_FILE = os.path.join("outputs", "bulk_resumes_voice_eval.json")
    OUTPUT_FILE = os.path.join("outputs", "answer_analysis_results.json")
    
    # Initialize Engine
    engine = AIAnswerUnderstandingEngine()
    
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_sessions = json.load(f)
    
    if not all_sessions:
        print("[ERROR] No sessions found in input file.")
        return

    # Process transcripts from the FIRST session
    session = all_sessions[0]
    candidate_name = session.get("application", {}).get("candidate_id", "Unknown")
    transcripts = session.get("transcript", [])
    
    results = []
    
    print("=" * 60)
    print(f"   AI ANSWER UNDERSTANDING ENGINE (AGGREGATOR) - SESSION RUN")
    print(f"   Candidate: {candidate_name}")
    print("=" * 60)
    
    for i, t in enumerate(transcripts, 1):
        q_id = t.get("question_id", "Q_UNKNOWN")
        q_type = t.get("intent", "other")
        answer = t.get("normalized_text", "")
        
        print(f"[{i}/{len(transcripts)}] Analyzing {q_id} ({q_type})...")
        
        analysis = engine.analyze_answer(
            question=f"Response to {q_id}",
            question_type=q_type,
            answer=answer,
            question_id=q_id
        )
        
        results.append({
            "question_id": q_id,
            "input": {
                "question_type": q_type,
                "answer": answer
            },
            "analysis": analysis
        })
    
    # Retrieve the consolidated global profile
    global_profile = engine.get_global_profile()
    
    # Build final output structure as per requirement
    output_data = {
        "metadata": {
            "engine": "AI Answer Understanding Engine v2.0 (Aggregator)",
            "candidate_id": candidate_name,
            "processed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "num_transcripts": len(results)
        },
        "global_profile": global_profile,
        "results": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print("=" * 60)
    print(f"Analysis complete. Results updated in: {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
