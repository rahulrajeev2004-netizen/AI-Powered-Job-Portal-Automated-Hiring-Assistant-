import json
import os
import sys
import re
from typing import Dict, Any, List, Optional

# Ensure project root is in sys.path for direct execution
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from interview_ai.error_handling_framework import ErrorHandlingFramework
from interview_ai.followup_engine import FollowUpDetector, FollowUpGenerator
from interview_ai.adaptive_engine import AdaptiveDifficultyManager, AdaptiveQuestionBuilder

class CallFlowEngine:
    """
    Production-grade AI Call Flow Engine for dynamic voice interactions.
    Handles State Machine transitions, Silence/Confusion recovery, and Follow-up triggers.
    """

    def __init__(self, config_dir: str, language: str = "en"):
        self.config_dir = config_dir
        self.language = language
        self.session_id = "SES-" + str(os.getpid()) + "-" + str(int(os.times()[4] * 1000) % 1000)
        
        # Load configs with robust defaults
        self.state_machine = self._load_json("state_machine.json", {"states": ["INIT", "GREETING", "QUESTIONING", "FAILED"]})
        self.decision_rules = self._load_json("decision_rules.json", {
            "silence_logic": {"max_repeated_silences": 3, "tiers": []},
            "error_logic": {"asr_low_confidence": {"threshold": 0.45}}
        })
        self.prompts = self._load_json("prompts_engine.json", {
            "scenarios": {
                "asking_to_repeat": ["Could you please repeat that?"],
                "silence_recovery": ["I'm still here.", "Are you there?"],
                "callback_request": ["Should I call you back?"],
                "noise_recovery": ["I'm sorry, it's too noisy. Could you move to a quieter spot?"],
                "escalation": ["I'll have a human recruiter reach out to you."]
            }
        })
        
        # Session State
        self.current_state = "INIT"
        self.retry_counts = {}  # state_id -> count
        self.silence_count = 0
        self.session_data = {}
        self.last_ai_prompt = ""
        self.interaction_history = []
        
        # Error Handling Framework
        self.error_handler = ErrorHandlingFramework(session_id=self.session_id, candidate_id="CAND-001")
        # Follow-ups counter to prevent infinite looping
        self.follow_ups_triggered = 0

    def _load_json(self, filename: str, default: Dict[str, Any]) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if not os.path.exists(path):
            return default
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default

    def start_call(self) -> str:
        """Initializes the call and returns the first greeting."""
        self.current_state = "GREETING"
        prompt = "Hello! This is the Zecpath AI Interviewer. Am I speaking with the candidate?"
        self.last_ai_prompt = prompt
        return prompt

    def generate_evaluation(self) -> Dict[str, Any]:
        """Generates the final structured evaluation JSON."""
        return {
            "session_id": self.session_id,
            "timestamp": "2026-04-27T14:40:00Z",
            "final_state": self.current_state,
            "interaction_summary": {
                "total_turns": len(self.interaction_history),
                "completion_status": "SUCCESS" if self.current_state in ["COMPLETED", "QUESTIONING", "CONSENT"] else "PARTIAL",
                "errors_encountered": self.error_handler.session_errors.get(self.session_id, {})
            },
            "compliance": {
                "consent_obtained": any("consent" in str(h).get("user", "").lower() for h in self.interaction_history if "user" in h)
            },
            "raw_log": self.interaction_history
        }

    def process_turn(self, user_input: str, stt_confidence: float = 1.0, silence_sec: float = 0) -> Dict[str, Any]:
        """
        Processes a single turn using the upgraded Robustness Engine.
        """
        self.interaction_history.append({"user": user_input, "state": self.current_state, "confidence": stt_confidence})
        
        # 1. Handle Silence Logic
        if silence_sec > 2:
            robust_silence = self.error_handler.handle_silence(int(silence_sec))
            event = robust_silence["silence_event"]
            
            prompt = self.last_ai_prompt # Default
            if event["action"] == "REPROMPT":
                prompt = "I'm sorry, I didn't hear anything. " + self.last_ai_prompt
            elif event["action"] == "RETRY_QUESTION":
                prompt = "Are you still there? Let me repeat: " + self.last_ai_prompt
            elif event["action"] == "SKIP_FALLBACK":
                return self._handle_fallback("It seems we're having connection issues.")

            self.interaction_history.append({"ai": prompt, "state": self.current_state, "silence": True})
            return {"prompt": prompt, "state": self.current_state, "action": event["action"]}

        # 2. Robust Response Processing (NLP + Detection)
        qid = "Q-" + self.current_state
        robust_res = self.error_handler.process_response(user_input, qid, confidence=stt_confidence)
        
        if robust_res["action"] == "ESCALATE":
            prompt = self.prompts["scenarios"].get("escalation", ["I'm having trouble. Escalating to a human."])[0]
            self.interaction_history.append({"ai": prompt, "state": "ESCALATED", "action": "ESCALATE"})
            return {"prompt": prompt, "state": "ESCALATED", "action": "ESCALATE"}

        if robust_res["action"] == "REPROMPT":
            reason = robust_res.get("reason", "unknown error")
            if reason == "background_noise":
                prompt = self.prompts["scenarios"].get("noise_recovery", ["It's too noisy."])[0]
            else:
                prompt = f"I didn't quite get that ({reason.replace('_', ' ')}). Could you please clarify?"
            
            self.interaction_history.append({"ai": prompt, "state": self.current_state, "retry": True})
            return {"prompt": prompt, "state": self.current_state, "action": "REPROMPT"}

        # 3. State Transitions & Answer Processing
        res = self._transition_state(user_input)
        self.interaction_history.append({"ai": res["prompt"], "state": res["state"]})
        return res

    def _handle_fallback(self, fallback_prompt: str) -> Dict[str, Any]:
        """Safety fallback logic to keep the call moving."""
        if self.current_state == "GREETING":
            self.current_state = "FAILED"
            return {"prompt": "I'm sorry, I'm unable to proceed at this time. Goodbye.", "state": "FAILED", "action": "TERMINATE"}
        
        # Skip to next mandatory question
        self.current_state = "QUESTIONING"
        next_prompt = fallback_prompt + " Let's move on. How many years of total work experience do you have?"
        self.last_ai_prompt = next_prompt
        return {"prompt": next_prompt, "state": self.current_state, "action": "SKIP"}

    def _handle_silence(self, seconds: float) -> Dict[str, Any]:
        self.silence_count += 1
        tiers = self.decision_rules.get("silence_logic", {}).get("tiers", [])
        
        action = "encourage"
        phrase = self.prompts["scenarios"]["silence_recovery"][0]

        for tier in tiers:
            if tier["min_sec"] <= seconds < tier["max_sec"]:
                action = tier["action"]
                if action == "encourage":
                    phrase = self.prompts["scenarios"]["silence_recovery"][0]
                elif action == "reprompt":
                    phrase = self.prompts["scenarios"]["silence_recovery"][1]
                elif action == "direct_ask":
                    phrase = "I'm still here. " + self.last_ai_prompt
        
        if self.silence_count >= self.decision_rules.get("silence_logic", {}).get("max_repeated_silences", 3):
            self.current_state = "CALLBACK_REQUEST"
            return {
                "prompt": self.prompts["scenarios"]["callback_request"][0],
                "state": self.current_state,
                "action": "SCHEDULE_CALLBACK"
            }

        return {
            "prompt": phrase,
            "state": self.current_state,
            "action": action.upper()
        }

    def _is_confused(self, user_input: str) -> bool:
        confusion_triggers = ["what", "repeat", "understand", "pardon", "again", "clear", "not sure", "don't get"]
        user_input_lower = user_input.lower()
        if any(trigger in user_input_lower for trigger in confusion_triggers):
            return True
        return False

    def _handle_confusion(self, user_input: str) -> Dict[str, Any]:
        count = self.retry_counts.get(self.current_state, 0) + 1
        self.retry_counts[self.current_state] = count
        
        scenarios = self.prompts.get("scenarios", {})
        repeat_prompts = scenarios.get("asking_to_repeat", ["Could you please repeat that?"])
        
        if count <= len(repeat_prompts):
            prompt = repeat_prompts[count-1]
        elif count == len(repeat_prompts) + 1:
            prompt = "No problem. Let me simplify: " + self.last_ai_prompt
        else:
            prompt = "I understand. Let's try a different topic. "
            if self.current_state == "GREETING":
                self.current_state = "FAILED"
                prompt = "I'm sorry, I'm unable to proceed at this time. Goodbye."
            else:
                self.current_state = "QUESTIONING"
                prompt += "How many years of total work experience do you have?"

        return {
            "prompt": prompt,
            "state": self.current_state,
            "action": "CONFUSION_RECOVERY"
        }

    def _transition_state(self, user_input: str) -> Dict[str, Any]:
        user_input_lower = user_input.lower()
        next_prompt = ""
          
        # Reset retry/silence counts on successful input
        self.retry_counts[self.current_state] = 0
        self.silence_count = 0

        intents = {
            "affirmative": ["yes", "speaking", "it is", "correct", "sure", "ok", "agree", "consent", "proceed", "yeah", "yup"],
            "negative": ["no", "not really", "stop", "don't", "refuse", "wrong person", "incorrect"],
            "completion": ["done", "finished", "that's it", "nothing else"]
        }

        def has_intent(input_text, intent_list):
            return any(re.search(rf"\b{word}\b", input_text) for word in intent_list)

        if self.current_state == "GREETING":
            if has_intent(user_input_lower, intents["affirmative"]):
                self.current_state = "IDENTITY_VERIFICATION"
                next_prompt = "Great. Can you please confirm your full name for the record?"
            elif has_intent(user_input_lower, intents["negative"]):
                next_prompt = "I'm sorry, I might have the wrong number. Goodbye."
                self.current_state = "FAILED"
            else:
                next_prompt = "I'm calling from Zecpath for a job interview. Am I speaking with the candidate?"

        elif self.current_state == "IDENTITY_VERIFICATION":
            if len(user_input.split()) >= 2:
                self.current_state = "CONSENT"
                next_prompt = "Thank you. This call is recorded for automated screening. Do you consent to proceed?"
            else:
                next_prompt = "Could you please provide your full name as it appears on your application?"

        elif self.current_state == "CONSENT":
            if has_intent(user_input_lower, intents["affirmative"]):
                self.current_state = "QUESTIONING"
                next_prompt = "Perfect. Let's begin. How many years of total work experience do you have?"
            elif has_intent(user_input_lower, intents["negative"]):
                next_prompt = "Understood. We require consent to continue. I will close the call now."
                self.current_state = "FAILED"
            else:
                next_prompt = "To continue, I need your verbal consent to record this call. Do you agree?"

        elif self.current_state == "QUESTIONING":
            answer_quality = FollowUpDetector.evaluate_quality(user_input)
            
            if answer_quality != "good" and self.follow_ups_triggered < 2:
                self.current_state = "FOLLOW_UP"
                next_prompt = FollowUpGenerator.create_prompt(self.last_ai_prompt, answer_quality)
                self.follow_ups_triggered += 1
            else:
                self.current_state = "QUESTIONING"
                self.follow_ups_triggered = 0
                mode = AdaptiveDifficultyManager.determine_level(answer_quality, 1.0)
                next_prompt = AdaptiveQuestionBuilder.build("What are your primary technical skills?", mode)
        
        elif self.current_state == "FOLLOW_UP":
            answer_quality = FollowUpDetector.evaluate_quality(user_input)
            
            if answer_quality != "good" and self.follow_ups_triggered < 2:
                next_prompt = FollowUpGenerator.create_prompt(self.last_ai_prompt, answer_quality)
                self.follow_ups_triggered += 1
            else:
                self.current_state = "QUESTIONING"
                self.follow_ups_triggered = 0
                mode = AdaptiveDifficultyManager.determine_level(answer_quality, 1.0)
                next_prompt = AdaptiveQuestionBuilder.build("What are your primary technical skills?", mode)

        if not next_prompt:
            next_prompt = "Thank you for that information. Let's move on to the next section."

        self.last_ai_prompt = next_prompt
        return {
            "prompt": next_prompt,
            "state": self.current_state,
            "action": "TRANSITION"
        }

    def _trigger_followup(self, user_input: str) -> bool:
        # Legacy stub - logic now handled inline using AdaptiveQuestioningFramework
        return False

    def _get_followup_question(self, user_input: str) -> str:
        # Legacy stub - logic now handled inline using AdaptiveQuestioningFramework
        return ""

