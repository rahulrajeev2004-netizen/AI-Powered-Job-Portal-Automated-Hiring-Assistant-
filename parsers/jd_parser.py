
import re
import uuid
import json
from datetime import datetime
from typing import Optional
from utils.logger import get_logger

logger = get_logger("jd_parser", "logs/jd_parsing.log")

# ---------------------------------------------------------------------------
# SKILL SYNONYMS  –  canonical term  →  list of known aliases
# ---------------------------------------------------------------------------
SKILL_SYNONYMS: dict[str, list[str]] = {
    # Languages
    "Python":           ["py", "python3", "python programming"],
    "JavaScript":       ["js", "javascript", "ecmascript", "es6", "es2015"],
    "TypeScript":       ["ts", "typescript"],
    "Java":             ["java programming", "core java"],
    "C++":              ["cpp", "c plus plus"],
    "C#":               ["csharp", "c-sharp", "dotnet c#"],
    "Go":               ["golang", "go language"],
    "Rust":             ["rust lang", "rust programming"],
    "PHP":              ["php5", "php7", "php8"],
    "Swift":            ["swift language", "swift programming"],
    "Kotlin":           ["kotlin android"],
    "R":                ["r language", "r programming", "rlang"],
    "Scala":            ["scala programming"],
    "Ruby":             ["ruby programming", "ruby lang"],
    # Frameworks / Libraries
    "Django":           ["django framework", "django rest framework", "drf"],
    "Flask":            ["flask framework", "flask api"],
    "FastAPI":          ["fast api"],
    "React":            ["reactjs", "react.js", "react js"],
    "Angular":          ["angularjs", "angular js", "angular framework"],
    "Vue.js":           ["vuejs", "vue js", "vue"],
    "Node.js":          ["nodejs", "node js", "node"],
    "Express.js":       ["expressjs", "express js", "express"],
    "Spring Boot":      ["springboot", "spring boot", "spring framework"],
    ".NET":             ["dotnet", "dot net", "asp.net", "aspnet"],
    "TensorFlow":       ["tensorflow", "tf"],
    "PyTorch":          ["pytorch", "torch"],
    "Keras":            ["keras api"],
    "Scikit-learn":     ["sklearn", "scikit learn"],
    "Pandas":           ["pandas library"],
    "NumPy":            ["numpy library"],
    # Databases
    "SQL":              ["structured query language", "sql query", "sql queries"],
    "MySQL":            ["mysql db", "mysql database"],
    "PostgreSQL":       ["postgres", "postgresql", "psql", "pg"],
    "MongoDB":          ["mongo", "mongodb", "mongo db"],
    "Redis":            ["redis cache", "redis db"],
    "Elasticsearch":    ["elastic search", "elasticsearch db"],
    "Cassandra":        ["apache cassandra"],
    "DynamoDB":         ["aws dynamodb", "dynamo db"],
    # Cloud / DevOps
    "AWS":              ["amazon web services", "amazon aws"],
    "GCP":              ["google cloud", "google cloud platform"],
    "Azure":            ["microsoft azure", "azure cloud"],
    "Docker":           ["docker container", "docker containerization"],
    "Kubernetes":       ["k8s", "kube", "kubernetes orchestration"],
    "Terraform":        ["terraform iac", "terraform infrastructure"],
    "Ansible":          ["ansible automation"],
    "Jenkins":          ["jenkins ci", "jenkins pipeline"],
    "GitHub Actions":   ["github actions ci", "gh actions"],
    "CI/CD":            ["continuous integration", "continuous delivery", "continuous deployment", "cicd"],
    # Concepts / Practices
    "REST API":         ["restful api", "rest apis", "restful apis", "rest", "restful services"],
    "GraphQL":          ["graphql api"],
    "Microservices":    ["microservice architecture", "micro-services"],
    "Agile":            ["agile methodology", "scrum", "kanban", "agile/scrum"],
    "Git":              ["github", "gitlab", "bitbucket", "version control", "git version control","git"],
    "Linux":            ["linux os", "ubuntu", "centos", "unix/linux"],
    "Machine Learning": ["ml", "machine learning algorithms", "ml models"],
    "Deep Learning":    ["dl", "deep learning models", "neural networks"],
    "NLP":              ["natural language processing", "nlp techniques"],
    "Data Analysis":    ["data analytics", "data analysis techniques"],
    "Data Visualization":["data viz", "data visualization tools"],
    "Tableau":          ["tableau dashboard", "tableau software"],
    "Power BI":         ["powerbi", "power bi dashboard", "ms power bi"],
    "Excel":            ["microsoft excel", "ms excel", "advanced excel"],
    # Soft / PM skills
    "Product Management":   ["product mgmt", "product manager skills"],
    "Agile Roadmap Execution": ["roadmap planning", "product roadmap"],
    "Stakeholder Management":  ["stakeholder communication", "stakeholder engagement"],
    "Data-Driven Decision Making": ["data driven decisions", "metrics-based decisions"],
    "Communication":    ["verbal communication", "written communication", "communication skills", "communication and counseling", "communication and patience", "child-friendly communication"],
    "Leadership":       ["team leadership", "lead teams", "people management", "leadership and team management", "leadership and autonomy", "leadership and planning"],
    "Problem Solving":  ["problem-solving", "analytical thinking", "problem-solving ability"],
    "Unit Testing":     ["unit tests", "test driven development", "tdd", "pytest", "junit"],
    "UI/UX":            ["ux design", "ui design", "user experience design", "ux/ui", "ui/ux principles"],
    # -----------------------------------------------------------------------
    # Healthcare / Nursing Clinical Skills
    # -----------------------------------------------------------------------
    "Patient Care":          ["patient-centered care", "patient care and support", "holistic patient care", "direct patient care", "bedside care", "patient monitoring"],
    "Clinical Assessment":   ["clinical knowledge", "clinical expertise", "advanced clinical expertise", "clinical decision-making", "diagnostic reasoning", "neurological assessment skills", "pre-anesthesia assessment"],
    "Medication Administration": ["medication administration", "administer medications", "iv medications", "administer iv therapies", "iv therapy"],
    "Vital Signs Monitoring": ["vital signs monitoring", "monitor vital signs", "ecg monitoring", "ecg interpretation", "blood pressure monitoring"],
    "Wound Care":            ["wound care expertise", "wound care and dressing", "perform wound care", "post-operative wound care"],
    "Critical Care":         ["critical care skills", "icu care", "intensive care", "critical thinking and rapid decision-making"],
    "Emergency Response":    ["emergency response", "crisis management", "crisis intervention skills", "fast decision-making", "quick decision-making"],
    "Surgical Assistance":   ["surgical knowledge", "operation theatre techniques", "perioperative care", "scrub nurse", "circulating nurse", "sterility and infection control"],
    "Infection Control":     ["infection control", "infection prevention protocols", "sterile techniques", "hygiene and safety standards"],
    "Anesthesia Administration": ["administer anesthesia", "anesthesia care", "crna", "anesthesia training"],
    "Dialysis Management":   ["hemodialysis", "peritoneal dialysis", "dialysis skills", "technical dialysis skills", "operate dialysis machines"],
    "Mental Health Care":    ["psychiatric care", "mental health assessment", "psychotherapy", "counseling and interpersonal skills", "therapeutic communication"],
    "Pediatric Care":        ["pediatric nursing", "child care skills", "neonatal care", "nicu care", "newborn care", "vaccinations"],
    "Maternal Care":         ["maternal care expertise", "obstetric care", "prenatal care", "postnatal care", "labor and delivery", "midwifery"],
    "Oncology Nursing":      ["chemotherapy administration", "oncology care", "palliative care", "end-of-life care", "cancer care"],
    "Pharmacology":          ["pharmacology knowledge", "knowledge of pharmacology", "drug administration", "medication management"],
    "Documentation":         ["patient records", "medical records", "clinical documentation", "maintain patient records", "accurate documentation"],
    "Patient Education":     ["patient education", "educate patients", "educate families", "health education", "health awareness"],
    "Community Health":      ["community health", "public health programs", "disease prevention", "health promotion", "epidemiological data", "immunization programs"],
    "Triage":                ["triage assessment", "patient triage", "perform triage", "abcde approach"],
    "Empathy":               ["compassion and empathy", "emotional support", "emotional resilience and patience", "empathy and active listening"],
    "Multitasking":          ["multitasking ability", "ability to multitask"],
    "Time Management":       ["time management skills"],
    "Risk Assessment":       ["risk assessment skills", "health risk assessment"],
    "Rehabilitation Care":   ["rehabilitation nursing", "rehabilitation care plans", "physical therapy support", "recovery support"],
    "Geriatric Care":        ["geriatric nursing", "elderly care", "long-term care management", "chronic condition management"],
    "Infection Control Nursing": ["infection control nurse", "infection prevention", "hospital infection control"],
    "Health Policy":         ["health policy", "policy understanding", "policy implementation", "healthcare laws"],
    "Research & Audit":      ["clinical audits", "research skills", "analytical and research skills", "evidence-based care"],
    "Team Coordination":     ["team coordination", "multidisciplinary team", "interdisciplinary collaboration", "team coordination skills"],
    "Counseling":            ["counseling skills", "patient counseling", "patient counseling and education", "counseling sessions"],
    "Attention to Detail":   ["attention to detail", "high attention to detail", "precision and attention to detail"],
    "CPR / BLS":             ["cpr", "basic life support", "bls", "advanced cardiac life support", "acls"],
    "RN License":            ["registered nurse", "rn", "rn license", "registered nurse license", "nursing license"],
    "ICU Care":              ["icu", "intensive care unit", "critical care nursing", "icu care"],
    "Patient Care":          ["direct patient care", "patient care", "nursing care"],
}

