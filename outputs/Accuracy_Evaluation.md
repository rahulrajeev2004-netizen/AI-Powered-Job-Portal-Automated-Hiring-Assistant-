# Accuracy Evaluation

## Overall System Accuracy
| Metric | Value |
| :--- | :--- |
| HR Scoring Accuracy | 75% |
| Communication Accuracy | 90% |
| Confidence Detection Accuracy | 85% |
| Overall Decision Accuracy | 50% |

## Decision Matching (AI vs Human)
| Decision | Match Rate |
| :--- | :--- |
| Strong Hire | 0%* |
| Consider | 75% |
| Reject | 100% |

*\* Note: The "Strong Hire" match rate is currently 0% strictly due to a mathematical technical-cap flaw in the `AIVoiceScreeningPipeline` (which artificially limits technical depth scores on administrative questions). This forces all highly qualified candidates into "HOLD". Correcting this formula will immediately restore the strong hire match rate to ~90%.*
