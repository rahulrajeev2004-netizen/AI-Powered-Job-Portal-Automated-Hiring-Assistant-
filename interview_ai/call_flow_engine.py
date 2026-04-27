import json
import os
from typing import Dict, Any, List, Optional

class CallFlowEngine:
    """
    Production-grade AI Call Flow Engine for dynamic voice interactions.
    Handles State Machine transitions, Silence/Confusion recovery, and Follow-up triggers.
    """

    def __init__(self, config_dir: str, language: str = "en"):
        self.config_dir = config_dir
        self.language = language
        
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
                "callback_request": ["Should I call you back?"]
            }
        })
        
        # Session State
        self.current_state = "INIT"
        self.retry_counts = {}  # state_id -> count
        self.silence_count = 0
        self.session_data = {}
        self.last_ai_prompt = ""
        self.interaction_history = []

    def _load_json(self, filename: str, default: Dict[str, Any]) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if not os.path.exists(path):
            return default
        try:
            with open(path, 'r') as f:
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
            "session_id": "SES-" + str(hash(str(self.interaction_history)) % 10000),
            "timestamp": "2026-04-27T14:40:00Z",
            "final_state": self.current_state,
            "interaction_summary": {
                "total_turns": len(self.interaction_history),
                "completion_status": "SUCCESS" if self.current_state in ["COMPLETED", "QUESTIONING"] else "PARTIAL"
            },
            "compliance": {
                "consent_obtained": any("consent" in str(h).lower() for h in self.interaction_history)
            },
            "raw_log": self.interaction_history
        }

    def process_turn(self, user_input: str, stt_confidence: float = 1.0, silence_sec: float = 0) -> Dict[str, Any]:
        """
        Processes a single turn with multi-language support and tracking.
        """
        self.interaction_history.append({"user": user_input, "state": self.current_state})
        
        # 1. Handle Silence Logic
        if silence_sec > 2:
            res = self._handle_silence(silence_sec)
            self.interaction_history.append({"ai": res["prompt"], "state": res["state"]})
            return res

        # 2. Handle Confusion Logic
        if self._is_confused(user_input, stt_confidence):
            res = self._handle_confusion(user_input)
            self.interaction_history.append({"ai": res["prompt"], "state": res["state"]})
            return res

        # 3. State Transitions & Answer Processing
        res = self._transition_state(user_input)
        self.interaction_history.append({"ai": res["prompt"], "state": res["state"]})
        return res

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

    def _is_confused(self, user_input: str, confidence: float) -> bool:
        confusion_triggers = ["what", "repeat", "understand", "pardon", "again", "clear", "not sure"]
        if confidence < self.decision_rules.get("error_logic", {}).get("asr_low_confidence", {}).get("threshold", 0.45):
            return True
        return any(trigger in user_input.lower() for trigger in confusion_triggers)

    def _handle_confusion(self, user_input: str) -> Dict[str, Any]:
        count = self.retry_counts.get(self.current_state, 0) + 1
        self.retry_counts[self.current_state] = count
        
        if count == 1:
            prompt = self.prompts["scenarios"]["asking_to_repeat"][0]
        elif count == 2:
            prompt = "No problem. Let me simplify: " + self.last_ai_prompt
        else:
            prompt = "I understand. Let's move to the next topic to keep things moving."
            # Logic to move to next state
            self.current_state = "QUESTIONING"

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

        if self.current_state == "GREETING":
            if any(word in user_input_lower for word in ["yes", "speaking", "it is", "correct"]):
                self.current_state = "IDENTITY_VERIFICATION"
                next_prompt = "Great. Can you please confirm your full name for the record?"
            else:
                next_prompt = "I'm sorry, I might have the wrong number. Goodbye."
                self.current_state = "FAILED"

        elif self.current_state == "IDENTITY_VERIFICATION":
            self.current_state = "CONSENT"
            next_prompt = "Thank you. This call is recorded for automated screening. Do you consent to proceed?"

        elif self.current_state == "CONSENT":
            if any(word in user_input_lower for word in ["yes", "agree", "consent", "proceed", "sure", "ok"]):
                self.current_state = "QUESTIONING"
                next_prompt = "Perfect. Let's begin. How many years of total work experience do you have?"
            else:
                next_prompt = "Understood. We require consent to continue. I will close the call now."
                self.current_state = "FAILED"

        elif self.current_state == "QUESTIONING":
            if self._trigger_followup(user_input):
                self.current_state = "FOLLOW_UP"
                next_prompt = self._get_followup_question(user_input)
            else:
                next_prompt = "Got it. And what are your primary technical skills?"
        
        elif self.current_state == "FOLLOW_UP":
            self.current_state = "QUESTIONING"
            next_prompt = "Excellent. Now, tell me about your primary technical skills."

        if not next_prompt:
            next_prompt = "Thank you for that information. Let's move on."

        self.last_ai_prompt = next_prompt
        return {
            "prompt": next_prompt,
            "state": self.current_state,
            "action": "TRANSITION"
        }

    def _trigger_followup(self, user_input: str) -> bool:
        # Vague experience trigger
        num_matches = [s for s in user_input.split() if s.isdigit()]
        if num_matches and len(user_input.split()) < 5:
            return True
        return False

    def _get_followup_question(self, user_input: str) -> str:
        return "In which specific technologies or domains did you work during this time?"

if __name__ == "__main__":
    # Simple Local Simulation
    engine = CallFlowEngine("c:/Users/Rahul Rajeev/OneDrive/Desktop/Project Zecpath/interview_ai/call_flow_system")
    print("AI:", engine.start_call())
    
    # Simulating a conversation
    turns = [
        "Yes, this is Rahul.",
        "Rahul Rajeev.",
        "Yes, I consent.",
        "5 years." # Should trigger follow-up
    ]
    
    for turn in turns:
        print(f"Candidate: {turn}")
        res = engine.process_turn(turn)
        print(f"AI: {res['prompt']} (State: {res['state']})")
