

## 🔧 Structured Improvement Table

| Issue ID | Problem | Priority | Fix Strategy & Technical Logic | Metric Impact | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SYS-001** | **Seniority Inversion** | **High** | Implement **Tenure Multiplier**: `Tenure Boost = years × domain_bonus`. (domain_bonus: 0.5 - 1.5 based on role criticality). | **Spearman Rank Correlation (ρ)** | ρ: 0.60 → **~0.85**. Fixes rank-swaps between senior and junior staff. |
| **SYS-002** | **Domain Ghosting** | **High** | Implement **Hard Industry Gatekeeper**: `If (core_skill_match < 15%) then STATUS = 'Disqualified'`. | **Rejection Accuracy** | Accuracy: 0.0 → **>0.90**. Auto-rejects 100% of out-of-domain noise. |
| **SYS-003** | **Penalty Coupling** | **High** | **Decouple Experience Scoring**: Evaluate tenure years as a standalone variable. Remove the $SkillMatch \times Experience$ multiplier. | **Score Calibration** | Precision@2 preserved; reduction in score overlap between senior and weak profiles. |
| **SYS-004** | **Certification Bias** | **Med** | **Weight Redistribution**: Rebalance weights toward specialized skills (SkillSet: 50% | Experience: 30% | Certs: 10% | Edu: 10%). | **Spearman Rank Correlation (ρ)** | Improved ranking diversity; reduces "Cert-jumping" in specialists. |
| **SYS-005** | **Soft-Skill Bleed** | **Med** | **Relative Soft-Skill Scaling**: `Soft_Score = Base_Soft_Score × (Hard_Skill_Match / 0.20)`. If hard match <10%, soft skills count as 0. | **Score Calibration** | Eliminates IT-to-Nursing false positives (Score for irrelevant roles drops to < 0.05). |

---

## 📐 Final Section: Expected System Improvement Summary

Implementing the roadmap above will transform the engine from a "Search Filter" into an "Intelligent Recruiter."

### 1. Ranking Quality (Intelligence)
- **Outcome:** The **Spearman ρ** is projected to climb from **0.60 to 0.85+**. 
- **Impact:** Seniority will be the dominant ranking factor for mid-to-high level roles, correctly reflecting domain hierarchy.

### 2. Filtering Capability (Noise Reduction)
- **Outcome:** **Rejection Accuracy** will move from **0.0 to >0.90**. 
- **Impact:** Irrelevant "Domain Bleed" (e.g., a Data Analyst appearing in a Nursing shortlist) will be eliminated via the 15% core-skill gatekeeper.

### 3. Score Reliability (Precision)
- **Outcome:** The "False Positive" zone of 0.15 — 0.25 will be cleared. 
- **Impact:** Disqualified candidates will drop to near-zero scores, creating a clear gap between "Noise" and "Weak Matches."

### 4. Candidate Diversity (Bias Reduction)
- **Outcome:** Mitigation of **Candidate Dominance Bias**.
- **Impact:** By lowering the weight of generic certifications and increasing the value of specialized experience, the system will optimize for "Best Role Fit" rather than "Best Keyword Match."

---

## 📋 System Evaluation Summary (Current vs. Target)

| Metric | Current State | Post-Fix Target | Status |
| :--- | :--- | :--- | :--- |
| **Candidate Identification** | 9 / 10 | 9 / 10 | Stable |
| **Ranking Accuracy** | 3 / 10 | 8 / 10 | Major Upgrade |
| **Domain Filtering** | 1 / 10 | 9 / 10 | Critical Fix |
| **Overall Score** | **4.3 / 10** | **8.8 / 10** | **Production-Ready** |
