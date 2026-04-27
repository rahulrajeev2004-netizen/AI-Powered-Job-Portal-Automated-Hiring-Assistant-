import json
import os
import time

class ProductionFlowEngine:
    """
    Executes the AI call flow logic directly from the consolidated production JSON.
    Supports state machine, tiered retry logic, and dynamic follow-ups.
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.current_state = self.config["call_flow_logic"]["entry"]
        self.history = []
        self.retry_count = 0
        self.current_q_index = 0
        self.questions = self.config["question_engine"]["questions"]
        self.is_active = True

    def get_prompt(self) -> str:
        if self.current_state == "GREETING":
            return "Hello! I'm your AI interviewer. Do you have a moment to talk?"
        
        if self.current_state == "ASKING_QUESTION":
            q = self.questions[self.current_q_index]
            # Select version based on retry count
            if self.retry_count == 0: return q["primary"]
            if self.retry_count == 1: return q["fallback_simpler"]
            if self.retry_count == 2: return q["fallback_example"]
            return q["retry_final"]
        
        return "Thank you for your time. Goodbye!"

    def process_input(self, user_input: str, silence_sec: float = 0) -> str:
        if not self.is_active: return "Call ended."
        
        # Log the interaction
        current_prompt = self.get_prompt()

        # 1. Handle Silence Logic
        if silence_sec > 0:
            for tier in self.config["error_handling"]["silence_tiers"]:
                if silence_sec >= tier["threshold"]:
                    self.retry_count += 1
                    resp = tier["prompt"]
                    self.history.append({"ai": resp, "user": "[SILENCE]", "state": self.current_state})
                    return resp

        user_input_lower = user_input.lower()

        # 2. Handle Follow-up Triggers
        for rule in self.config["followup_rules"]:
            if rule["trigger_keyword"] in user_input_lower:
                resp = rule["question"]
                self.history.append({"ai": resp, "user": user_input, "state": "FOLLOW_UP"})
                return resp

        # 3. State Transitions & History Capture
        if self.current_state == "GREETING":
            if any(w in user_input_lower for w in ["yes", "sure", "ok"]):
                self.current_state = "ASKING_QUESTION"
                self.retry_count = 0
                resp = self.get_prompt()
                self.history.append({"ai": resp, "user": user_input, "state": "GREETING"})
                return resp
            else:
                self.is_active = False
                return "Understood. I'll call back later. Goodbye."

        if self.current_state == "ASKING_QUESTION":
            self.history.append({"ai": current_prompt, "user": user_input, "state": "ASKING_QUESTION"})
            self.current_q_index += 1
            self.retry_count = 0
            
            if self.current_q_index >= len(self.questions):
                self.is_active = False
                return "That's all for today. Thank you!"
            
            return self.get_prompt()

        return "Processing..."

def run_production_demo():
    config_file = "outputs/call_flow_logic_production.json"
    engine = ProductionFlowEngine(config_file)
    
    print("--- STARTING PRODUCTION CALL FLOW ---")
    print(f"AI: {engine.get_prompt()}")
    
    # Simulate turn 1
    print("\n[USER SAYS: Yes]")
    print(f"AI: {engine.process_input('Yes')}")
    
    # Simulate turn 2 (Vague answer -> Fallback)
    print("\n[USER SAYS: What? (Triggering silence 8s)]")
    print(f"AI: {engine.process_input('', silence_sec=8)}")
    
    # Simulate turn 3 (Follow-up)
    print("\n[USER SAYS: I know Python]")
    print(f"AI: {engine.process_input('I know Python')}")
    
    print("\n--- SAVING OUTPUT DIRECTLY INTO outputs/call_flow_logic_production.json ---")
    
    with open(config_file, 'r') as f:
        master_config = json.load(f)
    
    master_config["sample_conversation_output"] = {
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "interaction_history": engine.history
    }
    
    with open(config_file, 'w') as f:
        json.dump(master_config, f, indent=2)
    
    print("SUCCESS: Session history has been appended to the production logic file.")

if __name__ == "__main__":
    run_production_demo()
