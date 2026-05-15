import json
import logging
import os
import sys
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Core internal engine imports
from interview_ai.call_flow_engine import CallFlowEngine
from interview_ai.pipeline import AIVoiceScreeningPipeline

logger = logging.getLogger(__name__)

class ProductionHRInterviewModule:
    """
    Enterprise-Grade Facade for the HR Interview AI System.
    This module provides a clean, production-ready API for integrating 
    the Zecpath AI Interviewer into ATS platforms or external dashboards.
    
    It orchestrates the real-time call flow, handles error recovery seamlessly, 
    and triggers the heavy analytical pipeline for the final HR decision.
    """
    
    def __init__(self, config_dir: str = "interview_ai/call_flow_system"):
        """
        Initializes the Production HR module.
        Ensures the CallFlow engine has access to the state machines and prompt configurations.
        """
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            
        self.config_dir = config_dir
        self.pipeline = AIVoiceScreeningPipeline()
        self.active_sessions: Dict[str, CallFlowEngine] = {}
        
    def start_new_interview(self, candidate_id: str, job_id: str) -> Dict[str, Any]:
        """
        Initializes a new interview session for a candidate.
        Returns the session ID and the first AI greeting.
        """
        try:
            engine = CallFlowEngine(config_dir=self.config_dir)
            session_id = engine.session_id
            
            # Store metadata needed for later evaluation
            engine.session_data = {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "transcripts": [] # Used to store the Q&A for the analytical pipeline
            }
            
            first_prompt = engine.start_call()
            self.active_sessions[session_id] = engine
            
            return {
                "status": "success",
                "session_id": session_id,
                "ai_prompt": first_prompt,
                "state": engine.current_state
            }
        except Exception as e:
            logger.error(f"Failed to start interview: {e}")
            return {"status": "error", "message": "System unavailable"}

    def process_candidate_audio_turn(
        self, 
        session_id: str, 
        transcribed_text: str, 
        confidence: float = 1.0, 
        silence_seconds: float = 0.0
    ) -> Dict[str, Any]:
        """
        Processes a single turn of the conversation. 
        Handles silence, low confidence STT, intent mapping, and state transitions.
        """
        if session_id not in self.active_sessions:
            return {"status": "error", "message": "Invalid or expired session"}
            
        engine = self.active_sessions[session_id]
        
        # 1. Process turn through the Call Flow Engine (includes Robustness Framework)
        response = engine.process_turn(
            user_input=transcribed_text,
            stt_confidence=confidence,
            silence_sec=silence_seconds
        )
        
        # 2. If it's a valid answer to a question (not just consent/greeting), log it for the pipeline
        if engine.current_state in ["QUESTIONING", "FOLLOW_UP"] and transcribed_text.strip() and silence_seconds < 3:
            question_id = f"Q_SKILL_{len(engine.session_data['transcripts']) + 1:02d}"
            
            engine.session_data['transcripts'].append({
                "question_id": question_id,
                "question_text": engine.last_ai_prompt,
                "raw_transcript": {
                    "text": transcribed_text,
                    "confidence": confidence,
                    "duration_seconds": max(len(transcribed_text.split()) * 0.5, 3.0) # Approx speaking duration
                }
            })

        return {
            "status": "success",
            "session_id": session_id,
            "ai_prompt": response["prompt"],
            "action": response.get("action", "CONTINUE"),
            "state": response["state"]
        }

    def conclude_and_evaluate(self, session_id: str, classified_role: str = "General") -> Dict[str, Any]:
        """
        Ends the interview call and triggers the massive HR evaluation pipeline.
        Returns the final hiring decision and detailed JSON report.
        """
        if session_id not in self.active_sessions:
            return {"status": "error", "message": "Invalid or expired session"}
            
        engine = self.active_sessions[session_id]
        
        # 1. Get the Call Flow summary (Compliance, Silence Drops, etc.)
        call_summary = engine.generate_evaluation()
        
        # 2. If no transcripts were collected, return early
        if not engine.session_data.get("transcripts"):
            return {
                "status": "partial",
                "call_summary": call_summary,
                "message": "Interview terminated before technical questions were answered."
            }
            
        # 3. Push data into the deep Analytical Pipeline
        final_evaluation = self.pipeline.process_stt_result(
            session_id=session_id,
            candidate_id=engine.session_data["candidate_id"],
            job_id=engine.session_data["job_id"],
            raw_stt_payload=engine.session_data["transcripts"],
            classified_role=classified_role
        )
        
        # Merge basic call flow compliance into the final eval
        final_evaluation["call_compliance"] = call_summary.get("compliance", {})
        
        # Cleanup memory
        del self.active_sessions[session_id]
        
        return {
            "status": "completed",
            "evaluation_report": final_evaluation
        }

    def run_hr_interview(
        self, 
        candidate_id: str, 
        answers: List[Dict[str, Any]], 
        communication: Dict[str, Any], 
        behavior: Dict[str, Any],
        ats_score: float = 70.0,
        screening_score: float = 75.0
    ) -> Dict[str, Any]:
        """
        Runs the standalone HR interview logic combining HR Scoring, 
        Unified ATS + HR Scoring, and final Summary Generation.
        """
        from interview_ai.hr_scoring_engine import HREvaluationProcessor
        from scoring.cross_round_scoring import UnifiedScoringEngine
        from interview_ai.summary_generator import InterviewSummaryGenerator

        # 1. Process HR Scoring Pipeline
        processor = HREvaluationProcessor("experienced")
        processed_answers = [processor.process_single_answer(ans) for ans in answers]
        hr_result = processor.format_hr_report(processed_answers, candidate_id)

        # 2. Calculate Unified Score across all rounds
        final_score_data = UnifiedScoringEngine.compute_weighted_aggregate(
            ats=ats_score,
            screening=screening_score,
            hr=hr_result["hr_interview_score"],
            candidate_type="experienced"
        )
        final_score = final_score_data["total_score"]

        # 3. Generate Natural Language Summary
        summary_engine = InterviewSummaryGenerator()
        summary = summary_engine.generate_interview_summary(
            candidate_id=candidate_id,
            hr_scores=hr_result["breakdown"],
            comm_data=communication,
            behavior_data=behavior,
            answers=answers
        )

        return {
            "candidate_id": candidate_id,
            "final_score": final_score,
            "unified_score_breakdown": final_score_data,
            "decision": summary["decision"],
            "natural_language_summary": summary.get("natural_language_summary", ""),
            "hr_interview_details": hr_result
        }