if __name__ == "__main__":
    # Robust Test Simulation
    engine = CallFlowEngine("c:/Users/Rahul Rajeev/OneDrive/Desktop/Project Zecpath/interview_ai/call_flow_system")
    print("AI:", engine.start_call())
    
    test_cases = [
        ("Yes, this is Rahul.", 1.0, 0),            # Normal
        ("Rahul Rajeev", 1.0, 0),                 # Normal
        ("Yes han, I consent.", 1.0, 0),           # Language Mixing (Hinglish)
        ("[noise] [inaudible] [static]", 0.3, 0),  # Background Noise
        ("", 1.0, 5),                              # Silence (5s)
        ("I prefer not to say.", 1.0, 0),          # Evasive Answer
        ("5 years.", 1.0, 0),                       # Ambiguous (triggers follow-up clarification)
        ("I worked at Google.", 1.0, 0),            # Ambiguous (triggers clarification 2)
        ("I led a team of 10 engineers where we architected a scalable distributed backend using microservices, optimized the database queries, and successfully deployed it to production reducing latency by 40%.", 1.0, 0), # Confident (scenario)
        ("I built the frontend with React and Redux.", 1.0, 0), # Simple (deepening)
    ]
    
    for turn, conf, silence in test_cases:
        print(f"\nCandidate: '{turn}' (Conf: {conf}, Silence: {silence}s)")
        res = engine.process_turn(turn, stt_confidence=conf, silence_sec=silence)
        print(f"AI Action: {res.get('action')} | Prompt: {res['prompt']} (State: {res['state']})")
