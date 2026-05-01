import json
import random
import os
from typing import List, Dict, Any

class QuestionGenerator:
    """
    Dynamic Role-Based Question Generator for Zecpath AI Interview System.
    Pulls questions from the central question bank architecture based on candidate
    experience and role type.
    """
    def __init__(self, bank_path: str = "outputs/question_bank_architecture.json"):
        # Resolve the absolute path to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.bank_path = os.path.join(project_root, bank_path)
        self.question_bank = self._load_question_bank()

    def _load_question_bank(self) -> Dict[str, Any]:
        """Loads the JSON architecture file."""
        try:
            with open(self.bank_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading question bank at {self.bank_path}: {e}")
            return {"question_bank": {"categories": []}}

    def generate_questions(self, role_type: str, experience_level: str) -> List[Dict[str, Any]]:
        """
        Generates a tailored queue of questions based on role (Technical/Non-technical)
        and experience level (Fresher/Experienced).
        """
        qb = self.question_bank.get("question_bank", {}).get("categories", [])
        if not qb:
            return []

        selected_questions = []

        # Iterate through categories to find applicable questions
        for category in qb:
            questions = category.get("questions", [])
            valid_questions = []
            
            for q in questions:
                target_exp = q.get("target_experience", [])
                target_role = q.get("target_role", [])
                
                # Check if the question matches the candidate's profile
                if experience_level in target_exp and role_type in target_role:
                    valid_questions.append(q)
            
            if valid_questions:
                # Pick 1 random question per category to ensure a balanced, dynamic interview
                selected = random.choice(valid_questions)
                selected_copy = selected.copy()
                selected_copy["category_name"] = category.get("name")
                selected_questions.append(selected_copy)

        # Structure the interview flow:
        # 1. Introduction always comes first
        # 2. Availability / Goals come last
        # 3. Core behavioral and technical questions are randomized in the middle
        
        intro_q = [q for q in selected_questions if "intro" in q["id"].lower()]
        closing_q = [q for q in selected_questions if "avail" in q["id"].lower() or "goals" in q["id"].lower()]
        middle_q = [q for q in selected_questions if q not in intro_q and q not in closing_q]
        
        random.shuffle(middle_q)
        
        final_queue = intro_q + middle_q + closing_q
        
        # Format the output for the CallFlowEngine
        output_queue = []
        for q in final_queue:
            output_queue.append({
                "question_id": q["id"],
                "text": q["text"],
                "category": q["category_name"],
                "requires_follow_up": q.get("requires_follow_up", False)
            })

        return output_queue

if __name__ == "__main__":
    generator = QuestionGenerator()
    
    print("--- Scenario 1: Fresher / Technical ---")
    fresher_tech = generator.generate_questions("Technical", "Fresher")
    print(json.dumps(fresher_tech, indent=2))
    
    print("\n--- Scenario 2: Experienced / Non-technical ---")
    exp_nontech = generator.generate_questions("Non-technical", "Experienced")
    print(json.dumps(exp_nontech, indent=2))
