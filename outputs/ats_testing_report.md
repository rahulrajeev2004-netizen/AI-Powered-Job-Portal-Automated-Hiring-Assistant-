

**Date:** 2026-04-10  
**Audit Specialist:** Lead Professional Auditor  

---

## 1. Evaluation Context
- **Evaluation Pool:** 10 diverse Job Descriptions (JDs) representing full system variability (Nursing, Education, Management, Technical).
- **Methodology:** Comparative analysis between Automated ATS Output and Manual Expert Ground Truth Rankings.
- **Primary Objective:** To validate the engine's accuracy and adaptability in **Relevant Candidate Retrieval**, **Seniority-Based Ranking**, and **Irrelevant Candidate Filtering (Rejection)**.

---

## 2. Metric Definitions & Audit Standards
| Metric | Definition |
| :--- | :--- |
| **Precision @ K=2** | Reliability of identifying correct candidates within the top match bracket. |
| **Recall @ K=2** | Ability to capture 100% of high-quality relevant candidates from the pool. |
| **Exact Match Accuracy** | Proportion of roles where ATS ranks perfectly match expert ground truth. |
| **Spearman Rank Correlation (ρ)** | Statistical measure of rank-order consistency across the entire candidate pool. |
| **Rejection Accuracy** | Effectiveness of assigning "Rejected" status to out-of-domain applicants. |

---

## 3. Validated Accuracy Metrics
| Metric | Value | Audit Interpretation |
| :--- | :--- | :--- |
| **Precision @ K=2** | 1.00 | **Success:** Correct candidate identification within the top bracket. |
| **Recall @ K=2** | 1.00 | **Success:** No relevant candidates missed or suppressed. |
| **Exact Match Accuracy** | 0.00 | **Failure:** Total mismatch in internal position rankings. |
| **Spearman Rank Correlation (ρ)** | 0.60 | **Moderate:** General pool identification is correct, but order is inconsistent. |
| **Rejection Accuracy** | 0.00 | **Critical Failure:** 0% of irrelevant candidates correctly rejected. |

> [!IMPORTANT]  
> High Precision and Recall (1.00) indicate successful **retrieval success** (finding the right pool), but do NOT indicate **ranking correctness** (internal ordering).

### Failure Rate Summary:
- **Ranking Failure Rate:** 100% (Exact Match Accuracy = 0.00)
- **Filtering Failure Rate:** 100% (Rejection Accuracy = 0.00)
- **Purpose:** Quick diagnostic snapshot for stakeholders.

---

## 4. Manual Ranking Table (Ground Truth vs. ATS Output)
| Category | Expected Outcome (Rank 1) | Actual ATS Behavior (Rank 1) | Match? | Audit Finding |
| :--- | :--- | :--- | :--- | :--- |
| **Specialized Nursing** | Anita Mathew (Senior) | nurse_resume (Junior) | **No** | **Rank Inversion:** Prioritized cert keywords over specialized tenure. |
| **General Nursing** | nurse_resume | nurse_resume | **Yes** | Alignment on entry-to-mid level staff profiles. |
| **Healthcare Mgmt** | Anita Mathew | Anita Mathew | **Yes** | Proper seniority detection, but score remains suboptimal. |
| **Cross-Domain** | **Disqualified** | **Assigned Weak Match** | **No** | **Filtering Failure:** Irrelevant profiles received numerical ranks. |

---

## 5. Engineering Error Analysis (Observation → Cause → Impact)

### Issue A: Seniority Rank Inversion
- **Observation:** Expert Rank 1 candidates consistently fall to ATS Rank 2 or 3 in specialized roles.
- **Cause:** **Certification Over-weighting**. Binary matches for certifications (ACLS/BLS) out-weight specialized experience tenure.
- **Impact:** System defaults to recommending "Generic Safe Hires" over "Expert Specialists."

### Issue B: Demographic/Tenure Penalty
- **Observation:** Senior candidates (5-10 yrs) receive an experience score of **< 0.5**.
- **Cause:** **Penalty Coupling**. The engine reduces tenure scores if the semantic keyword match is low.
- **Impact:** Experienced professionals using narrative or mature terminology are "double-penalized."

### Issue C: Domain Filtering Failure
- **Observation:** Irrelevant Candidates rank higher for Nursing than some irrelevant senior candidates.
- **Cause:** **Soft-Skill Inflation**. Global attributes (Teamwork) inflate match scores of unqualified candidates.
- **Impact:** Failed automated rejection; high noise floor in the shortlisting pipeline.

### Issue D: Candidate Dominance Bias
- **Observation:** A single candidate appears as Rank 1 in ~70% of relevant roles.
- **Cause:** Weak differentiation logic and over-reliance on common certifications.
- **Impact:** Reduced ranking diversity and biased recommendations toward "generic safe candidates."

---

## 6. Implementation Roadmap (Improvement Backlog)

| Issue ID | Fix Strategy & Technical Logic | Metric Impact | Expected Outcome | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **SYS-001** | **Tenure Multiplier:** Apply `Tenure Boost = years × domain_bonus`. | Spearman ρ & Exact Match | Spearman ρ: 0.60 → **~0.85+** | **High** |
| **SYS-002** | **Industry Gatekeeper:** Reject if `core_skill_match < 15%`. | Rejection Accuracy | Accuracy: 0.00 → **>0.80** | **High** |
| **SYS-003** | **Decoupling:** Remove keyword multiplier from experience score. | Exact Match Accuracy | Exact Match: 0.00 → **~0.60+** | **High** |
| **SYS-004** | **Re-Weighting:** Reduce certification weight; increase domain-skill weight. | Spearman ρ | Reduces dominance bias, improves rank distribution fairness, and increases role-specific ranking accuracy | **Med** |
| **SYS-005** | **Soft-Skill Scaling:** Zero soft-skill values if hard match < 10%. | Rejection Accuracy | Reduces false positives and improves filtering accuracy | **Med** |

---

## 7. Expected System Improvement Summary

Implementing the prioritized roadmap above will result in the following performance shifts:
- **Ranking Intelligence:** **Spearman ρ** projected move from **0.60 to 0.85+**.
- **Ranking Fidelity:** **Exact Match Accuracy** projected move from **0.00 to ~0.60+**.
- **Filtering Capability:** **Rejection Accuracy** projected move from **0.00 to >0.80**.

---

### Operational Impact:
- Recruiters must manually re-rank top candidates due to ranking inconsistency.
- Increased screening time due to presence of irrelevant candidates who should have been auto-rejected.
- High risk of incorrect hiring decisions for senior and specialized roles if ranking output is trusted blindly.

---

## 8. Final System Audit Evaluation

| Category | Score / 10 | Conclusion |
| :--- | :--- | :--- |
| **Retrieval Success** | 9.0 | High efficiency in finding the right pool. |
| **Ranking Accuracy** | 3.0 | Failure in seniority-based differentiation. |
| **Filtering Capability** | 1.0 | Failure in automated disqualification. |

### Final Overall Audit Score: **4.3 / 10**
> **Executive Summary:** The engine is functionally successful as a **Retrieval Pipeline** but fails as a **Ranking System.** Immediate recalibration of tenure logic and rejection thresholds is required for production readiness.
