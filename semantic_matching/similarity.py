from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# =========================================
# SKILL SIMILARITY (CORE)
# =========================================
def compute_skill_similarity(resume_skills, jd_skills, embedder, job_title=""):
    """
    Computes semantic similarity for skills using JD-Requirement Coverage.
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

    # Similarity matrix (Resume x JD)
    sim_matrix = cosine_similarity(resume_emb, jd_emb)
    
    # Requirement Coverage: For each JD skill, how well is it covered by the resume?
    max_per_requirement = sim_matrix.max(axis=0)
    skill_score = float(max_per_requirement.mean())
    
    return skill_score

# =========================================
# EXPERIENCE SIMILARITY (BULLET MATCHING)
# =========================================
def compute_experience_similarity(resume_experience, jd_responsibilities, embedder):
    """
    Computes semantic similarity for experience.
    Uses JD-centric bullet coverage.
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

# =========================================
# PROJECT SIMILARITY (FIXED)
# =========================================
def compute_project_similarity(resume_projects, jd_description, embedder):
    if not resume_projects or not jd_description:
        return 0.0

    projects = [embedder.clean_text(p) for p in resume_projects if p]
    jd_text = embedder.clean_text(jd_description)

    if not projects or not jd_text:
        return 0.0

    proj_emb = embedder.get_embeddings(projects)
    jd_emb = embedder.get_embeddings([jd_text])

    if proj_emb.size == 0 or jd_emb.size == 0:
        return 0.0

    sim_matrix = cosine_similarity(proj_emb, jd_emb)
    max_proj = sim_matrix.max(axis=1)
    proj_score = float(max_proj.mean())
    return proj_score