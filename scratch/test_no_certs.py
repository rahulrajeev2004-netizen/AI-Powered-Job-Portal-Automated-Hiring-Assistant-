
from scoring.ats_scorer import candidate_score_generator

job = {
    "job_title": "Software Engineer",
    "experience_required": 2.0,
    "required_skills": ["Java", "Python"], # No certs here
    "education_required": "Bachelors"
}

candidate = {
    "candidate_id": "test_cand",
    "skills": ["Java"],
    "experience_years": 5.0,
    "education": "Bachelors"
}

result = candidate_score_generator(candidate, job, 0.8)
import json
print(json.dumps(result["domain_relevance_detail"], indent=2))
print(result["explanation"])
