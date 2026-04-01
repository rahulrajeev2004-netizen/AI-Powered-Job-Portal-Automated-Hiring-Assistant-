import numpy as np

class Evaluator:
    def __init__(self, thresholds=None):
        """
        Dynamic thresholds for semantic evaluation.
        """
        # Updated thresholds for Day 12 (aligned with semantic scoring)
        self.thresholds = thresholds or [0.4, 0.5, 0.6, 0.7, 0.8]

    # =====================================
    # CORE METRIC COMPUTATION
    # =====================================
    def compute_metrics(self, data, threshold):
        tp = fp = fn = tn = 0

        for item in data:
            score = item.get("score", 0.0)
            actual = item.get("actual", 0)

            predicted = 1 if score >= threshold else 0

            if predicted == 1 and actual == 1:
                tp += 1
            elif predicted == 1 and actual == 0:
                fp += 1
            elif predicted == 0 and actual == 1:
                fn += 1
            else:
                tn += 1

        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "threshold": threshold
        }

    # =====================================
    # THRESHOLD OPTIMIZATION
    # =====================================
    def evaluate_thresholds(self, data):
        results = []

        for t in self.thresholds:
            metrics = self.compute_metrics(data, t)
            results.append(metrics)

        best = max(results, key=lambda x: x["f1"])

        return {
            "all_results": results,
            "best_threshold_metrics": best
        }

    # =====================================
    # SCORE DISTRIBUTION ANALYSIS (NEW)
    # =====================================
    def analyze_score_distribution(self, data):
        scores = [item.get("score", 0.0) for item in data]

        if not scores:
            return {}

        return {
            "min_score": round(min(scores), 4),
            "max_score": round(max(scores), 4),
            "avg_score": round(np.mean(scores), 4),
            "std_dev": round(np.std(scores), 4)
        }

    # =====================================
    # MATCH LEVEL CLASSIFICATION (NEW)
    # =====================================
    def classify_match(self, score):
        if score >= 0.7:
            return "Strong Match"
        elif score >= 0.5:
            return "Moderate Match"
        else:
            return "Weak Match"

    # =====================================
    # MATCH DISTRIBUTION (NEW)
    # =====================================
    def match_distribution(self, data):
        distribution = {
            "Strong Match": 0,
            "Moderate Match": 0,
            "Weak Match": 0
        }

        for item in data:
            score = item.get("score", 0.0)
            label = self.classify_match(score)
            distribution[label] += 1

        return distribution

    # =====================================
    # DEBUG ANALYSIS (CRITICAL FOR DAY 12)
    # =====================================
    def debug_analysis(self, data):
        print("\n[DEBUG] Score Analysis:")

        scores = [item.get("score", 0.0) for item in data]

        print("Scores:", scores)
        print("Min:", min(scores) if scores else 0)
        print("Max:", max(scores) if scores else 0)
        print("Avg:", np.mean(scores) if scores else 0)
        print("Std Dev:", np.std(scores) if scores else 0)

        # Detect flat score issue
        if scores and (max(scores) - min(scores) < 0.05):
            print("⚠️ WARNING: Scores are too close → Semantic issue likely!")

    # =====================================
    # FINAL REPORT (ENHANCED)
    # =====================================
    def generate_report(self, data):
        evaluation = self.evaluate_thresholds(data)
        best = evaluation["best_threshold_metrics"]

        distribution = self.match_distribution(data)
        stats = self.analyze_score_distribution(data)

        self.debug_analysis(data)  # 🔥 important

        report = (
            "=== Evaluation Report ===\n\n"
            f"Precision: {best['precision']}\n"
            f"Recall: {best['recall']}\n"
            f"F1 Score: {best['f1']}\n"
            f"Best Threshold: {best['threshold']}\n\n"
            "=== Score Distribution ===\n"
            f"Min: {stats.get('min_score')}\n"
            f"Max: {stats.get('max_score')}\n"
            f"Avg: {stats.get('avg_score')}\n"
            f"Std Dev: {stats.get('std_dev')}\n\n"
            "=== Match Distribution ===\n"
            f"Strong: {distribution['Strong Match']}\n"
            f"Moderate: {distribution['Moderate Match']}\n"
            f"Weak: {distribution['Weak Match']}\n"
        )

        return report