import json
from interview_ai.cognitive_evaluator import CognitiveEvaluator

def main():
    evaluator = CognitiveEvaluator()
    
    # 1. Design reasoning-based question
    question = evaluator.design_reasoning_question()
    print(f"Generated Question:\n{json.dumps(question, indent=2)}\n")
    
    # Simulate candidate answers
    candidate_answers = [
        {
            "scenario_id": "SIT_1", # deadline_pressure
            "answer_text": "First, I would prioritize the most critical tasks. Then, I'll create a plan to execute the fix quickly. Finally, I will communicate the result to the team."
        },
        {
            "scenario_id": "SIT_2", # team_conflict
            "answer_text": "I'll try to talk to them and understand their views."
        }
    ]
    
    # 2. Evaluate candidate cognition
    result = evaluator.evaluate_candidate_cognition(
        candidate_id="CAND-404",
        answers=candidate_answers
    )
    
    print("Cognitive Evaluation Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
