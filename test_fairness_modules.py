"""
test_fairness_modules.py
Quick integration test for PII Masker and Bias Indicator modules.
"""
import json
from utils.pii_masker import mask_pii, get_pii_summary
from scoring.bias_indicator import analyze_jd_bias, analyze_resume_bias, compare_bias

# -----------------------------------------------------------------------
# Test 1: PII Masker
# -----------------------------------------------------------------------
sample_resume = """
Anita Mathew
Email: anita.mathew@gmail.com | Phone: +91-9876543210
LinkedIn: linkedin.com/in/anita-mathew
DOB: 14/03/1995 | Age: 29 | Religion: Christian | Nationality: Indian
She has 5 years of ICU nursing experience.
"""

masked, report = mask_pii(sample_resume)
print("=" * 50)
print("TEST 1: PII MASKER")
print("=" * 50)
print(masked)
print("Summary:", get_pii_summary(report))
print()

# -----------------------------------------------------------------------
# Test 2: JD Bias Indicator
# -----------------------------------------------------------------------
sample_jd = (
    "Looking for a young male candidate under 30 years old. "
    "Indian nationals only. Must be physically fit and presentable. "
    "Christian candidates preferred."
)

jd_rpt = analyze_jd_bias(sample_jd)
print("=" * 50)
print("TEST 2: JD BIAS REPORT")
print("=" * 50)
d = jd_rpt.to_dict()
print("Risk Level  :", d["risk_level"])
print("Bias Detected:", d["bias_detected"])
print("Summary     :", d["summary"])
print("Flagged categories:")
for cat, v in d["categories"].items():
    if v["detected"]:
        print(f"  - {cat}: {v['matched_phrases']}")
print()

# -----------------------------------------------------------------------
# Test 3: Resume Bias (on already-masked text)
# -----------------------------------------------------------------------
res_rpt = analyze_resume_bias(masked)
print("=" * 50)
print("TEST 3: RESUME BIAS REPORT (post-PII-mask)")
print("=" * 50)
print("Bias Detected:", res_rpt.bias_detected)
print("Summary      :", res_rpt.summary)
print()

# -----------------------------------------------------------------------
# Test 4: Cross-comparison
# -----------------------------------------------------------------------
comp = compare_bias(jd_rpt, res_rpt)
print("=" * 50)
print("TEST 4: BIAS COMPARISON (JD vs Resume)")
print("=" * 50)
print(json.dumps(comp, indent=2))
print()
print("All tests complete.")
