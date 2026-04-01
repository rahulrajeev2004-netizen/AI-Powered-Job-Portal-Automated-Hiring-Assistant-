import numpy as np
from similarity import (
    compute_skill_similarity,
    compute_experience_similarity,
    compute_project_similarity
)

class Scorer:
    def __init__(self, embedder):
        self.embedder = embedder

        # Base weights (will be dynamically adjusted)
        self.base_weights = {
            "skills": 0.5,
            "experience": 0.3,
            "projects": 0.2
        }

    # =========================================
    # MATCH CLASSIFICATION
    # =========================================
    def classify_match(self, score):
        if score >= 0.7:
            return "Strong Match"
        elif score >= 0.5:
            return "Moderate Match"
        else:
            return "Weak Match"

    # =========================================
    # DYNAMIC WEIGHT ADJUSTMENT
    # =========================================
    def adjust_weights(self, skill_score, exp_score, proj_score):
        weights = self.base_weights.copy()

        # If projects missing → redistribute weight
        if proj_score == 0:
            weights["skills"] += 0.1
            weights["experience"] += 0.1
            weights["projects"] = 0

        # Normalize weights to sum = 1
        total = sum(weights.values())
        for k in weights:
            weights[k] /= total

        return weights

    # =========================================
    # CONFIDENCE SCORE (NEW)
    # =========================================
    def compute_confidence(self, skill_score, exp_score, proj_score):
        """
        Confidence based on variance of component scores (Requirement 7).
        Higher similarity between sections → Higher confidence.
        """
        scores = [s for s in [skill_score, exp_score, proj_score] if s > 0]
        if len(scores) < 2:
            return 0.8  # Default confidence for single-section matches
        
        variance = np.var(scores)
        # Variance of 0.0 → 1.0 confidence, Variance of 0.1 → ~0.7 confidence
        confidence = 1.0 - min(0.5, variance * 3)
        return round(float(confidence), 2)

    def compute_skill_similarity(self, resume_skills, jd_skills, embedder, job_title=""):
        """
        Computes semantic similarity for skills using Top-K averaging.
        This prevents score dilution from low-relevance resume items.
        """
        # Clean inputs
        resume_skills = embedder.prepare_skills(resume_skills)
        jd_skills = embedder.prepare_skills(jd_skills)

        # Fallback heuristic: use job title if JD skills are missing or generic
        if (not jd_skills or (len(jd_skills) == 1 and jd_skills[0] == 'mandatory')) and job_title:
            jd_skills = [embedder.clean_job_title(job_title)]

        if not resume_skills or not jd_skills:
            return 0.0

        # Embeddings
        resume_emb = embedder.get_embeddings(resume_skills)
        jd_emb = embedder.get_embeddings(jd_skills)

        if resume_emb.size == 0 or jd_emb.size == 0:
            return 0.0

        # Similarity matrix
        sim_matrix = cosine_similarity(resume_emb, jd_emb)
        
        # For every JD requirement, find its best match in the resume
        # This is "Requirement Coverage"
        max_per_requirement = sim_matrix.max(axis=0)
        
        # Final Skill Score = average of coverage
        skill_score = float(max_per_requirement.mean())
        return skill_score

    def compute_experience_similarity(self, resume_experience, jd_responsibilities, embedder):
        """
        Computes semantic similarity for experience.
        Uses Bullet-to-Bullet max pooling.
        """
        if not resume_experience or not jd_responsibilities:
            return 0.0

        res_bullets = [embedder.clean_text(b) for b in resume_experience if b]
        jd_bullets = [embedder.clean_text(r) for r in jd_responsibilities if r]

        if not res_bullets or not jd_bullets:
            return 0.0

        res_emb = embedder.get_embeddings(res_bullets)
        jd_emb = embedder.get_embeddings(jd_bullets)

        if res_emb.size == 0 or jd_emb.size == 0:
            return 0.0

        matrix = cosine_similarity(res_emb, jd_emb)
        # Coverage: Each JD responsibility should be met by at least one resume bullet
        max_per_jd_bullet = matrix.max(axis=0)
        exp_score = float(max_per_jd_bullet.mean())
        return exp_score

    def calculate_match_scores(self, resume_data, jd_data):
        """
        Expert Role-Aware Scorer (Day 12 Final Calibration).
        Implements penalties for specialized/leadership roles and boosts for core roles.
        """
        raw_title = jd_data.get("job_title", "")
        job_title = self.embedder.clean_job_title(raw_title)
        title_lower = job_title.lower()
        
        # 1. Component Scores (No innate scaling here)
        skill_score = compute_skill_similarity(
            resume_data.get("skills", []),
            jd_data.get("required_skills", []),
            self.embedder,
            job_title=job_title
        )
        
        exp_score = compute_experience_similarity(
            resume_data.get("experience", []),
            jd_data.get("responsibilities", []),
            self.embedder
        )
        
        proj_score = compute_project_similarity(
            resume_data.get("projects", []),
            jd_data.get("description", ""),
            self.embedder
        )
        
        # 2. Dynamic Weighting (Requirement 5)
        weights = {"skills": 0.5, "experience": 0.3, "projects": 0.2}
        if proj_score == 0:
            weights = {"skills": 0.6, "experience": 0.4, "projects": 0.0}
            
        # 3. Base Weighted Score
        base_score = (
            weights["skills"] * skill_score +
            weights["experience"] * exp_score +
            weights["projects"] * proj_score
        )
        
        # 4. ROLE-AWARE PENALTY SYSTEM (Requirement 1)
        penalties_applied = []
        multiplier = 1.0
        
        SPECIALIZED_ROLES = ["anesthetist", "midwife", "neonatal", "psychiatric", "oncology", "perioperative"]
        LEADERSHIP_ROLES = ["chief", "director", "head", "officer", "administrator"]
        CORE_ROLES = ["icu", "critical care", "staff nurse", "ward nurse", "patient care"]
        
        if any(role in title_lower for role in SPECIALIZED_ROLES):
            multiplier *= 0.6  # Strong penalty for specialized roles
            penalties_applied.append("specialized")
            
        if any(role in title_lower for role in LEADERSHIP_ROLES):
            multiplier *= 0.5  # Very strong penalty for leadership roles
            penalties_applied.append("leadership")
            
        if any(role in title_lower for role in CORE_ROLES):
            multiplier *= 1.1  # Core boost
            
        # 5. VALIDATION CHECKS (Requirement 3 & 4)
        if skill_score < 0.5:
            multiplier *= 0.7  # Skill validation penalty
            
        final_score_scaled = base_score * multiplier
        
        # 6. NON-LINEAR SPREAD (Requirement 2)
        # Power 1.2 expands the spread (Strong gets higher, Low gets lower)
        final_score_calibrated = max(0.0, min(1.0, final_score_scaled)) ** 1.2
        
        # 7. Classification (Requirement 6: Strong >= 0.7, Moderate >= 0.5)
        match_level = self.classify_match(final_score_calibrated)
        
        # MANDATORY DEBUG (Requirement 7)
        print(f"\n[DEBUG] {job_title}")
        print(f"Skills: {skill_score:.2f} | Exp: {exp_score:.2f} | Proj: {proj_score:.2f}")
        print(f"Penalties Applied: {penalties_applied} | Multiplier: {multiplier:.2f}")
        print(f"Final Score: {final_score_calibrated:.2f} | Match: {match_level}")
        
        return {
            "job_title": job_title,
            "final_score": round(float(final_score_calibrated), 2),
            "match_level": match_level,
            "penalty_applied": penalties_applied
        }