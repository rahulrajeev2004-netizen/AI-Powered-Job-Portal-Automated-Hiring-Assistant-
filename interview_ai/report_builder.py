import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

class RecruiterReportBuilder:
    """
    Enterprise ATS Recruiter Intelligence Engine v8.0 (Balanced Final).
    Production-ready intelligence engine focused on balancing fairness with governance.
    """

    def __init__(self, candidate_id: str):
        self.candidate_id = candidate_id
        self.raw_analysis = {}
        self.evaluation = {}
        self.behavioral = {}
        self.report = {}

    def load_data(self, analysis_path: str, evaluation_path: str, behavioral_path: str):
        """Loads data from the various AI engines."""
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r', encoding='utf-8') as f:
                self.raw_analysis = json.load(f)
        
        if os.path.exists(evaluation_path):
            with open(evaluation_path, 'r', encoding='utf-8') as f:
                self.evaluation = json.load(f)
                
        if os.path.exists(behavioral_path):
            with open(behavioral_path, 'r', encoding='utf-8') as f:
                self.behavioral = json.load(f)

    def _soften_language(self, text: str) -> str:
        """Applies v8.0 Risk Language Policy (Section 7)."""
        mapping = {
            r"unsupported": "requires validation",
            r"weak": "limited detail provided",
            r"poor": "limited detail provided",
            r"suspicious": "requires validation",
            r"high risk detected": "moderate concern",
            r"unacceptable": "further clarification recommended",
            r"critical risk": "moderate concern",
            r"vague": "limited detail provided"
        }
        softened = text
        for pattern, replacement in mapping.items():
            softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)
        return softened

    def _normalize_salary(self) -> Dict[str, Any]:
        """Normalizes salary data according to standard rules."""
        profile = self.raw_analysis.get("global_profile", {}).get("salary", {})
        expected = profile.get("expected", {})
        
        raw_val = expected.get("value", 0)
        currency = expected.get("normalized_currency", expected.get("currency", "INR"))
        raw_input = f"{raw_val} {expected.get('currency', 'INR')}"
        
        period = "monthly"
        annualized = 0
        monthly = 0
        confidence = "Medium"

        if raw_val > 500000:
            period = "annual"
            annualized = raw_val
            monthly = raw_val / 12
        elif raw_val > 0:
            period = "monthly"
            monthly = raw_val
            annualized = raw_val * 12
        else:
            period = "unknown"
            confidence = "Low"

        return {
            "raw_input": raw_input,
            "currency": currency,
            "amount": raw_val,
            "period": period,
            "monthly_value": round(monthly, 2) if monthly else None,
            "annualized_value": round(annualized, 2) if annualized else None,
            "confidence": confidence if raw_val > 0 else "Low"
        }

    def _calculate_scores(self, validated_count: int, contradictions: List[Dict]) -> Dict[str, Any]:
        """Calculates score breakdown according to v8.0 rules (Section 4, 5, 9)."""
        cat_scores = self.evaluation.get("category_scores", {})
        behavioral_metrics = self.behavioral.get("detailed_metrics", {})
        
        # Section 5: Technical Score Rules
        tech = cat_scores.get("Skills", 60)
        if validated_count == 1:
            tech = min(tech, 65.0)
        elif validated_count == 0:
            tech = min(tech, 50.0)
            
        comm = behavioral_metrics.get("communication_strength_index", 0.7) * 100
        exp = cat_scores.get("Experience", 60)
        prob = (cat_scores.get("Skills", 60) + cat_scores.get("Experience", 60)) / 2
        
        # Section 4: Consistency Scoring Rules
        consistency = 80
        for c in contradictions:
            sev = c.get("severity", "Medium")
            if sev == "High": consistency -= 30
            elif sev == "Medium": consistency -= 20
            else: consistency -= 10
        consistency = max(35, consistency)
        
        penalty = -int(self.evaluation.get("penalty_breakdown", {}).get("total_penalty", 0))
        
        # v8.0 Weights: Tech 30%, Comm 15%, Exp 20%, Cons 15%, Prob 20%
        base = (tech * 0.30) + (comm * 0.15) + (exp * 0.20) + (consistency * 0.15) + (prob * 0.20)
        final_score = int(round(max(0, min(100, base + penalty))))

        return {
            "technical_skills": round(tech, 1),
            "communication": round(comm, 1),
            "experience_relevance": round(exp, 1),
            "consistency": round(consistency, 1),
            "problem_solving": round(prob, 1),
            "risk_penalty": penalty,
            "final_score": final_score
        }

    def _get_calibrated_decision(self, score: int, scores: Dict[str, Any], contradictions: List[Dict]) -> Tuple[str, Optional[str], Optional[str], List[str]]:
        """Calibrated decision banding for v8.0 (Section 1 & 2)."""
        reason_codes = []
        override_reason = None
        
        if score >= 90: decision = "Priority Shortlist"
        elif score >= 80: decision = "Strong Shortlist"
        elif score >= 70: decision = "Shortlist"
        elif score >= 65: decision = "Further Evaluation"
        elif score >= 50: decision = "Hold for Review"
        else: decision = "Not Proceeding"

        # Section 2: Upside Protection Rules
        if scores["technical_skills"] >= 60 and scores["communication"] >= 75 and scores["problem_solving"] >= 65 and len(contradictions) <= 1:
            if decision == "Not Proceeding":
                decision = "Hold for Review"
                override_reason = "Candidate shows positive technical and communication indicators. Manual review recommended before rejection."
                reason_codes.append("UPSIDE_PROTECTION")
            
        if len(contradictions) > 0: reason_codes.append("CONTRADICTION_DETECTED")
        if scores["technical_skills"] >= 65: reason_codes.append("TECH_SIGNAL_QUALIFIED")

        # Section 10: Consistency Check mappings
        if decision == "Priority Shortlist": next_step = "Hiring Manager Round"
        elif decision == "Strong Shortlist": next_step = "Hiring Manager Round"
        elif decision == "Shortlist": next_step = "Hiring Manager Round"
        elif decision == "Further Evaluation": next_step = "Technical Interview"
        elif decision == "Hold for Review": next_step = "Clarification + Technical Screening"
        else: next_step = None

        return decision, next_step, override_reason, reason_codes

    def build(self) -> Dict[str, Any]:
        """Builds the v8.0 balanced intelligence report."""
        
        # 1. Contradictions (Needed for scoring)
        raw_conflicts = self.behavioral.get("contradiction_summary", {}).get("detailed_reports", [])
        contradictions = []
        for c in raw_conflicts:
            desc = c.get("desc", "")
            if "linguistic variance" in desc.lower(): continue
            contradictions.append({
                "field": c.get("theme", "other"),
                "claims": [desc],
                "severity": "High" if c.get("severity", 0) > 0.6 else "Medium",
                "resolution": "Needs Clarification"
            })

        # 2. Validated Skills Separation
        q_analysis = self.evaluation.get("question_analysis", [])
        validated_skills = []
        for qa in q_analysis:
            if qa.get("evidence_level") == "high" and qa.get("category") == "Skills":
                skill_name = qa.get("question", "").replace("Explain your ", "").replace("Describe your ", "").title()
                # Filtering Rule: No logistics (Section 6)
                if any(k in skill_name.lower() for k in ["location", "salary", "experience", "notice"]): continue
                
                validated_skills.append({
                    "skill": skill_name,
                    "evidence": qa.get("answer", "")
                })

        # 3. Scoring (Section 4, 5, 9)
        scores = self._calculate_scores(len(validated_skills), contradictions)
        
        # 4. Decision & Overrides
        decision, next_step, override_reason, reason_codes = self._get_calibrated_decision(scores["final_score"], scores, contradictions)
        
        # 5. Risks & Evidence (Section 7)
        raw_risks = self.evaluation.get("candidate_summary", {}).get("top_risks", [])
        risks = []
        for r in raw_risks:
            risks.append({
                "risk": self._soften_language(r),
                "evidence": "Observed during screening response analysis."
            })

        # 6. Final Report Assembly
        salary_data = self._normalize_salary()
        global_profile = self.raw_analysis.get("global_profile", {})
        
        # Executive Summary (Section 11)
        if decision == "Not Proceeding":
            summary = f"Current evidence does not meet advancement criteria based on available information. Final score: {scores['final_score']}."
        elif decision == "Hold for Review":
            summary = f"Candidate shows mixed indicators with credible upside potential. Final score: {scores['final_score']}. Recommendation is Hold for Review pending clarification and targeted technical validation."
        elif decision == "Further Evaluation":
            summary = f"Candidate demonstrates relevant potential with moderate confidence. Final score: {scores['final_score']}. Recommendation is Further Evaluation."
        else:
            summary = f"Candidate demonstrates strong evidence across relevant dimensions. Final score: {scores['final_score']}."

        self.report = {
            "report_metadata": {
                "candidate_id": self.candidate_id,
                "job_role": self.evaluation.get("job_role", "Software Engineer"),
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "engine_version": "v8.0-production-balanced"
            },
            "executive_summary": {
                "hiring_decision": decision,
                "overall_score": scores["final_score"],
                "summary_narrative": summary,
                "recruiter_priority": "High" if "Shortlist" in decision else "Medium"
            },
            "score_breakdown": scores,
            "candidate_profile": {
                "years_experience": global_profile.get("experience", {}).get("total_years"),
                "current_location": global_profile.get("location", {}).get("current"),
                "relocation_interest": global_profile.get("location", {}).get("negotiable"),
                "notice_period": f"{global_profile.get('notice_period', {}).get('days')} days",
                "salary_expectation": f"{global_profile.get('salary', {}).get('expected', {}).get('value')} {global_profile.get('salary', {}).get('expected', {}).get('currency')}",
                "availability": "Notice Period" if global_profile.get("notice_period", {}).get("days", 0) > 0 else "Immediate"
            },
            "hiring_logistics": {
                "salary": salary_data
            },
            "technical_profile": {
                "validated_skills": validated_skills,
                "claimed_skills": [s for s in global_profile.get("skills", {}).get("explicit", []) if not any(v["skill"].lower() in s.lower() for v in validated_skills)],
                "inferred_skills": [s["name"] for s in global_profile.get("skills", {}).get("inferred", [])]
            },
            "risk_assessment": {
                "identified_risks": risks,
                "bias_safety": "Decision grounded in objective scoring dimensions with fairness-focused override rules active."
            },
            "contradictions": contradictions,
            "confidence_metrics": {
                "experience": "Medium" if any(c["field"] == "experience" for c in contradictions) else "High",
                "salary": salary_data["confidence"],
                "location": "High",
                "skills": "High" if len(validated_skills) >= 2 else "Medium",
                "availability": "High"
            },
            "final_recommendation": {
                "action": decision,
                "decision_override_reason": override_reason,
                "next_best_step": next_step,
                "interview_focus": self.evaluation.get("recruiter_recommendation", {}).get("interview_focus_areas", []) if decision != "Not Proceeding" else []
            },
            "audit_log": {
                "decision_reason_codes": reason_codes,
                "model_confidence": "Medium",
                "human_review_recommended": True if (decision == "Hold for Review" or len(contradictions) > 0 or scores["communication"] >= 80) else False
            }
        }
        return self.report

    def generate_markdown(self) -> str:
        """Generates a v8.0 production-ready Markdown report."""
        r = self.report
        s = r["score_breakdown"]
        p = r["candidate_profile"]
        
        md = f"# intelligence Screening Report: {r['report_metadata']['candidate_id']}\n"
        md += f"**Role:** {r['report_metadata']['job_role']} | **Engine:** {r['report_metadata']['engine_version']}\n\n"
        
        md += "## 🎯 Executive Summary\n"
        md += f"- **Hiring Decision:** **{r['executive_summary']['hiring_decision']}**\n"
        md += f"- **Overall Score:** `{s['final_score']}/100`\n"
        md += f"- **Narrative:** {r['executive_summary']['summary_narrative']}\n"
        if r['final_recommendation']['decision_override_reason']:
            md += f"- **Decision Note:** *{r['final_recommendation']['decision_override_reason']}*\n"
        md += f"- **Next Step:** {r['final_recommendation']['next_best_step'] or 'Not Proceeding'}\n\n"

        md += "## 📊 Balanced Score Breakdown\n"
        md += f"| Category | Score | Weight |\n"
        md += f"| :--- | :--- | :--- |\n"
        md += f"| Technical Skills | {s['technical_skills']} | 30% |\n"
        md += f"| Problem Solving | {s['problem_solving']} | 20% |\n"
        md += f"| Experience Relevance | {s['experience_relevance']} | 20% |\n"
        md += f"| Consistency | {s['consistency']} | 15% |\n"
        md += f"| Communication | {s['communication']} | 15% |\n"
        md += f"| **Risk Penalty** | **{s['risk_penalty']}** | - |\n"
        md += f"| **Final Score** | **{s['final_score']}** | 100% |\n\n"

        md += "## 👤 Candidate Profile\n"
        md += f"- **Experience:** {p['years_experience']} years\n"
        md += f"- **Location:** {p['current_location']}\n"
        md += f"- **Salary Expectation:** {p['salary_expectation']}\n"
        md += f"- **Availability:** {p['availability']} ({p['notice_period']})\n\n"

        md += "## 🛠️ Technical Evidence Profile\n"
        md += "### Validated Skills\n"
        if r['technical_profile']['validated_skills']:
            for vs in r['technical_profile']['validated_skills']:
                md += f"- **{vs['skill']}**: {vs['evidence']}\n"
        else:
            md += "None identified.\n"
        
        md += "\n### Claimed Skills\n"
        md += f"{', '.join(r['technical_profile']['claimed_skills']) or 'None'}\n\n"

        md += "## ⚠️ Risks & Contradictions\n"
        if r['contradictions']:
            md += "### Information Variance\n"
            for c in r['contradictions']:
                md += f"- **{c['field'].title()}**: {c['claims'][0]}\n"
        
        md += "\n### Identified Risks\n"
        for risk in r['risk_assessment']['identified_risks']:
            md += f"- {risk['risk']}\n"

        md += "\n---\n*Confidential ATS Enterprise Report*"
        return md

    def save_report(self, output_dir: str):
        """Saves the report in both JSON and Markdown formats."""
        os.makedirs(output_dir, exist_ok=True)
        
        json_path = os.path.join(output_dir, "recruiter_screening_report.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2)
            
        md_path = os.path.join(output_dir, "recruiter_screening_report.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_markdown())
            
        return json_path, md_path

def main():
    builder = RecruiterReportBuilder("cand_d7e57bdf")
    builder.load_data("outputs/answer_analysis_results.json", "outputs/automated_screening_report.json", "outputs/behavioral_indicators_report.json")
    builder.build()
    builder.save_report("outputs")

if __name__ == "__main__":
    main()
