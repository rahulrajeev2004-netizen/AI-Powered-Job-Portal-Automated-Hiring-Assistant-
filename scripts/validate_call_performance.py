import os
import sys
import json
import time
from datetime import datetime

# Add project root to sys.path to resolve module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from interview_ai.call_flow_engine import CallFlowEngine

def run_validation_suite():
    config_path = "c:/Users/Rahul Rajeev/OneDrive/Desktop/Project Zecpath/interview_ai/call_flow_system"
    engine = CallFlowEngine(config_path)
    
    test_cases = [
        {
            "name": "Standard Happy Path",
            "turns": [
                {"input": "Yes, speaking", "expected_state": "IDENTITY_VERIFICATION"},
                {"input": "Rahul Rajeev", "expected_state": "CONSENT"},
                {"input": "I agree to the recording", "expected_state": "QUESTIONING"},
                {"input": "I have 5 years of experience as a software engineer", "expected_state": "QUESTIONING"}
            ]
        },
        {
            "name": "Vague Answer Trigger (Follow-up)",
            "turns": [
                {"input": "Yes", "expected_state": "IDENTITY_VERIFICATION"},
                {"input": "Rahul Rajeev", "expected_state": "CONSENT"},
                {"input": "Sure", "expected_state": "QUESTIONING"},
                {"input": "5 years", "expected_state": "FOLLOW_UP"} # Should trigger follow-up because it's too short
            ]
        },
        {
            "name": "Confusion & Recovery",
            "turns": [
                {"input": "Yes", "expected_state": "IDENTITY_VERIFICATION"},
                {"input": "What did you say?", "expected_state": "IDENTITY_VERIFICATION", "expected_action": "CONFUSION_RECOVERY"},
                {"input": "My name is Rahul", "expected_state": "CONSENT"}
            ]
        },
        {
            "name": "Silence Handling",
            "turns": [
                {"input": "Yes", "expected_state": "IDENTITY_VERIFICATION"},
                {"input": "", "silence": 7, "expected_state": "IDENTITY_VERIFICATION", "expected_action": "REPROMPT"},
                {"input": "Rahul Rajeev", "expected_state": "CONSENT"}
            ]
        },
        {
            "name": "Negative Intent (Termination)",
            "turns": [
                {"input": "No, wrong person", "expected_state": "FAILED"}
            ]
        },
        {
            "name": "Ambiguity Keyword Trigger",
            "turns": [
                {"input": "Yes", "expected_state": "IDENTITY_VERIFICATION"},
                {"input": "Rahul Rajeev", "expected_state": "CONSENT"},
                {"input": "Yes", "expected_state": "QUESTIONING"},
                {"input": "Roughly 4 years", "expected_state": "FOLLOW_UP"} # 'Roughly' is an ambiguity keyword
            ]
        }
    ]

    results = []
    total_checks = 0
    passed_checks = 0

    print(f"--- Starting Validation Suite at {datetime.now()} ---")

    for case in test_cases:
        print(f"\nRunning Case: {case['name']}")
        # Re-init engine for each case
        engine = CallFlowEngine(config_path)
        engine.start_call()
        
        case_results = []
        for turn in case["turns"]:
            total_checks += 1
            user_input = turn["input"]
            silence = turn.get("silence", 0)
            
            res = engine.process_turn(user_input, silence_sec=silence)
            
            state_match = res["state"] == turn["expected_state"]
            action_match = True
            if "expected_action" in turn:
                action_match = res["action"] == turn["expected_action"]
                total_checks += 1 # Add another check for action
            
            success = state_match and action_match
            if success:
                passed_checks += (2 if "expected_action" in turn else 1)
            
            case_results.append({
                "input": user_input,
                "actual_state": res["state"],
                "expected_state": turn["expected_state"],
                "actual_action": res["action"],
                "expected_action": turn.get("expected_action", "N/A"),
                "passed": success
            })
            
            print(f"  Input: '{user_input}' -> State: {res['state']} (Expected: {turn['expected_state']}) [{'PASS' if success else 'FAIL'}]")

        results.append({
            "case_name": case["name"],
            "turns": case_results,
            "overall_passed": all(t["passed"] for t in case_results)
        })

    accuracy = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    # Generate Report
    report_filename = f"outputs/screening_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    os.makedirs("outputs", exist_ok=True)
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("# Screening System Performance Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Overall Accuracy:** {accuracy:.2f}%\n")
        f.write(f"**Total Checks:** {total_checks}\n")
        f.write(f"**Passed Checks:** {passed_checks}\n\n")
        
        f.write("## Detailed Test Results\n\n")
        for res in results:
            status = "✅ PASS" if res["overall_passed"] else "❌ FAIL"
            f.write(f"### {res['case_name']} ({status})\n")
            f.write("| Input | Actual State | Expected State | Action | Status |\n")
            f.write("|-------|--------------|----------------|--------|--------|\n")
            for turn in res["turns"]:
                status_emoji = "✅" if turn["passed"] else "❌"
                f.write(f"| {turn['input'] or '(Silence)'} | {turn['actual_state']} | {turn['expected_state']} | {turn['actual_action']} | {status_emoji} |\n")
            f.write("\n")
            
        f.write("## Improvements Implemented\n")
        f.write("- **Enhanced Intent Detection:** Added support for affirmative/negative intent mapping beyond simple keywords.\n")
        f.write("- **Ambiguity Handling:** Implemented 'roughly/about' keyword detection to trigger follow-up questions.\n")
        f.write("- **False Rejection Mitigation:** Added a recovery path where the AI moves to the next topic instead of failing after repeated confusion.\n")
        f.write("- **Config-Driven Thresholds:** Moved silence and confidence thresholds to JSON for easier tuning.\n")
        
    print(f"\n--- Validation Completed ---")
    print(f"Overall Accuracy: {accuracy:.2f}%")
    print(f"Report saved to: {report_filename}")

if __name__ == "__main__":
    run_validation_suite()
