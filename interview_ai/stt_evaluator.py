import re
from typing import List, Dict

class STTEvaluator:
    """
    Module for measuring Speech-to-Text accuracy.
    Calculates Word Error Rate (WER) and provides accent-based performance benchmarking.
    """
    
    @staticmethod
    def calculate_wer(reference: str, hypothesis: str) -> float:
        """
        Calculate Word Error Rate (WER).
        WER = (S + D + I) / N
        """
        def clean(t): return re.sub(r'[^\w\s]', '', t.lower()).split()
        
        ref = clean(reference)
        hyp = clean(hypothesis)
        
        n = len(ref)
        if n == 0: return 1.0 if len(hyp) > 0 else 0.0
        
        # Levenshtein distance for words
        d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
        for i in range(len(ref) + 1): d[i][0] = i
        for j in range(len(hyp) + 1): d[0][j] = j
        
        for i in range(1, len(ref) + 1):
            for j in range(1, len(hyp) + 1):
                if ref[i-1] == hyp[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion    = d[i][j-1] + 1
                    deletion     = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
                    
        return round(d[len(ref)][len(hyp)] / n, 4)

    def generate_report(self, test_results: List[Dict[str, Any]]) -> str:
        """
        Generates a Markdown report summarizing STT performance across conditions.
        """
        avg_wer = sum(r['wer'] for r in test_results) / len(test_results)
        
        report = [
            "# STT Accuracy & Robustness Report",
            f"\n**Overall Average WER:** {avg_wer:.2%}",
            "\n## Test Results By Condition",
            "| Condition | Accent | Noise Level | Avg WER | Accuracy (1-WER) |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        
        # Group by condition
        conditions = {}
        for r in test_results:
            c = r['condition']
            if c not in conditions: conditions[c] = []
            conditions[c].append(r['wer'])
            
        for cond, wers in conditions.items():
            avg = sum(wers) / len(wers)
            accent = cond.split('_')[0].title()
            noise = cond.split('_')[1] if len(cond.split('_')) > 1 else "Clean"
            report.append(f"| {cond} | {accent} | {noise} | {avg:.2%} | {1-avg:.2%} |")
            
        return "\n".join(report)

if __name__ == "__main__":
    evaluator = STTEvaluator()
    # Mock data for accent/noise testing
    mock_data = [
        {"condition": "indian_low_noise", "wer": 0.051},
        {"condition": "indian_high_noise", "wer": 0.182},
        {"condition": "us_low_noise", "wer": 0.023},
        {"condition": "uk_low_noise", "wer": 0.035},
        {"condition": "singaporean_low_noise", "wer": 0.081}
    ]
    print(evaluator.generate_report(mock_data))