# For simple testing when executed directly
if __name__ == "__main__":
    import pprint
    module = ProductionHRInterviewModule()
    
    print("--- 1. Starting Interview ---")
    start = module.start_new_interview("Cand-001", "Job-DataEng")
    session = start["session_id"]
    print(f"AI: {start['ai_prompt']}")
    
    print("\n--- 2. Simulated Interaction ---")
    module.process_candidate_audio_turn(session, "Yes, I am here.")
    module.process_candidate_audio_turn(session, "John Doe.")
    turn3 = module.process_candidate_audio_turn(session, "I consent.")
    print(f"AI: {turn3['ai_prompt']}")
    
    print(f"\nCand: I have 5 years of Python and SQL experience.")
    turn4 = module.process_candidate_audio_turn(session, "I have 5 years of Python and SQL experience.")
    print(f"AI: {turn4['ai_prompt']}")
    
    print("\n--- 3. Concluding & Evaluating ---")
    result = module.conclude_and_evaluate(session, classified_role="Data Engineer")
    print(f"Final Decision: {result['evaluation_report']['final_decision']['status']}")
    print(f"Overall Score: {result['evaluation_report']['aggregate_scores']['overall_score']}")
    
    # Save the output
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/production_module_demo.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n[SUCCESS] Production module test complete. Output saved to outputs/production_module_demo.json")

    print("\n--- 4. Testing Offline HR Scoring & Summary Method ---")
    mock_answers = [
        {"question_id": "Q1", "answer_text": "I used Python and Docker.", "relevance_score": 0.8, "communication_score": 85.0, "confidence_score": 90.0, "aptitude_score": 80.0},
        {"question_id": "Q2", "answer_text": "I led a team of five engineers.", "relevance_score": 0.9, "communication_score": 90.0, "confidence_score": 95.0, "aptitude_score": 85.0}
    ]
    mock_comm = {"communication_score": 85.0}
    mock_behav = {"behavioral_score": 90.0, "confidence": {"confidence_score": 92.0}}
    
    hr_eval = module.run_hr_interview(
        candidate_id="Cand-002",
        answers=mock_answers,
        communication=mock_comm,
        behavior=mock_behav,
        ats_score=85.0,
        screening_score=80.0
    )
    print(f"Offline HR Eval Decision: {hr_eval['decision']}")
    print(f"Unified Final Score: {hr_eval['final_score']}")
    with open("outputs/production_module_offline_demo.json", "w") as f:
        json.dump(hr_eval, f, indent=2)
    print("[SUCCESS] Offline HR Eval test complete. Output saved to outputs/production_module_offline_demo.json")