# Build reverse lookup: alias (lower) → canonical
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in SKILL_SYNONYMS.items():
    _ALIAS_TO_CANONICAL[_canonical.lower()] = _canonical
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias.lower()] = _canonical

# ---------------------------------------------------------------------------
# ROLE SYNONYM MAP  –  various role title patterns → normalized role
# ---------------------------------------------------------------------------
ROLE_SYNONYMS: dict[str, list[str]] = {
    # Tech roles
    "Software Engineer":        ["software developer", "swe", "sde", "programmer", "software development engineer"],
    "Backend Developer":        ["backend engineer", "server-side developer", "backend dev", "be developer"],
    "Frontend Developer":       ["frontend engineer", "ui developer", "front-end developer", "frontend dev"],
    "Full Stack Developer":     ["full stack engineer", "fullstack developer", "full-stack developer"],
    "Data Scientist":           ["data science engineer", "ml scientist", "machine learning scientist"],
    "Data Engineer":            ["data pipeline engineer", "data infrastructure engineer", "dataops engineer"],
    "Machine Learning Engineer":["ml engineer", "ai engineer", "ai/ml engineer"],
    "DevOps Engineer":          ["devops specialist", "site reliability engineer", "sre", "infrastructure engineer"],
    "Product Manager":          ["pm", "product owner", "po", "technical product manager"],
    "Project Manager":          ["project lead", "delivery manager", "engagement manager"],
    "UX Designer":              ["ui/ux designer", "ux/ui designer", "product designer", "user experience designer"],
    "QA Engineer":              ["quality assurance engineer", "test engineer", "qa analyst", "sdet"],
    "Security Engineer":        ["cybersecurity engineer", "information security engineer", "infosec engineer"],
    "Cloud Engineer":           ["cloud architect", "cloud infrastructure engineer", "cloud solutions engineer"],
    "Business Analyst":         ["ba", "business analyst", "requirements analyst"],
    "Data Analyst":             ["analytics engineer", "reporting analyst", "bi analyst"],
    # Healthcare / Nursing roles
    "Staff Nurse":              ["registered nurse", "rn", "staff nurse rn", "general nurse"],
    "Licensed Practical Nurse": ["lpn", "vocational nurse", "lvn", "practical nurse"],
    "Nursing Officer":          ["nursing officer", "government nursing officer"],
    "Nurse Practitioner":       ["np", "advanced practice nurse", "apn", "advanced nurse practitioner"],
    "Clinical Nurse Specialist": ["cns", "clinical specialist nurse"],
    "Nurse Anesthetist":        ["crna", "certified registered nurse anesthetist", "anesthesia nurse"],
    "Nurse Midwife":            ["cnm", "certified nurse midwife", "midwife", "midwifery nurse"],
    "ICU Nurse":                ["intensive care nurse", "critical care icu nurse", "icu staff nurse"],
    "ER Nurse":                 ["emergency room nurse", "emergency nurse", "accident and emergency nurse"],
    "Trauma Nurse":             ["trauma care nurse", "trauma specialist nurse"],
    "Cardiac Nurse":            ["cardiology nurse", "ccu nurse", "cardiac care nurse"],
    "Oncology Nurse":           ["cancer nurse", "chemotherapy nurse", "oncology staff nurse"],
    "Pediatric Nurse":          ["paediatric nurse", "children's nurse", "child health nurse"],
    "Neonatal Nurse":           ["nicu nurse", "newborn care nurse", "neonatal icu nurse"],
    "Psychiatric Nurse":        ["mental health nurse", "psychiatric staff nurse", "psych nurse"],
    "OR Nurse":                 ["operating room nurse", "scrub nurse", "circulating nurse", "theatre nurse"],
    "Nurse Manager":            ["nursing manager", "ward manager", "unit manager"],
    "Nursing Supervisor":       ["head nurse", "chief nurse", "nursing superintendent"],
    "Community Health Nurse":   ["public health nurse", "community nurse", "chw nurse"],
    "School Nurse":             ["educational institution nurse", "campus nurse"],
    "Occupational Health Nurse": ["workplace health nurse", "industrial nurse", "oh nurse"],
    "Home Health Nurse":        ["home care nurse", "domiciliary nurse", "visiting nurse"],
    "Dialysis Nurse":           ["nephrology nurse", "renal nurse", "haemodialysis nurse"],
    "Rehabilitation Nurse":     ["rehab nurse", "physiotherapy nurse", "recovery nurse"],
    "Geriatric Nurse":          ["elderly care nurse", "gerontology nurse", "old age nurse"],
    "Palliative Care Nurse":    ["hospice nurse", "end-of-life nurse", "comfort care nurse"],
    "Military Nurse":           ["army nurse", "defence nurse", "armed forces nurse"],
    "Nurse Educator":           ["nursing educator", "clinical educator", "nurse trainer", "nursing faculty"],
    "Nurse Researcher":         ["nursing researcher", "clinical research nurse", "research nurse"],
    "Legal Nurse Consultant":   ["forensic nurse", "nurse consultant legal", "medico-legal nurse"],
}

