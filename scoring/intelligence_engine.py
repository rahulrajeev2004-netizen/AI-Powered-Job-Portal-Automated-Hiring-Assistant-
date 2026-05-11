import re
import hashlib
from typing import Dict, Any, List

class IntelligenceEngine:
    """
    Enterprise-grade scoring engine with independent logic for ATS, Screening, and HR.
    """

    @staticmethod
    def calculate_ats_score(structured_data: Dict[str, Any], job_reqs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realistic ATS evaluation based on multi-factor analysis.
        """
        sections = structured_data.get("sections", {})
        text = structured_data.get("full_text", "").lower()
        
        # 1. Skill Match (40%)
        required_skills = [s.lower() for s in job_reqs.get("mandatory_skills", [])]
        matched_skills = [s for s in required_skills if s in text]
        skill_score = (len(matched_skills) / len(required_skills) * 100) if required_skills else 50
        
        # 2. Experience Match (30%)
        req_years = job_reqs.get("min_years", 0)
        # Simple extraction of numbers near "year" or "exp"
        exp_matches = re.findall(r'(\d+)\+?\s*years?', text)
        found_years = max([int(y) for y in exp_matches] + [0])
        
        if found_years >= req_years:
            exp_score = 100
        elif found_years > 0:
            exp_score = 60 + (found_years / req_years * 40)
        else:
            exp_score = 40 # Minimum baseline for having some experience text
            
        # 3. Education Match (15%)
        req_degree = job_reqs.get("min_degree", "").lower()
        education_text = sections.get("education", "").lower()
        edu_score = 100 if req_degree in education_text or req_degree in text else 50
        
        # 4. Resume Quality & Format (15%)
        # Based on length, sections detected, and parser confidence
        quality_score = 50
        if len(sections) >= 3: quality_score += 20
        if structured_data.get("parser_confidence", 0) > 0.7: quality_score += 20
        if 500 < len(text) < 5000: quality_score += 10
        quality_score = min(100, quality_score)

        # Weighted Final ATS
        final_ats = (skill_score * 0.4) + (exp_score * 0.3) + (edu_score * 0.15) + (quality_score * 0.15)
        
        # Normalization (Ensuring it stays in realistic 20-95 range)
        final_ats = 20 + (final_ats * 0.75) 
        
        return {
            "score": round(final_ats, 2),
            "details": {
                "matched_skills": matched_skills,
                "missing_skills": list(set(required_skills) - set(matched_skills)),
                "experience_match": f"Found {found_years}y (Req {req_years}y)",
                "education_match": edu_score == 100,
                "resume_quality": "High" if quality_score > 80 else "Standard" if quality_score > 50 else "Basic"
            }
        }

    @staticmethod
    def calculate_screening_score(candidate_id: str, job_role: str) -> float:
        """
        Independent Screening Logic (Coding, MCQ, Aptitude).
        Simulated based on deterministic hash of candidate_id to mimic real variations.
        """
        h = int(hashlib.md5(f"screening_{candidate_id}".encode()).hexdigest(), 16)
        # Range: 40 to 95
        base = 40 + (h % 55)
        return float(round(base, 2))

    @staticmethod
    def calculate_hr_score(candidate_id: str) -> float:
        """
        Independent HR Logic (Communication, Behavior, Confidence).
        Simulated based on deterministic hash.
        """
        h = int(hashlib.md5(f"hr_{candidate_id}".encode()).hexdigest(), 16)
        # Range: 45 to 98
        base = 45 + (h % 53)
        return float(round(base, 2))

    @staticmethod
    def calculate_hiring_fit(final_score: float, ats_details: Dict[str, Any], hr_score: float) -> Dict[str, Any]:
        """
        Advanced Hiring Fit using the specified formula.
        Formula: (FinalScore * 0.70) + (SkillMatch * 0.15) + (CultureFit * 0.15)
        """
        skill_match_ratio = len(ats_details.get("matched_skills", [])) / \
                           max(1, len(ats_details.get("matched_skills", [])) + len(ats_details.get("missing_skills", [])))
        skill_match_score = skill_match_ratio * 100
        
        # Culture fit derived from HR performance
        culture_fit = hr_score 
        
        hiring_fit_val = (final_score * 0.70) + (skill_match_score * 0.15) + (culture_fit * 0.15)
        
        # Stability and Learning Potential (Simulated)
        stability = 70 + (final_score % 30)
        learning_potential = 60 + (skill_match_score % 40)
        
        category = "Reject"
        if hiring_fit_val >= 85: category = "Strong Hire"
        elif hiring_fit_val >= 70: category = "Hire"
        elif hiring_fit_val >= 55: category = "Review"
        elif hiring_fit_val >= 40: category = "Borderline"
        
        return {
            "percentage": round(hiring_fit_val, 2),
            "category": category,
            "metrics": {
                "skill_alignment": round(skill_match_score, 2),
                "culture_fit": round(culture_fit, 2),
                "stability_score": round(stability, 2),
                "learning_potential": round(learning_potential, 2)
            }
        }
