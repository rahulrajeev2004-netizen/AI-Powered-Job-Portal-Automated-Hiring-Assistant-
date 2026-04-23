import json
import os
import re
from typing import Dict, Any, List, Optional
import openai
from dotenv import load_dotenv

# Load environment variables (for API keys)
load_dotenv()

class AIAnswerUnderstandingEngine:
    """
    Production Aggregator Engine (Production Mode v3.0).
    Features: Insightful Semantics, Strict Dynamic Scoring, Unified Completeness Logic.
    """
    
    SYSTEM_PROMPT = """
You are an advanced AI Answer Understanding Engine (Production Mode v3.0).

Your task is to extract hiring entities and signals into a production-grade JSON.

-----------------------------------
1. SEMANTIC SUMMARY (CRITICAL UPGRADE)
-----------------------------------
Every semantic_summary MUST combine extracted signals into ONE coherent sentence indicating interpretation and hiring relevance.
Format: [What was detected] + [Context/Action] + [Implication]
Examples:
- "Candidate reports 4.5 years of professional experience, indicating mid-level engineering seniority."
- "Candidate demonstrates explicit proficiency in Python, supported by self-assessed skill rating."
- "Candidate describes legacy migration to microservices, indicating hands-on experience with system design and distributed systems."
If no signals: "No structured signals extracted; response remains high-level."

-----------------------------------
2. DYNAMIC CONFIDENCE SCORING
-----------------------------------
Assign confidence_score strictly within these bands:
- Strong structured data (years, salary, notice period): 0.80 - 0.95
- Explicit skills (clearly mentioned): 0.75 - 0.90
- Inferred skills (context-based): 0.65 - 0.85
- Binary signals (yes/no relocation, employment): 0.65 - 0.80
- Weak/general/vague responses: 0.40 - 0.60
Mix of signals -> use highest applicable band. Vague -> always below 0.60.

-----------------------------------
3. COMPLETENESS LOGIC
-----------------------------------
is_complete = TRUE if ANY exist: structured numeric data, explicit skill, inferred skill, domain/context, or binary meaningful signal.
FALSE only if response is vague AND no extractable signal exists.

-----------------------------------
4. SCHEMA & ADDITIONAL ENFORCEMENTS
-----------------------------------
Clean JSON - NO nulls, NO empty objects. Normalize all skill names (e.g., "API Design").
All inferred skills MUST include: {"name": string, "confidence": float, "sources": ["Q_ID"]}

{
"intent": {"primary": "", "confidence": 0.0},
"entities": {
    "skills": {
        "explicit": [],
        "inferred": [{"name": "", "confidence": 0.0, "sources": ["Q_ID"]}]
    },
    ...
},
"quality": {"is_vague": false, "is_complete": false},
"semantic_summary": "",
"confidence_score": 0.0
}
"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        self.global_state = self._initialize_state()
        
        self.norm_map = {
            "api design": "API Design",
            "db tuning": "Database Optimization",
            "database tuning": "Database Optimization",
            "microservices": "Distributed Systems"
        }

    def _initialize_state(self):
        return {
            "skills": {
                "explicit": [],
                "inferred": []
            },
            "experience": {
                "total_years": None,
                "domains": {}
            },
            "education": {"degree": None, "institution": None},
            "location": {"current": None, "negotiable": None},
            "salary": {
                "current": None,
                "expected": None
            },
            "notice_period": {"days": None, "negotiable": None}
        }

    def reset_session(self):
        self.global_state = self._initialize_state()

    def analyze_answer(self, question: str, question_type: str, answer: str, question_id: str = "unknown") -> Dict[str, Any]:
        if not self.api_key:
            return self._simulated_analysis(question, question_type, answer, question_id)
        
        prompt = self.SYSTEM_PROMPT.replace("{{question}}", question)\
                                   .replace("{{question_type}}", question_type)\
                                   .replace("{{answer}}", answer)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o", 
                messages=[{"role": "system", "content": "ATS Aggregator Production Mode v3.0."},
                          {"role": "user", "content": prompt}],
                temperature=0
            )
            content = response.choices[0].message.content.strip()
            if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
            result = json.loads(content)
            self._update_global_profile(result.get("entities", {}), question_type, question_id)
            return self._clean_nulls(result)
        except Exception as e:
            print(f"[ERROR] Engine v3.0 failed: {e}")
            return self._simulated_analysis(question, question_type, answer, question_id)

    def _update_global_profile(self, local: Dict, q_type: str, q_id: str):
        l_skills = local.get("skills", {})
        for s in l_skills.get("explicit", []):
            s_name = self.norm_map.get(s.lower(), s.title())
            if s_name not in self.global_state["skills"]["explicit"]:
                self.global_state["skills"]["explicit"].append(s_name)
        
        for s in l_skills.get("inferred", []):
            s_name = self.norm_map.get(s["name"].lower(), s["name"].title())
            existing = next((x for x in self.global_state["skills"]["inferred"] if x["name"] == s_name), None)
            if existing:
                existing["confidence"] = max(existing["confidence"], s["confidence"])
                if q_id not in existing["sources"]: existing["sources"].append(q_id)
            else:
                self.global_state["skills"]["inferred"].append({
                    "name": s_name,
                    "confidence": s["confidence"],
                    "sources": [q_id]
                })

        exp = local.get("experience", {})
        if exp.get("years") is not None:
            prev = self.global_state["experience"]["total_years"] or 0
            self.global_state["experience"]["total_years"] = max(prev, float(exp["years"]))
            if exp.get("domain"):
                self.global_state["experience"]["domains"][exp["domain"]] = exp["years"]

        sal = local.get("salary", {})
        if sal.get("value") is not None:
            is_expected = any(k in q_type.lower() or k in q_id for k in ["expect", "look", "SAL_02"])
            target = "expected" if is_expected else "current"
            self.global_state["salary"][target] = {
                "value": sal["value"],
                "currency": sal.get("currency", "INR"),
                "unit": sal.get("unit", "monthly")
            }

        loc = local.get("location", {})
        if loc.get("current"): self.global_state["location"]["current"] = loc["current"]
        if loc.get("negotiable") is not None: self.global_state["location"]["negotiable"] = loc["negotiable"]
        
        np = local.get("notice_period", {})
        if np.get("days") is not None:
            prev = self.global_state["notice_period"]["days"] or 0
            self.global_state["notice_period"]["days"] = max(prev, int(np["days"]))
        if np.get("negotiable") is not None: self.global_state["notice_period"]["negotiable"] = np["negotiable"]

        edu = local.get("education", {})
        if edu.get("degree"): self.global_state["education"]["degree"] = edu["degree"]
        if edu.get("institution"): self.global_state["education"]["institution"] = edu["institution"]

    def _simulated_analysis(self, question: str, question_type: str, answer: str, question_id: str) -> Dict[str, Any]:
        """Simulation Production Mode v3.0 - Fix: Salary semantics, upgraded summaries, recalibrated scores."""
        ans_l = answer.lower()
        entities = {
            "skills": {"explicit": [], "inferred": []},
            "experience": {"years": None, "domain": None},
            "education": {"degree": None, "institution": None},
            "location": {"current": None, "negotiable": None},
            "salary": {"value": None, "currency": None, "unit": None},
            "notice_period": {"days": None, "negotiable": None}
        }

        has_structured = False
        has_explicit = False
        has_inferred = False
        has_domain = False
        has_binary = False

        summary_parts = []
        is_vague = False

        # Facts
        ym = re.search(r"(\d+(?:\.\d+)?)\s*years?", ans_l)
        if ym: 
            entities["experience"]["years"] = float(ym.group(1))
            has_structured = True
            dom = "Cloud Engineering" if "cloud" in ans_l else None
            if dom: 
                entities["experience"]["domain"] = dom
                has_domain = True
            # FIX 2: Include domain context in summary when available
            if dom:
                summary_parts.append(f"Candidate reports {ym.group(1)} years of experience in {dom}, indicating domain-specific engineering seniority")
            else:
                summary_parts.append(f"Candidate reports {ym.group(1)} years of professional experience, indicating engineering seniority")

        sm = re.search(r"(\d+)\s*(lpa|k|thousand|month|dollars|usd)", ans_l)
        if sm:
            entities["salary"]["value"] = int(sm.group(1)) * (100000 if "lpa" in ans_l else 1)
            entities["salary"]["currency"] = "USD" if "dollar" in ans_l or "usd" in ans_l else "INR"
            entities["salary"]["unit"] = "monthly"
            has_structured = True
            # FIX 1: Distinguish current vs expected salary in summary (HARD RULE)
            _is_current_sal = any(k in ans_l for k in ["current", "take-home", "take home", "drawing", "ctc"])
            _is_expected_sal = any(k in question_id for k in ["SAL_02"]) or any(k in ans_l for k in ["expecting", "expect", "looking for", "want"])
            if _is_current_sal:
                summary_parts.append(f"Candidate reports current salary of {entities['salary']['value']} {entities['salary']['currency']} monthly, establishing compensation reference")
            elif _is_expected_sal:
                summary_parts.append(f"Candidate states expected salary of {entities['salary']['value']} {entities['salary']['currency']} monthly, defining target compensation")
            else:
                summary_parts.append(f"Candidate provides salary figure of {entities['salary']['value']} {entities['salary']['currency']} monthly")

        nm = re.search(r"(\d+)\s*days?", ans_l)
        if nm: 
            entities["notice_period"]["days"] = int(nm.group(1))
            has_structured = True
            summary_parts.append(f"Candidate communicates a {nm.group(1)}-day notice period, establishing strict timeline availability")
        if "negotiat" in ans_l and "notice" in ans_l or ("negotiat" in ans_l and nm):
            entities["notice_period"]["negotiable"] = True
            has_binary = True
            if not nm: summary_parts.append("Candidate indicates notice period negotiability, allowing flexible onboarding")

        if "thiruvananthapuram" in ans_l: 
            entities["location"]["current"] = "Thiruvananthapuram"
            has_binary = True
            summary_parts.append("Candidate confirms current location in Thiruvananthapuram")
        if "relocat" in ans_l: 
            entities["location"]["negotiable"] = True
            has_binary = True
            summary_parts.append("Candidate expresses willingness to relocate, showing role flexibility")

        if "degree" in ans_l or "bachelor" in ans_l:
            entities["education"]["degree"] = "Bachelor's"
            has_structured = True
            if "university" in ans_l: entities["education"]["institution"] = "State University"
            summary_parts.append("Candidate confirms Bachelor's degree, validating educational baseline")

        # Skills & Inference
        for t in ["Python", "Django", "React", "Node", "AWS", "Docker", "Kubernetes"]:
            if t.lower() in ans_l: 
                entities["skills"]["explicit"].append(t)
                has_explicit = True
        if has_explicit:
            skill_list = ', '.join(entities['skills']['explicit'])
            # FIX 2: Include deployment/usage context when keywords imply it
            if any(k in ans_l for k in ["deployed", "container", "production", "used"]):
                summary_parts.append(f"Candidate demonstrates explicit, production-level proficiency in {skill_list}, confirming hands-on deployment experience")
            else:
                summary_parts.append(f"Candidate demonstrates explicit proficiency in {skill_list}, confirming core technical competencies")

        if any(w in ans_l for w in ["microservices", "system migration", "service decomposition"]):
            entities["skills"]["inferred"].extend([
                {"name": "System Design", "confidence": 0.85, "sources": [question_id]},
                {"name": "Distributed Systems", "confidence": 0.85, "sources": [question_id]},
                {"name": "API Design", "confidence": 0.85, "sources": [question_id]}
            ])
            has_inferred = True
            summary_parts.append("Candidate describes migration of legacy systems to microservices, demonstrating hands-on experience in System Design, Distributed Systems, and API Design")

        if any(w in ans_l for w in ["database locks", "index usage", "read replicas", "query performance"]):
            entities["skills"]["inferred"].append({"name": "Database Optimization", "confidence": 0.80, "sources": [question_id]})
            has_inferred = True
            summary_parts.append("Candidate references performance and index strategies, establishing clear Database Optimization capabilities")

        is_complete = has_structured or has_explicit or has_inferred or has_domain or has_binary
        
        if not summary_parts and ("many" in ans_l or "experienced" in ans_l):
            is_vague = True
            
        if not is_complete:
            is_vague = True
            summary = "No structured signals extracted; response remains high-level."
            score = 0.50
        else:
            summary = " ".join(summary_parts)
            if not summary.endswith("."):
                summary += "."
            # FIX 3: Recalibrated confidence bands (no inflation, aligned with signal quality)
            if has_structured and (has_explicit or has_domain):
                score = 0.90  # Multiple strong signals
            elif has_structured:
                score = 0.82  # Single structured signal
            elif has_explicit and entities["skills"]["explicit"] and len(entities["skills"]["explicit"]) > 1:
                score = 0.82  # Multiple explicit skills
            elif has_explicit:
                score = 0.75  # Single explicit skill
            elif has_inferred:
                score = 0.72  # Inferred only - moderate, never inflated
            elif has_binary:
                score = 0.68  # Binary signals
            else:
                score = 0.55

        self._update_global_profile(entities, question_type, question_id)
        return self._clean_nulls({
            "intent": {"primary": question_type, "confidence": 0.95},
            "entities": entities,
            "quality": {"is_vague": is_vague, "is_complete": is_complete},
            "semantic_summary": summary,
            "confidence_score": round(score, 2)
        })

    def get_global_profile(self) -> Dict[str, Any]:
        return self._clean_nulls(self.global_state)

    def _clean_nulls(self, d: Any) -> Any:
        if isinstance(d, dict):
            cleaned = {k: self._clean_nulls(v) for k, v in d.items()}
            return {k: v for k, v in cleaned.items() if v is not None and v != {} and v != []}
        elif isinstance(d, list):
            cleaned = [self._clean_nulls(v) for v in d]
            return [v for v in cleaned if v is not None and v != {} and v != []]
        return d

if __name__ == "__main__":
    engine = AIAnswerUnderstandingEngine()
    print(json.dumps(engine.analyze_answer("Exp?", "experience", "I have 5 years in cloud.", "Q_EXP_01"), indent=2))