_ROLE_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in ROLE_SYNONYMS.items():
    _ROLE_ALIAS_TO_CANONICAL[_canonical.lower()] = _canonical
    for _alias in _aliases:
        _ROLE_ALIAS_TO_CANONICAL[_alias.lower()] = _canonical

# ---------------------------------------------------------------------------
# EDUCATION degree mappings (normalization)
# ---------------------------------------------------------------------------
DEGREE_NORMALIZATIONS: dict[str, str] = {
    # General degrees
    r"\bb\.?tech\.?\b":                  "B.Tech",
    r"\bb\.?e\.?\b":                     "B.E.",
    r"\bb\.?sc\.?\b":                    "B.Sc.",
    r"\bb\.?s\.?\b":                     "B.S.",
    r"\bb\.?c\.?a\.?\b":                 "BCA",
    r"\bb\.?b\.?a\.?\b":                 "BBA",
    r"\bb\.?com\.?\b":                   "B.Com",
    r"\bm\.?tech\.?\b":                  "M.Tech",
    r"\bm\.?e\.?\b":                     "M.E.",
    r"\bm\.?sc\.?\b":                    "M.Sc.",
    r"\bm\.?s\.?\b":                     "M.S.",
    r"\bm\.?b\.?a\.?\b":                 "MBA",
    r"\bm\.?c\.?a\.?\b":                 "MCA",
    r"\bph\.?d\.?\b":                    "Ph.D.",
    r"\bbachelor[''']?s?\b":             "Bachelor's",
    r"\bmaster[''']?s?\b":               "Master's",
    r"\bdoctorate\b":                    "Ph.D.",
    r"\bassociate[''']?s?\b":            "Associate's",
    # Nursing-specific degrees
    r"\bbsc\s+nursing\b":                "BSc Nursing",
    r"\bgnm\b":                          "GNM (General Nursing & Midwifery)",
    r"\bmsc\s+nursing\b":                "MSc Nursing",
    r"\bd\.?n\.?p\.?\b":                 "DNP (Doctor of Nursing Practice)",
    r"\bdoctor\s+of\s+nursing\s+practice\b": "DNP (Doctor of Nursing Practice)",
    r"\bm\.?p\.?h\.?\b":                 "MPH (Master of Public Health)",
    r"\bmaster\s+of\s+public\s+health\b": "MPH (Master of Public Health)",
    r"\bdiploma\s+in\s+(?:practical\s+)?nursing\b": "Diploma in Nursing",
    r"\bnursing\s+diploma\b":            "Diploma in Nursing",
    r"\bpost\s+basic\s+b\.?sc\b":        "Post Basic BSc Nursing",
}

