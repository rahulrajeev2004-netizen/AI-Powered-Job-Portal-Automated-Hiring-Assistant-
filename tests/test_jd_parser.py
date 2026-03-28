"""
tests/test_jd_parser.py
=======================
Pytest test suite for the Zecpath JD Parser module.

Run with:
    pytest tests/test_jd_parser.py -v
    pytest tests/test_jd_parser.py -v --tb=short
"""

import sys
import os
import json
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parsers.jd_parser import (
    parse_jd,
    parse_jd_batch,
    _normalize_text,
    _extract_skills_from_text,
    _extract_experience,
    _extract_education,
    _extract_responsibilities,
    _extract_location,
    _resolve_skill,
    _resolve_role,
    _split_into_sections,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_JD_BACKEND = """\
Junior Backend Developer

About Nebula Cloud Solutions
Location: Bengaluru, India | Hybrid

Job Summary
We are looking for a motivated Junior Backend Developer to join our core engineering team.

Responsibilities
- Write reusable, testable, and efficient code in Python.
- Help maintain database performance and integrity.
- Collaborate with front-end developers to integrate user-facing elements.

Requirements
- 1+ years of experience in Software Development.
- Proficiency in Python and SQL.
- Experience with RESTful APIs and Git.
- Bachelor's in Computer Science or a related field.

Preferred
- Familiarity with Django or Flask.
- Experience with PostgreSQL and Docker.

Benefits
- Competitive Salary
- Health Insurance
"""

SAMPLE_JD_ML_ENGINEER = """\
Machine Learning Engineer

Company: DeepMind Labs | Location: Remote

Overview
We need an ML Engineer to build and deploy production AI models.

Requirements
At least 4 years of experience in Machine Learning. Proficiency in PyTorch (torch) and scikit-learn (sklearn). Strong Python and NumPy skills. AWS cloud experience required.

Minimum Qualifications
M.Tech or M.S. in Computer Science.

What We Offer
- Stock options
- Flexible hours
"""

SAMPLE_JD_SYNONYM_HEAVY = """\
Full-Stack Developer

Company: Orion Digital Labs | Hybrid | Pune, India

Responsibilities
- Build UIs with reactjs and ts (TypeScript).
- Develop REST APIs in nodejs (express).
- Manage data in psql.

Requirements
3 to 5 years of experience as a software developer. Git version control required.

Preferred
- k8s experience
- Amazon AWS familiarity
"""


# ---------------------------------------------------------------------------
# Unit Tests: text normalization
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_removes_extra_whitespace(self):
        text = "Hello   World\n\n\n\nNew Para"
        result = _normalize_text(text)
        assert "   " not in result
        assert result.count("\n\n\n") == 0

    def test_normalizes_unicode_quotes(self):
        text = "\u2018smart quotes\u2019 and \u201cdouble\u201d"
        result = _normalize_text(text)
        assert "'" in result
        assert '"' in result

    def test_strips_leading_trailing(self):
        text = "   \n  hello world  \n  "
        assert _normalize_text(text) == "hello world"


# ---------------------------------------------------------------------------
# Unit Tests: skill extraction
# ---------------------------------------------------------------------------

class TestSkillExtraction:
    def test_detects_python(self):
        skills = _extract_skills_from_text("We need strong Python skills.")
        assert "Python" in skills

    def test_resolves_alias_reactjs(self):
        skills = _extract_skills_from_text("Build UIs with reactjs and vuejs.")
        assert "React" in skills
        assert "Vue.js" in skills

    def test_resolves_alias_postgres(self):
        skills = _extract_skills_from_text("Experience with psql and pg required.")
        assert "PostgreSQL" in skills

    def test_resolves_alias_k8s(self):
        skills = _extract_skills_from_text("Deploy via k8s.")
        assert "Kubernetes" in skills

    def test_resolves_alias_sklearn(self):
        skills = _extract_skills_from_text("Use sklearn for modelling.")
        assert "Scikit-learn" in skills

    def test_resolves_cicd_aliases(self):
        skills = _extract_skills_from_text("Maintain continuous integration and continuous delivery pipelines.")
        assert "CI/CD" in skills

    def test_no_false_positives(self):
        skills = _extract_skills_from_text("We value teamwork and dedication.")
        # Should not detect 'Python', 'SQL', etc.
        assert "Python" not in skills
        assert "SQL" not in skills

    def test_multiple_skills(self):
        text = "Required: Python, SQL, Git, Docker, and AWS."
        skills = _extract_skills_from_text(text)
        for expected in ["Python", "SQL", "Git", "Docker", "AWS"]:
            assert expected in skills


# ---------------------------------------------------------------------------
# Unit Tests: synonym resolution
# ---------------------------------------------------------------------------

class TestSynonymResolution:
    def test_resolve_skill_py(self):
        assert _resolve_skill("py") == "Python"

    def test_resolve_skill_torch(self):
        assert _resolve_skill("torch") == "PyTorch"

    def test_resolve_skill_unknown(self):
        assert _resolve_skill("SomeUnknownLib") == "SomeUnknownLib"

    def test_resolve_role_sde(self):
        result = _resolve_role("sde")
        assert result == "Software Engineer"

    def test_resolve_role_backend_dev(self):
        result = _resolve_role("backend dev")
        assert result == "Backend Developer"

    def test_resolve_role_unknown(self):
        result = _resolve_role("Wizard of Data")
        assert result == "Wizard of Data"


# ---------------------------------------------------------------------------
# Unit Tests: experience extraction
# ---------------------------------------------------------------------------

class TestExperienceExtraction:
    def test_extracts_plus_years(self):
        exp = _extract_experience("Requires 3+ years of experience in Python Development.")
        assert exp.get("min_years") == 3

    def test_extracts_minimum_years(self):
        exp = _extract_experience("Minimum of 5 years of experience required.")
        assert exp.get("min_years") == 5

    def test_extracts_range_years(self):
        exp = _extract_experience("3 to 5 years of software development experience.")
        assert exp.get("min_years") == 3

    def test_extracts_at_least_years(self):
        exp = _extract_experience("At least 7 years of Product Management experience.")
        assert exp.get("min_years") == 7

    def test_extracts_field(self):
        exp = _extract_experience("4+ years of experience in Machine Learning.")
        assert exp.get("min_years") == 4
        assert "Machine Learning" in exp.get("relevant_field", "")

    def test_no_experience_stated(self):
        exp = _extract_experience("Join our amazing team!")
        assert exp == {}


# ---------------------------------------------------------------------------
# Unit Tests: education extraction
# ---------------------------------------------------------------------------

class TestEducationExtraction:
    def test_extracts_bachelor(self):
        edu = _extract_education("Bachelor's degree in Computer Science required.")
        assert "Bachelor's" in edu.get("min_degree", "")

    def test_extracts_mba_preferred(self):
        edu = _extract_education("Bachelor's Degree required; MBA preferred.")
        assert "Bachelor's" in edu.get("min_degree", "")
        assert "MBA" in edu.get("preferred_degree", "")

    def test_extracts_btech(self):
        edu = _extract_education("B.Tech or M.Tech in Computer Science.")
        assert edu.get("min_degree") in ["B.Tech", "M.Tech", "B.Tech"]

    def test_no_education_stated(self):
        edu = _extract_education("Strong communication skills needed.")
        assert edu == {}


# ---------------------------------------------------------------------------
# Unit Tests: location extraction
# ---------------------------------------------------------------------------

class TestLocationExtraction:
    def test_detects_remote(self):
        loc = _extract_location("This role is fully remote.")
        assert loc.get("work_type") == "Remote"

    def test_detects_hybrid(self):
        loc = _extract_location("Office location: Bangalore | Hybrid")
        assert loc.get("work_type") == "Hybrid"

    def test_detects_onsite(self):
        loc = _extract_location("This is an on-site position at our HQ.")
        assert loc.get("work_type") == "On-site"


# ---------------------------------------------------------------------------
# Unit Tests: responsibilities extraction
# ---------------------------------------------------------------------------

class TestResponsibilitiesExtraction:
    def test_extracts_bullet_items(self):
        text = "• Build APIs\n• Write unit tests\n• Collaborate with team"
        items = _extract_responsibilities(text)
        assert len(items) == 3
        assert "Build APIs" in items

    def test_extracts_numbered_items(self):
        text = "1. Design schema\n2. Implement endpoints\n3. Write documentation"
        items = _extract_responsibilities(text)
        assert len(items) == 3


# ---------------------------------------------------------------------------
# Integration Tests: full parse_jd pipeline
# ---------------------------------------------------------------------------

class TestParseJD:
    def test_parse_backend_jd_title(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        assert "developer" in result["job_title"].lower() or "engineer" in result["job_title"].lower()

    def test_parse_backend_jd_company(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        assert "Nebula" in result["company_name"] or result["company_name"] == ""

    def test_parse_backend_jd_location(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        assert result["location"].get("work_type") == "Hybrid"

    def test_parse_backend_jd_experience(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        assert result["requirements"]["experience"].get("min_years") == 1

    def test_parse_backend_jd_education(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        edu = result["requirements"]["education"]
        assert "Bachelor" in edu.get("min_degree", "")

    def test_parse_backend_jd_mandatory_skills(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        mandatory = result["requirements"]["skills"]["mandatory"]
        assert "Python" in mandatory
        assert "SQL" in mandatory

    def test_parse_backend_jd_preferred_skills(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        preferred = result["requirements"]["skills"]["preferred"]
        assert "Django" in preferred or "Flask" in preferred

    def test_parse_backend_jd_responsibilities(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        assert len(result["responsibilities"]) >= 2

    def test_parse_backend_jd_benefits(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        assert len(result["benefits"]) >= 1

    def test_parse_ml_engineer_experience(self):
        result = parse_jd(SAMPLE_JD_ML_ENGINEER)
        assert result["requirements"]["experience"].get("min_years") == 4

    def test_parse_ml_engineer_skills_include_pytorch(self):
        result = parse_jd(SAMPLE_JD_ML_ENGINEER)
        mandatory = result["requirements"]["skills"]["mandatory"]
        assert "PyTorch" in mandatory

    def test_parse_ml_engineer_skills_include_sklearn(self):
        result = parse_jd(SAMPLE_JD_ML_ENGINEER)
        mandatory = result["requirements"]["skills"]["mandatory"]
        assert "Scikit-learn" in mandatory

    def test_parse_synonym_heavy_jd_react(self):
        result = parse_jd(SAMPLE_JD_SYNONYM_HEAVY)
        mandatory = result["requirements"]["skills"]["mandatory"]
        assert "React" in mandatory

    def test_parse_synonym_heavy_jd_typescript(self):
        result = parse_jd(SAMPLE_JD_SYNONYM_HEAVY)
        mandatory = result["requirements"]["skills"]["mandatory"]
        assert "TypeScript" in mandatory

    def test_parse_synonym_heavy_jd_postgres(self):
        result = parse_jd(SAMPLE_JD_SYNONYM_HEAVY)
        mandatory = result["requirements"]["skills"]["mandatory"]
        assert "PostgreSQL" in mandatory

    def test_parse_id_autogenerated(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        assert result["job_id"].startswith("JOB-")

    def test_parse_explicit_job_id(self):
        result = parse_jd(SAMPLE_JD_BACKEND, job_id="JOB-CUSTOM-001")
        assert result["job_id"] == "JOB-CUSTOM-001"

    def test_parse_explicit_company(self):
        result = parse_jd(SAMPLE_JD_BACKEND, company_name="Explicit Corp")
        assert result["company_name"] == "Explicit Corp"

    def test_meta_fields_present(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        meta = result.get("_meta", {})
        assert "parsed_at" in meta
        assert "parser_version" in meta
        assert "raw_char_count" in meta

    def test_output_is_json_serializable(self):
        result = parse_jd(SAMPLE_JD_BACKEND)
        serialized = json.dumps(result)
        assert len(serialized) > 10


# ---------------------------------------------------------------------------
# Integration Test: batch parsing
# ---------------------------------------------------------------------------

class TestParseJDBatch:
    def test_batch_returns_correct_count(self):
        batch = [
            {"raw_text": SAMPLE_JD_BACKEND, "job_id": "JOB-B01"},
            {"raw_text": SAMPLE_JD_ML_ENGINEER, "job_id": "JOB-B02"},
        ]
        results = parse_jd_batch(batch)
        assert len(results) == 2

    def test_batch_skips_empty_raw_text(self):
        batch = [
            {"raw_text": SAMPLE_JD_BACKEND},
            {"raw_text": ""},  # should be skipped
        ]
        results = parse_jd_batch(batch)
        assert len(results) == 1

    def test_batch_preserves_job_ids(self):
        batch = [
            {"raw_text": SAMPLE_JD_BACKEND, "job_id": "JOB-CUSTOM-A"},
        ]
        results = parse_jd_batch(batch)
        assert results[0]["job_id"] == "JOB-CUSTOM-A"


# ---------------------------------------------------------------------------
# Samples file integration test
# ---------------------------------------------------------------------------

class TestSamplesFile:
    SAMPLES_PATH = os.path.join(
        os.path.dirname(__file__), "..", "data", "samples", "jd_parsing_samples.json"
    )

    def test_samples_file_exists(self):
        assert os.path.exists(self.SAMPLES_PATH)

    def test_samples_file_parseable(self):
        with open(self.SAMPLES_PATH, "r", encoding="utf-8") as f:
            samples = json.load(f)
        assert len(samples) >= 5

    def test_each_sample_can_be_parsed(self):
        with open(self.SAMPLES_PATH, "r", encoding="utf-8") as f:
            samples = json.load(f)
        for sample in samples:
            result = parse_jd(sample["raw_text"])
            assert "job_id" in result
            assert "requirements" in result
