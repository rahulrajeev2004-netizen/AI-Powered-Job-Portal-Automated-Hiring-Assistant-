import re
import json
from typing import List, Dict, Optional, Tuple

DEGREE_LEVEL_MAP = {
    "phd": 3,
    "master": 2,
    "bachelor": 1,
    "diploma": 0,
    "associate": 0.5
}

# Domain mapping for semantic understanding
DOMAIN_MAP = {
    "nursing": ["healthcare", "medicine", "clinical", "patient care", "nursing", "medical"],
    "computer science": ["software engineering", "it", "information technology", "programming", "software development"],
    "information technology": ["computer science", "it", "software engineering"],
    "mechanical engineering": ["engineering", "manufacturing", "automotive"],
    "business administration": ["management", "business", "mba", "leadership"],
}

class AcademicEvaluator:
    def __init__(self):
        pass

    def compute_field_relevance(self, candidate_field: str, required_fields: List[str]) -> Tuple[float, List[str]]:
        if not candidate_field or not required_fields:
            return 0.0, []
        
        c_field = candidate_field.lower().strip()
        max_score = 0.0
        matched_items = []
        
        for req in required_fields:
            r_field = req.lower().strip()
            score = 0.0
            
            # 1. Exact Match
            if c_field == r_field:
                score = 1.0
            # 2. Substring Match
            elif c_field in r_field or r_field in c_field:
                score = 0.85
            
            # 3. Semantic/Domain Match
            if score < 0.85:
                # Check domain map for candidate field
                for canonical, aliases in DOMAIN_MAP.items():
                    # If candidate field is the canonical or among its aliases
                    all_aliases = aliases + [canonical]
                    if c_field in all_aliases:
                        # Check if requirement is among those same aliases
                        if any(r_field in (a_list := DOMAIN_MAP.get(a, []) + [a]) for a in all_aliases):
                             score = max(score, 0.85)
                             break
                        # Special check for nursing <-> healthcare if not caught
                        if (c_field == "nursing" and r_field == "healthcare") or (c_field == "healthcare" and r_field == "nursing"):
                             score = max(score, 0.9)
                             break
            
            # 4. Word Overlap fallback
            if score < 0.6:
                c_words = set(re.findall(r"\w+", c_field))
                r_words = set(re.findall(r"\w+", r_field))
                if not c_words or not r_words: continue
                overlap = len(c_words.intersection(r_words))
                if overlap > 0:
                    score = max(score, min(0.65, (overlap / max(len(c_words), len(r_words)) * 0.5) + 0.3))

            if score >= 0.3:
                if score > max_score:
                    max_score = score
                    matched_items = [r_field]
                elif score == max_score and r_field not in matched_items:
                    matched_items.append(r_field)
        
        return round(max_score, 2), matched_items

    def evaluate_relevance(self, candidate_profile: Dict, jd_input: Dict) -> Dict:
        edu_relevance = {
          "field_relevance_score": 0.0,
          "degree_match": False,
          "certification_boost": 0.0,
          "final_score": 0.0,
          "matched_fields": [],
          "overall_relevance": False
        }

        # Normalize JD inputs (Handle both direct and nested formats)
        jd_requirements = jd_input.get("requirements", {})
        jd_edu = jd_requirements.get("education", {}) if jd_requirements else jd_input
        
        # Determine JD min degree level
        jd_min_degree = jd_edu.get("min_degree", "bachelor") or jd_input.get("min_degree", "bachelor")
        jd_min_degree = jd_min_degree.lower()
        
        jd_min_level_val = 1
        for k, v in DEGREE_LEVEL_MAP.items():
            if k in jd_min_degree:
                jd_min_level_val = v
                break
        
        jd_required_fields = jd_edu.get("fields", []) or jd_input.get("required_education", [])
        if not jd_required_fields and jd_edu.get("field"):
            jd_required_fields = [jd_edu.get("field")]
        
        # JD Clinical/Healthcare domain detection for boost
        is_healthcare_jd = any(x in str(jd_required_fields).lower() or x in jd_min_degree for x in ["nurse", "medicine", "health", "clinical"])
        jd_pref_certs_domain = "healthcare" if is_healthcare_jd else "it"

        # 1. Degree Match (Strict Hierarchy)
        education = candidate_profile.get("education", [])
        cand_highest_val = -1
        for entry in education:
            level = entry.get("degree_level", "bachelor").lower()
            cand_highest_val = max(cand_highest_val, DEGREE_LEVEL_MAP.get(level, 1))
        
        edu_relevance["degree_match"] = bool(cand_highest_val >= jd_min_level_val)

        # 2. Field Match (Strict Logic)
        max_field_score = 0.0
        all_matched_fields = []
        for entry in education:
            field = entry.get("field", "").lower()
            score, matched = self.compute_field_relevance(field, jd_required_fields)
            if score > max_field_score:
                max_field_score = score
                all_matched_fields = matched
            elif score == max_field_score and score > 0:
                all_matched_fields.extend([f for f in matched if f not in all_matched_fields])
        
        edu_relevance["field_relevance_score"] = float(max_field_score)
        edu_relevance["matched_fields"] = [f.lower() for f in all_matched_fields] if max_field_score >= 0.6 else []

        # 3. Certification Boost (MANDATORY for matching domains)
        boost = 0.0
        certifications = candidate_profile.get("certifications", [])
        matching_certs = [c for c in certifications if c.get("category") == jd_pref_certs_domain]
        
        num_certs = len(matching_certs)
        if num_certs == 1:
            boost = 0.03
        elif num_certs == 2:
            boost = 0.05
        elif num_certs >= 3:
            # 3+ strong certs: +0.08–0.1
            boost = 0.08
            if any(c.get("confidence", 0) >= 0.95 for c in matching_certs):
                boost = 0.1
        
        edu_relevance["certification_boost"] = round(boost, 2)

        # 4. Final Score
        edu_relevance["final_score"] = round(min(1.0, float(edu_relevance["field_relevance_score"]) + boost), 2)

        # 5. Overall Relevance (STRICT DECISION)
        # Decision: field_score >= 0.6 AND degree_match is True
        edu_relevance["overall_relevance"] = bool(edu_relevance["field_relevance_score"] >= 0.6 and edu_relevance["degree_match"])

        return edu_relevance
