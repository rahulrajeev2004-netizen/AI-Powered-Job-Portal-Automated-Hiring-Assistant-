from interview_ai.call_flow_engine import CallFlowEngine
import time

def run_simulation():
    config_path = "c:/Users/Rahul Rajeev/OneDrive/Desktop/Project Zecpath/interview_ai/call_flow_system"
    engine = CallFlowEngine(config_path)

    print("=== STARTING AI CALL FLOW DEMO ===")
    print(f"AI: {engine.start_call()}\n")

    # Scenario 1: Standard Consent
    print("--- Scenario: Standard Greeting & Consent ---")
    response = engine.process_turn("Yes, speaking.")
    print(f"Cand: Yes, speaking.")
    print(f"AI: {response['prompt']}\n")

    response = engine.process_turn("Rahul Rajeev")
    print(f"Cand: Rahul Rajeev")
    print(f"AI: {response['prompt']}\n")

    response = engine.process_turn("I agree to the recording.")
    print(f"Cand: I agree to the recording.")
    print(f"AI: {response['prompt']}\n")

    # Scenario 2: Follow-up Trigger (Vague Experience)
    print("--- Scenario: Follow-up Trigger (Vague Answer) ---")
    response = engine.process_turn("5 years.")
    print(f"Cand: 5 years.")
    print(f"AI: {response['prompt']} (ACTION: {response['action']})\n")

    # Scenario 3: Confusion Handling
    print("--- Scenario: Confusion Recovery ---")
    response = engine.process_turn("What? I don't get the question.")
    print(f"Cand: What? I don't get the question.")
    print(f"AI: {response['prompt']} (ACTION: {response['action']})\n")

    # Scenario 4: Silence Handling
    print("--- Scenario: Silence Recovery (6s pause) ---")
    response = engine.process_turn("", silence_sec=6.0)
    print(f"Cand: (Silence 6s)")
    print(f"AI: {response['prompt']} (ACTION: {response['action']})\n")

    # Scenario 5: Repeated Silence -> Callback
    print("--- Scenario: Repeated Silence -> Callback Request ---")
    response = engine.process_turn("", silence_sec=10.0)
    print(f"Cand: (Silence 10s)")
    print(f"AI: {response['prompt']} (ACTION: {response['action']})\n")

    # Final Evaluation
    print("--- Final Output: Evaluation Report ---")
    evaluation = engine.generate_evaluation()
    
    # Save to file
    import json
    import os
    output_path = "outputs/last_call_evaluation.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(evaluation, indent=2, fp=f)
    
    print(json.dumps(evaluation, indent=2))
    print(f"\n[SUCCESS] Final evaluation report saved to: {output_path}")

    print("\n=== DEMO COMPLETED ===")

if __name__ == "__main__":
    run_simulation()
