import json
import os
from scoring.fairness_engine import FairnessEngine

def main():
    input_file = "outputs/ranked_candidates.json"
    output_file = "outputs/fairness_adjusted_ranking.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return
        
    engine = FairnessEngine(threshold=0.7)
    print("Applying fairness adjustments...")
    
    # Process multiple jobs
    fairness_results = engine.process_all(data)
    
    # Save the output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(fairness_results, f, indent=2)
        
    print(f"Successfully processed fairness and saved to {output_file}")


if __name__ == "__main__":
    main()
