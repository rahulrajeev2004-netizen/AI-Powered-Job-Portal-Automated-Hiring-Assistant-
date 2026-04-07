"""
scoring/bias_indicator.py
--------------------------
Evaluates bias indicators in:
  - Job Description (JD) text
  - Candidate resume text

Detects the following bias types:
  1. GENDER BIAS      — gendered language in JD requirements
  2. AGE BIAS         — age-based requirements or exclusions
  3. RELIGION BIAS    — religion/faith-based preferences
  4. ETHNICITY BIAS   — nationality or ethnicity preferences
  5. APPEARANCE BIAS  — references to physical attributes
  6. LANGUAGE BIAS    — native language requirements when irrelevant

Returns a structured BiasReport with per-category flags, matched phrases,
an overall bias_detected flag, and a human-readable summary.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger("bias_indicator", "logs/bias_indicator.log")


# ---------------------------------------------------------------------------
# Bias Pattern Definitions
# ---------------------------------------------------------------------------

_BIAS_PATTERNS: Dict[str, List[str]] = {
    "gender_bias": [
        # Gendered job titles / pronouns in JDs
        r"\b(he|she|him|her|his|hers)\b",
        r"\b(male\s+candidate|female\s+candidate|male\s+nurse|female\s+nurse)\b",
        r"\b(brotherhood|sisterhood|manpower|mankind|man\-hours)\b",
        r"\b(chairman|stewardess|fireman|policeman|mailman)\b",
        r"\b(prefer\s+(male|female)|only\s+(male|female))\b",
    ],
    "age_bias": [
        r"\b(age\s*(limit|bar|criteria|requirement|cap|cutoff|under|below|above|between))\b",
        r"\b(must\s+be\s+(under|below|above|atleast|at\s+least)\s+\d{2})\b",
        r"\b(freshers?\s+only|young\s+(candidate|professional|graduate))\b",
        r"\b(maximum\s+age|minimum\s+age)\b",
        r"\b(\d{2}\s*[-–]\s*\d{2}\s*years?\s+old)\b",
        r"\bupto\s+\d{2}\s+years\b",
    ],
    "religion_bias": [
        r"\b(christian|hindu|muslim|sikh|buddhist|jain|parsi|jewish)\s+(preferred|only|required|candidate)\b",
        r"\b(religious\s+affiliation|faith\s+based|church\s+going|mosque\s+going|temple\s+going)\b",
        r"\b(must\s+be\s+(christian|hindu|muslim|sikh))\b",
    ],
    "ethnicity_bias": [
        r"\b(indian\s+only|nationals?\s+only|local\s+candidates?\s+only)\b",
        r"\b(prefer\s+(indian|local|native)\s+candidates?)\b",
        r"\b(visa\s+status\s+required|must\s+be\s+(citizen|resident|domicile))\b",
        r"\b(race|caste|tribe|ethnic\s+background|racial\s+origin)\b",
    ],
    "appearance_bias": [
        r"\b(good\s+looks?|presentable|well\s+groomed|attractive|fair\s+complexion)\b",
        r"\b(height\s*(requirement|minimum|above|below|criteria))\b",
        r"\b(weight\s*(requirement|criteria|limit))\b",
        r"\b(physically\s+(fit|able|attractive))\b",
    ],
    "language_bias": [
        r"\b(mother\s+tongue|native\s+speaker\s+of\s+\w+|must\s+speak\s+\w+\s+at\s+home)\b",
        r"\b(fluent\s+in\s+(hindi|tamil|telugu|malayalam|kannada|marathi)\s+mandatory)\b",
        r"\b(local\s+language\s+mandatory)\b",
    ],
}

# Pre-compile all patterns
_COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]
    for category, patterns in _BIAS_PATTERNS.items()
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class CategoryResult:
    detected: bool = False
    matched_phrases: List[str] = field(default_factory=list)
    count: int = 0


@dataclass
class BiasReport:
    source: str                                          # "jd" or "resume"
    bias_detected: bool = False
    categories: Dict[str, CategoryResult] = field(default_factory=dict)
    total_flags: int = 0
    summary: str = ""
    risk_level: str = "LOW"                              # LOW | MEDIUM | HIGH

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "bias_detected": self.bias_detected,
            "risk_level": self.risk_level,
            "total_flags": self.total_flags,
            "summary": self.summary,
            "categories": {
                cat: {
                    "detected": res.detected,
                    "count": res.count,
                    "matched_phrases": res.matched_phrases
                }
                for cat, res in self.categories.items()
            }
        }


# ---------------------------------------------------------------------------
# Core Analysis Function
# ---------------------------------------------------------------------------

def analyze_bias(text: str, source: str = "jd") -> BiasReport:
    """
    Scans text for bias indicators across all defined categories.

    Args:
        text:   The raw text to analyze (JD or resume).
        source: Label for the report ("jd" or "resume").

    Returns:
        A BiasReport dataclass instance.
    """
    report = BiasReport(source=source)
    total_flags = 0

    for category, compiled_list in _COMPILED_PATTERNS.items():
        cat_result = CategoryResult()
        for pattern in compiled_list:
            matches = pattern.findall(text)
            if matches:
                cat_result.detected = True
                # Flatten match groups into strings
                for m in matches:
                    phrase = m if isinstance(m, str) else " ".join(m).strip()
                    if phrase and phrase not in cat_result.matched_phrases:
                        cat_result.matched_phrases.append(phrase.lower())
                cat_result.count += len(matches)
                total_flags += len(matches)

        report.categories[category] = cat_result

    report.bias_detected = any(r.detected for r in report.categories.values())
    report.total_flags = total_flags

    # Risk level
    if total_flags == 0:
        report.risk_level = "LOW"
    elif total_flags <= 3:
        report.risk_level = "MEDIUM"
    else:
        report.risk_level = "HIGH"

    # Human-readable summary
    flagged = [cat for cat, res in report.categories.items() if res.detected]
    if flagged:
        report.summary = (
            f"Bias detected in {len(flagged)} category(ies): "
            + ", ".join(c.replace("_", " ").title() for c in flagged)
            + f". Total flags: {total_flags}. Risk: {report.risk_level}."
        )
    else:
        report.summary = "No bias indicators detected. Text appears fair and neutral."

    logger.info(f"[{source.upper()}] Bias analysis complete — {report.summary}")
    return report


def analyze_jd_bias(jd_text: str) -> BiasReport:
    """Shortcut for analyzing a Job Description."""
    return analyze_bias(jd_text, source="jd")


def analyze_resume_bias(resume_text: str) -> BiasReport:
    """Shortcut for analyzing a resume (post-PII-mask)."""
    return analyze_bias(resume_text, source="resume")


def compare_bias(jd_report: BiasReport, resume_report: BiasReport) -> dict:
    """
    Cross-compares JD and resume bias reports to identify
    categories flagged in both (potential systemic bias).
    """
    jd_cats    = {c for c, r in jd_report.categories.items() if r.detected}
    res_cats   = {c for c, r in resume_report.categories.items() if r.detected}
    shared     = jd_cats & res_cats

    return {
        "jd_bias_categories":     sorted(jd_cats),
        "resume_bias_categories": sorted(res_cats),
        "shared_bias_categories": sorted(shared),
        "systemic_bias_risk":     len(shared) > 0,
        "recommendation": (
            "Review shared bias categories to ensure fair evaluation."
            if shared else
            "No systemic bias overlap between JD and resume detected."
        )
    }


# ---------------------------------------------------------------------------
# CLI / standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    sample_jd = """
    We are looking for a young male candidate, preferably under 30 years old.
    The candidate must be an Indian national only and should be physically fit
    and presentable. Christian candidates preferred.
    """

    sample_resume = """
    [NAME]
    She has 5 years of nursing experience.
    She was born in 1995 and is currently 29 years old.
    """

    jd_rpt     = analyze_jd_bias(sample_jd)
    res_rpt    = analyze_resume_bias(sample_resume)
    comparison = compare_bias(jd_rpt, res_rpt)

    print("=== JD BIAS REPORT ===")
    print(json.dumps(jd_rpt.to_dict(), indent=2))
    print("\n=== RESUME BIAS REPORT ===")
    print(json.dumps(res_rpt.to_dict(), indent=2))
    print("\n=== COMPARISON ===")
    print(json.dumps(comparison, indent=2))
