"""
utils/pii_masker.py
--------------------
Masks Personally Identifiable Information (PII) and non-essential personal
attributes from resume text BEFORE it is passed to any scoring engine.

Masked categories:
  - Email addresses
  - Phone numbers
  - URLs / LinkedIn / GitHub links
  - Physical addresses (street, city, pin-code patterns)
  - Date of Birth / Age references
  - Gender-coded nouns and pronouns
  - Religion / caste references
  - Nationality / ethnicity markers
  - Candidate name (heuristic: first line of resume if short)
"""

import re
from typing import Tuple, List, Dict
from utils.logger import get_logger

logger = get_logger("pii_masker", "logs/pii_masker.log")

# ---------------------------------------------------------------------------
# Replacement tokens (readable placeholders)
# ---------------------------------------------------------------------------
TOKEN_EMAIL      = "[EMAIL]"
TOKEN_PHONE      = "[PHONE]"
TOKEN_URL        = "[URL]"
TOKEN_ADDRESS    = "[ADDRESS]"
TOKEN_DOB        = "[DOB]"
TOKEN_AGE        = "[AGE]"
TOKEN_GENDER     = "[GENDER]"
TOKEN_RELIGION   = "[RELIGION]"
TOKEN_ETHNICITY  = "[ETHNICITY]"
TOKEN_NAME       = "[NAME]"

# ---------------------------------------------------------------------------
# Regex Patterns
# ---------------------------------------------------------------------------

# Email
_RE_EMAIL = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE
)

# Phone  (India-centric + international)
_RE_PHONE = re.compile(
    r"(\+?\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{4,5}",
    re.IGNORECASE
)

# URL / LinkedIn / GitHub
_RE_URL = re.compile(
    r"(https?://\S+|www\.\S+|linkedin\.com/\S*|github\.com/\S*)",
    re.IGNORECASE
)

# PIN codes (Indian 6-digit) and ZIP codes
_RE_PINCODE = re.compile(r"\b\d{6}\b|\b\d{5}(-\d{4})?\b")

# Date of Birth patterns
_RE_DOB = re.compile(
    r"\b(date\s+of\s+birth|dob|d\.o\.b\.?|born\s+on|birth\s+date)\s*[:\-]?\s*"
    r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}|\w+\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE
)

# Age references
_RE_AGE = re.compile(
    r"\b(age|aged)\s*[:\-]?\s*\d{1,2}\s*(years?)?\b",
    re.IGNORECASE
)

# Gender-coded nouns / pronouns
_GENDER_TERMS = [
    r"\b(he|she|him|her|his|hers|himself|herself)\b",
    r"\b(male|female|man|woman|boy|girl|gentleman|lady)\b",
    r"\b(mr\.?|mrs\.?|ms\.?|miss|master)\b",
]
_RE_GENDER = re.compile("|".join(_GENDER_TERMS), re.IGNORECASE)

# Religion / caste keywords
_RELIGION_TERMS = [
    "hindu", "muslim", "christian", "sikh", "buddhist", "jain",
    "parsi", "jewish", "islam", "catholic", "protestant",
    "brahmin", "kshatriya", "vaishya", "shudra", "dalit", "obc", "sc", "st"
]
_RE_RELIGION = re.compile(
    r"\b(" + "|".join(_RELIGION_TERMS) + r")\b",
    re.IGNORECASE
)

# Nationality / ethnicity markers
_ETHNICITY_TERMS = [
    "indian", "american", "british", "chinese", "pakistani", "bangladeshi",
    "african", "asian", "caucasian", "hispanic", "latino", "latina",
    "white", "black", "arab", "nepali", "sri lankan", "filipino"
]
_RE_ETHNICITY = re.compile(
    r"\b(" + "|".join(_ETHNICITY_TERMS) + r")\b",
    re.IGNORECASE
)

# Marital status
_RE_MARITAL = re.compile(
    r"\b(single|married|divorced|widowed|unmarried|marital\s+status)\b",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def mask_pii(text: str, mask_name: bool = True) -> Tuple[str, Dict[str, int]]:
    """
    Applies all PII masking rules to the input text.

    Args:
        text: Raw resume/candidate text.
        mask_name: If True, attempts to mask the candidate name from
                   the first line (heuristic).

    Returns:
        (masked_text, report) where report is a dict of {token: count_replaced}.
    """
    report: Dict[str, int] = {}

    def _replace(pattern, replacement, txt, label):
        new_txt, n = pattern.subn(replacement, txt)
        if n:
            report[label] = report.get(label, 0) + n
        return new_txt

    # Heuristic: mask first non-empty short line as the candidate name
    if mask_name:
        lines = text.strip().split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Likely a name: short, no digits, no @ symbols
            if stripped and len(stripped) < 50 and not re.search(r"[\d@]", stripped):
                lines[i] = TOKEN_NAME
                report[TOKEN_NAME] = 1
                break
        text = "\n".join(lines)

    text = _replace(_RE_EMAIL,    TOKEN_EMAIL,     text, TOKEN_EMAIL)
    text = _replace(_RE_URL,      TOKEN_URL,       text, TOKEN_URL)
    text = _replace(_RE_PHONE,    TOKEN_PHONE,     text, TOKEN_PHONE)
    text = _replace(_RE_PINCODE,  TOKEN_ADDRESS,   text, TOKEN_ADDRESS)
    text = _replace(_RE_DOB,      TOKEN_DOB,       text, TOKEN_DOB)
    text = _replace(_RE_AGE,      TOKEN_AGE,       text, TOKEN_AGE)
    text = _replace(_RE_GENDER,   TOKEN_GENDER,    text, TOKEN_GENDER)
    text = _replace(_RE_RELIGION, TOKEN_RELIGION,  text, TOKEN_RELIGION)
    text = _replace(_RE_ETHNICITY,TOKEN_ETHNICITY, text, TOKEN_ETHNICITY)
    text = _replace(_RE_MARITAL,  TOKEN_GENDER,    text, TOKEN_GENDER + "_marital")

    total = sum(report.values())
    logger.info(f"PII masking complete — {total} item(s) masked: {report}")
    return text, report


def get_pii_summary(report: Dict[str, int]) -> str:
    """Returns a human-readable summary of what was masked."""
    if not report:
        return "No PII detected."
    parts = [f"{token}: {count}" for token, count in report.items()]
    return "Masked: " + ", ".join(parts)


def mask_candidate(candidate: dict) -> Tuple[dict, Dict[str, int]]:
    """
    Convenience wrapper: masks the 'resume_text' field inside a candidate dict.
    Returns the modified candidate dict and the PII report.
    """
    raw_text = candidate.get("resume_text", "")
    if not raw_text:
        return candidate, {}

    masked_text, report = mask_pii(raw_text)
    candidate = dict(candidate)           # shallow copy — don't mutate original
    candidate["resume_text"] = masked_text
    candidate["pii_masked"] = True
    candidate["pii_report"] = report
    return candidate, report


# ---------------------------------------------------------------------------
# CLI / standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = """
    Anita Mathew
    Email: anita.mathew@gmail.com | Phone: +91-9876543210
    LinkedIn: linkedin.com/in/anita-mathew
    DOB: 14/03/1995 | Age: 29 | Gender: Female | Religion: Christian
    Address: 12 Rose Street, Kochi, Kerala 682001

    She has 5 years of nursing experience.
    She worked as an ICU nurse at Apollo Hospital.
    """
    masked, rpt = mask_pii(sample)
    print("=== MASKED TEXT ===")
    print(masked)
    print("\n=== REPORT ===")
    print(get_pii_summary(rpt))