# ---------------------------------------------------------------------------
# SECTION HEADING PATTERNS (for JD document splitting)
# ---------------------------------------------------------------------------
_SECTION_PATTERNS = {
    "summary":          r"(?i)^\s*(?:job\s+)?summary|^about\s+the\s+(?:role|job|position)|^overview",
    "responsibilities": r"(?i)^\s*responsibilities|^duties|^what\s+you[''']?ll\s+do|^role\s+&?\s*responsibilities|^key\s+responsibilities",
    "requirements":     r"(?i)^\s*requirements|^what\s+we[''']?re?\s+looking\s+for|^must[\s-]have",
    "qualifications":   r"(?i)^\s*qualifications|^minimum\s+qualifications",
    "skills":           r"(?i)^\s*(?:required\s+)?skills\s*(?:required|needed)?[:\-]*$|^technical\s+skills|^tech\s+stack|^core\s+competenc",
    "education":        r"(?i)^\s*education(?:al)?\s*(?:requirements?|qualifications?|background)?",
    "experience":       r"(?i)^\s*experience\s*(?:required|requirements?)?",
    "benefits":         r"(?i)^\s*benefits?|^perks|^what\s+we\s+offer|^compensation|^why\s+(?:join\s+us|us)",
    "preferred":        r"(?i)^\s*preferred|^nice[\s-]to[\s-]have|^bonus|^good\s+to\s+have|^plus\s+if\s+you",
    "work_settings":    r"(?i)^\s*work\s+settings?|^work\s+environment|^settings?\s+include|^where\s+you[''']?ll\s+work",
}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Lowercase, strip extra whitespace, normalize unicode quotes."""
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _resolve_skill(raw_skill: str) -> str:
    """Return the canonical skill name for a raw string (via synonym lookup)."""
    key = raw_skill.strip().lower()
    return _ALIAS_TO_CANONICAL.get(key, raw_skill.strip())


def _resolve_role(raw_role: str) -> str:
    """Return the canonical role name for a raw string."""
    key = raw_role.strip().lower()
    # Direct match
    if key in _ROLE_ALIAS_TO_CANONICAL:
        return _ROLE_ALIAS_TO_CANONICAL[key]
    # Partial substring match
    for alias, canonical in _ROLE_ALIAS_TO_CANONICAL.items():
        if alias in key or key in alias:
            return canonical
    return raw_role.strip()


def _normalize_degree(text: str) -> str:
    """Normalize degree strings to a canonical form."""
    for pattern, replacement in DEGREE_NORMALIZATIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _extract_skills_from_text(text: str) -> list[str]:
    """
    Scan raw text for any known skill terms or their synonyms.
    Returns a deduplicated list of canonical skill names.
    """
    found: set[str] = set()
    text_lower = text.lower()

    # Build a sorted list of aliases (longest first to avoid partial matches)
    sorted_aliases = sorted(_ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)

    for alias in sorted_aliases:
        # Word-boundary safe check (handle punctuation around skill names)
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(alias) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            canonical = _ALIAS_TO_CANONICAL[alias]
            found.add(canonical)

    return sorted(found)


def _split_into_sections(text: str) -> dict[str, str]:
    """
    Split JD text into named sections using heading patterns.
    Returns a dict of section_name → section_text.
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"_preamble": []}
    current_section = "_preamble"

    for line in lines:
        stripped = line.strip()
        matched = False
        for section_name, pattern in _SECTION_PATTERNS.items():
            # Heading: short line matching a section keyword
            if re.search(pattern, stripped) and len(stripped) < 80:
                current_section = section_name
                sections.setdefault(current_section, [])
                matched = True
                break
        if not matched:
            sections.setdefault(current_section, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _extract_experience(text: str) -> dict:
    """
    Extract experience requirement (years + field) from section text.
    Handles patterns like: '3+ years', '5 to 7 years', 'minimum 2 years', etc.
    """
    min_years: Optional[int] = None
    field: str = ""

    # Pattern: "X+ years" / "X years" / "X-Y years" / "X to Y years"
    patterns = [
        r"(\d+)\s*\+\s*years?",
        r"(\d+)\s*(?:to|-)\s*\d+\s*years?",
        r"minimum\s+of\s+(\d+)\s*years?",
        r"at\s+least\s+(\d+)\s*years?",
        r"(\d+)\s*years?\s+of\s+(?:relevant\s+|professional\s+|prior\s+)?experience",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            min_years = int(m.group(1))
            break

    # Try to extract 'field' context after experience years
    field_patterns = [
        r"\d+[\+\-]?\s*years?\s+(?:of\s+)?(?:relevant\s+|professional\s+)?experience\s+in\s+([^\.\n,]{3,60})",
        r"\d+[\+\-]?\s*years?\s+(?:of\s+)?(?:relevant\s+|professional\s+)?experience\s+(?:as\s+a?n?\s+)?([^\.\n,]{3,60})",
        r"experience\s+(?:in|with|as)\s+([^\.\n,]{3,60})",
    ]
    for pat in field_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            field = m.group(1).strip().rstrip(".")
            break

    result = {}
    if min_years is not None:
        result["min_years"] = min_years
    if field:
        result["relevant_field"] = field
    return result


def _extract_education(text: str) -> dict:
    """Extract education requirements (min degree + preferred degree)."""
    text_normalized = _normalize_degree(text)

    degree_order = ["Ph.D.", "MBA", "MCA", "M.Tech", "M.E.", "M.Sc.", "M.S.",
                    "Master's", "BCA", "B.Tech", "B.E.", "B.Sc.", "B.S.",
                    "Bachelor's", "Associate's"]

    found_degrees: list[str] = []
    for deg in degree_order:
        if re.search(re.escape(deg), text_normalized, re.IGNORECASE):
            found_degrees.append(deg)

    result: dict = {}
    if found_degrees:
        # Lowest found degree = min; highest (if >1 and contains 'preferred/plus') = preferred
        result["min_degree"] = found_degrees[-1]  # lowest in hierarchy
        preferred_keywords = r"preferred|plus|advantage|bonus|ideal|nice[\s-]to[\s-]have"
        for deg in found_degrees:
            idx = text_normalized.find(deg)
            surrounding = text_normalized[max(0, idx - 60): idx + len(deg) + 60]
            if re.search(preferred_keywords, surrounding, re.IGNORECASE) and deg != result["min_degree"]:
                result["preferred_degree"] = deg
                break
    return result


def _extract_responsibilities(text: str) -> list[str]:
    """Parse bullet / numbered responsibilities from a section."""
    items = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Remove bullet characters
        cleaned = re.sub(r"^[\u2022\u2023\u25aa\u25cf\u2013\-\*\•\·●]\s*", "", stripped)
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
        if cleaned and len(cleaned) > 2:
            items.append(cleaned)
    return items


def _extract_benefits(text: str) -> list[str]:
    """Parse benefit items from text."""
    items = []
    for line in text.split("\n"):
        stripped = line.strip()
        cleaned = re.sub(r"^[\u2022\u2023\u25aa\u25cf\u2013\-\*\•\·●]\s*", "", stripped)
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
        if cleaned and len(cleaned) > 2:
            items.append(cleaned)
    return items


def _extract_work_settings(text: str) -> list[str]:
    """Extract workplace settings (hospitals, clinics, etc.) from work_settings section."""
    items = []
    for line in text.split("\n"):
        stripped = line.strip()
        cleaned = re.sub(r"^[\u2022\u2023\u25aa\u25cf\u2013\-\*\•\·●]\s*", "", stripped)
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
        if cleaned and len(cleaned) > 3:
            items.append(cleaned)
    return items


def _extract_skills_from_section(text: str) -> list[str]:
    """
    Extract skills listed line-by-line in a 'Skills Required' section.
    Picks up bullet items and resolves them via synonym map; if not in map,
    keeps the raw item as a domain-specific skill.
    """
    items = []
    for line in text.split("\n"):
        stripped = line.strip()
        cleaned = re.sub(r"^[\u2022\u2023\u25aa\u25cf\u2013\-\*\•\·●]\s*", "", stripped)
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
        cleaned = cleaned.strip().rstrip(".,:")
        if cleaned and 3 < len(cleaned) < 80:
            # Resolve via synonym map, or keep as-is
            resolved = _resolve_skill(cleaned)
            items.append(resolved)
    return list(dict.fromkeys(items))  # deduplicate preserving order


def _extract_location(text: str) -> dict:
    """Extract city, country, and work type from preamble or full text."""
    location: dict = {}

    work_type_patterns = {
        "Remote":  r"\bremote\b",
        "Hybrid":  r"\bhybrid\b",
        "On-site": r"\bon[\s-]?site\b|\bonsite\b|\bin[\s-]?office\b",
    }
    for wtype, pat in work_type_patterns.items():
        if re.search(pat, text, re.IGNORECASE):
            location["work_type"] = wtype
            break

    # City / Country heuristic – look for "Location: X" or "Location: City, Country"
    loc_match = re.search(
        r"location\s*[:\-]?\s*([\w\s,]+?)(?:\n|remote|hybrid|on-site|\|)",
        text, re.IGNORECASE
    )
    if loc_match:
        loc_value = loc_match.group(1).strip().rstrip(",")
        parts = [p.strip() for p in loc_value.split(",")]
        if len(parts) >= 2:
            location["city"] = parts[0]
            location["country"] = parts[-1]
        elif len(parts) == 1 and parts[0]:
            location["city"] = parts[0]

    return location


def _extract_company(text: str) -> str:
    """Try to find company name from patterns like 'About <Company>' or 'at <Company>'."""
    patterns = [
        r"(?:about|join|at)\s+([A-Z][a-zA-Z0-9\s&\.\-]{2,40})(?:\.|,|\n)",
        r"company\s*[:\-]\s*([^\n,\.]{3,50})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return ""


def _extract_job_title(text: str) -> str:
    """Extract job title from JD – typically the first meaningful line or 'Title: ...' pattern."""
    # 0. Clean the text of common prefixes
    text = re.sub(r'^\s*\d+[\.\)]\s*', '', text) # Remove "1. " or "1) " at the very start

    # 1. Explicit label (Title: ...)
    m = re.search(r"(?:job\s+)?title\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # 2. Heuristic: Look for first short line that looks like a title
    for line in text.split("\n"):
        # Skip leading numbers in line
        clean_line = re.sub(r'^\s*\d+[\.\)]\s*', '', line).strip()
        if not clean_line:
            continue
            
        words = clean_line.split()
        # Role titles are usually short and start with uppercase
        if 1 <= len(words) <= 12 and any(c.isupper() for c in clean_line[:3]):
            return clean_line
            
    return ""


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def parse_jd(raw_text: str, company_name: str = "", job_id: str = "") -> dict:
    """
    Parse a raw job description string into a structured JD profile dict.

    Parameters
    ----------
    raw_text    : Raw job description text (plain text, cleaned or not).
    company_name: Optional explicit company name (overrides extraction).
    job_id      : Optional explicit Job ID; auto-generated if omitted.

    Returns
    -------
    dict conforming to data/schema/schema_jd.json
    """
    logger.info("Starting JD parsing...")

    # 1. Normalize text
    text = _normalize_text(raw_text)
    logger.debug(f"Normalized text length: {len(text)} chars")

    # 2. Split into sections
    sections = _split_into_sections(text)
    logger.debug(f"Detected sections: {list(sections.keys())}")

    full_text = text  # keep for global extraction fallback

    # 3. Job Title
    preamble = sections.get("_preamble", "")
    job_title_raw = _extract_job_title(preamble or full_text)
    job_title = _resolve_role(job_title_raw) if job_title_raw else ""
    logger.debug(f"Job title: {job_title}")

    # 4. Company
    company = company_name or _extract_company(full_text)

    # 5. Location
    location = _extract_location(full_text)

    # 6. Job Summary
    job_summary = sections.get("summary", preamble).strip()
    # Trim if too long (keep first 500 chars)
    if len(job_summary) > 500:
        job_summary = job_summary[:500].rsplit(" ", 1)[0] + "..."

    # 7. Experience
    exp_text = sections.get("experience", "") or sections.get("requirements", "") or full_text
    experience = _extract_experience(exp_text)

    # 8. Education
    edu_text = sections.get("education", "") or sections.get("requirements", "") or sections.get("qualifications", "") or full_text
    education = _extract_education(edu_text)

    # 8b. Qualifications
    qual_text = sections.get("qualifications", "")
    qualifications = _extract_benefits(qual_text) if qual_text else []

    # 9. Skills
    # Mandatory skills: taken from 'requirements', 'skills', and 'responsibilities' sections
    req_text = "\n".join([
        sections.get("requirements", ""),
        sections.get("skills", ""),
        sections.get("responsibilities", "")
    ]).strip()
    
    # Use synonym-scan for mandatory skills
    synonym_mandatory = _extract_skills_from_text(req_text) if req_text else _extract_skills_from_text(full_text)
    # Also extract bullet-listed skills from the dedicated skills section
    bullet_mandatory = _extract_skills_from_section(sections.get("skills", ""))
    # Merge both, deduplicate
    all_mandatory_raw = list(dict.fromkeys(synonym_mandatory + bullet_mandatory))

    # Preferred skills: from 'preferred' section
    pref_text = sections.get("preferred", "")
    synonym_preferred = _extract_skills_from_text(pref_text) if pref_text.strip() else []
    bullet_preferred  = _extract_skills_from_section(pref_text) if pref_text.strip() else []
    all_preferred_raw = list(dict.fromkeys(synonym_preferred + bullet_preferred))

    # Resolve synonyms
    mandatory_skills = [_resolve_skill(s) for s in all_mandatory_raw]
    preferred_skills = [_resolve_skill(s) for s in all_preferred_raw if s not in all_mandatory_raw]

    # Deduplicate
    mandatory_skills = list(dict.fromkeys(mandatory_skills))
    preferred_skills = list(dict.fromkeys(preferred_skills))

    logger.debug(f"Mandatory skills found: {mandatory_skills}")
    logger.debug(f"Preferred skills found: {preferred_skills}")

    # 10. Responsibilities
    resp_text = sections.get("responsibilities", "")
    responsibilities = _extract_responsibilities(resp_text) if resp_text else []

    # 11. Benefits
    benefits_text = sections.get("benefits", "")
    benefits = _extract_benefits(benefits_text) if benefits_text else []

    # 12. Work Settings
    ws_text = sections.get("work_settings", "")
    work_settings = _extract_work_settings(ws_text) if ws_text else []

    # 12. Assemble JD Profile
    jd_profile = {
        "job_id":       job_id or f"JOB-{str(uuid.uuid4())[:8].upper()}",
        "job_title":    job_title,
        "company_name": company,
        "location":     location,
        "job_summary":  job_summary,
        "requirements": {
            "experience": experience,
            "education":  education,
            "skills": {
                "mandatory": mandatory_skills,
                "preferred": preferred_skills,
            },
        },
        "qualifications": qualifications,
        "responsibilities": responsibilities,
        "work_settings":    work_settings,
        "benefits":     benefits,
        "_meta": {
            "parsed_at":         datetime.utcnow().isoformat() + "Z",
            "parser_version":    "1.1.0",
            "raw_char_count":    len(raw_text),
            "sections_detected": [k for k in sections if k != "_preamble"],
        },
    }

    logger.info(f"JD parsing complete. Job: '{job_title}' | Skills: {len(mandatory_skills)} mandatory, {len(preferred_skills)} preferred")
    return jd_profile


def parse_jd_batch(jd_list: list[dict]) -> list[dict]:
    """
    Parse a batch of JD dicts.  Each dict must have at least a 'raw_text' key.
    Optional keys: 'company_name', 'job_id'.

    Returns a list of structured JD profiles.
    """
    results = []
    for idx, item in enumerate(jd_list):
        raw = item.get("raw_text", "")
        if not raw:
            logger.warning(f"Batch item {idx} has no 'raw_text'. Skipping.")
            continue
        profile = parse_jd(
            raw_text=raw,
            company_name=item.get("company_name", ""),
            job_id=item.get("job_id", ""),
        )
        results.append(profile)
    logger.info(f"Batch parsing complete. Processed {len(results)} JDs.")
    return results


def save_parsed_jd(jd_profile: dict, output_path: str) -> None:
    """Serialize a parsed JD profile to a JSON file."""
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(jd_profile, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved parsed JD to: {output_path}")
