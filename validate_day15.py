"""
validate_day15.py
Runs all Day 15 validation checks against fairness_adjusted_ranking.json
and reports PASS / FAIL for each rule.
"""
import json

OUTPUT_FILE = "outputs/fairness_adjusted_ranking.json"

with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

REQUIRED_JOB_FIELDS      = {"job_id", "fairness_adjusted", "normalization_method",
                             "bias_adjustment_method", "candidates", "bias_analysis"}
REQUIRED_CAND_FIELDS     = {"candidate_id", "original_score", "normalized_score",
                             "adjusted_score", "rank", "bias_flag"}
REQUIRED_BIAS_FIELDS     = {"bias_detected", "reason", "method"}

errors   = []
warnings = []
passed   = []

for job in data:
    jid = job.get("job_id", "UNKNOWN")

    # ── 1. Required job-level fields ───────────────────────────────────
    missing_job = REQUIRED_JOB_FIELDS - set(job.keys())
    extra_job   = set(job.keys()) - REQUIRED_JOB_FIELDS
    if missing_job:
        errors.append(f"[{jid}] Missing job fields: {missing_job}")
    if extra_job:
        errors.append(f"[{jid}] Extra job fields (not allowed): {extra_job}")

    # ── 2. normalization_method and bias_adjustment_method values ──────
    if job.get("normalization_method") != "min-max":
        errors.append(f"[{jid}] normalization_method is not 'min-max'")
    if "rule-based" not in str(job.get("bias_adjustment_method", "")):
        errors.append(f"[{jid}] bias_adjustment_method missing 'rule-based'")

    # ── 3. bias_analysis fields ────────────────────────────────────────
    ba = job.get("bias_analysis", {})
    missing_ba = REQUIRED_BIAS_FIELDS - set(ba.keys())
    if missing_ba:
        errors.append(f"[{jid}] Missing bias_analysis fields: {missing_ba}")
    if not ba.get("reason", "").strip():
        errors.append(f"[{jid}] bias_analysis.reason is empty")
    if ba.get("method", "") != "min-max + rule-based adjustment":
        errors.append(f"[{jid}] bias_analysis.method value incorrect")

    candidates = job.get("candidates", [])

    for c in candidates:
        cid = c.get("candidate_id", "?")

        # ── 4. Required candidate fields ───────────────────────────────
        missing_c = REQUIRED_CAND_FIELDS - set(c.keys())
        extra_c   = set(c.keys()) - REQUIRED_CAND_FIELDS
        if missing_c:
            errors.append(f"[{jid}][{cid}] Missing candidate fields: {missing_c}")
        if extra_c:
            errors.append(f"[{jid}][{cid}] Extra candidate fields: {extra_c}")

        norm = c.get("normalized_score", -1)
        adj  = c.get("adjusted_score",  -1)
        flag = c.get("bias_flag", None)

        # ── 5. normalized_score in [0, 1] ─────────────────────────────
        if not (0.0 <= norm <= 1.0):
            errors.append(f"[{jid}][{cid}] normalized_score={norm} out of [0,1]")

        # ── 6. adjusted_score in [0, 1] ───────────────────────────────
        if not (0.0 <= adj <= 1.0):
            errors.append(f"[{jid}][{cid}] adjusted_score={adj} out of [0,1]")

        # ── 7. If bias_flag True → adjusted >= normalized ──────────────
        if flag is True and round(adj, 4) < round(norm, 4):
            errors.append(
                f"[{jid}][{cid}] bias_flag=true but adj({adj}) < norm({norm})"
            )

        # ── 8. If bias_flag True → boost exactly +0.05 (capped at 1.0) ─
        if flag is True:
            expected = round(min(norm + 0.05, 1.0), 2)
            if round(adj, 2) != expected:
                errors.append(
                    f"[{jid}][{cid}] bias_flag=true: expected adj={expected} "
                    f"but got {adj}"
                )

        # ── 9. If bias_flag False → adjusted == normalized ─────────────
        if flag is False and round(adj, 2) != round(norm, 2):
            errors.append(
                f"[{jid}][{cid}] bias_flag=false but adj({adj}) != norm({norm})"
            )

    # ── 10. Ranks are unique and sequential starting at 1 ─────────────
    ranks = [c.get("rank") for c in candidates]
    expected_ranks = list(range(1, len(ranks) + 1))
    if sorted(ranks) != expected_ranks:
        errors.append(
            f"[{jid}] Ranks not sequential/unique: {ranks}"
        )

    # ── 11. Ranking sorted by adjusted_score DESC ──────────────────────
    adj_scores = [c.get("adjusted_score", 0) for c in candidates]
    if adj_scores != sorted(adj_scores, reverse=True):
        errors.append(
            f"[{jid}] Candidates not sorted by adjusted_score DESC: {adj_scores}"
        )

    # ── 12. Dynamic bias_detected validation ───────────────────────────
    norm_scores = [c.get("normalized_score", 0) for c in candidates]
    if norm_scores:
        avg_n    = round(sum(norm_scores) / len(norm_scores), 2)
        max_n    = round(max(norm_scores), 2)
        var_i    = round(max_n - avg_n, 2)
        expected_bias = (avg_n < 0.4) or (var_i > 0.5)
        actual_bias   = ba.get("bias_detected")
        if actual_bias != expected_bias:
            errors.append(
                f"[{jid}] bias_detected={actual_bias} but rule gives {expected_bias} "
                f"(avg={avg_n}, var={var_i})"
            )

# ── Summary ────────────────────────────────────────────────────────────────
total_jobs = len(data)
print(f"Jobs validated: {total_jobs}")
print(f"Errors found  : {len(errors)}")
print()

if errors:
    print("=== FAILURES ===")
    for e in errors:
        print(" FAIL:", e)
else:
    print("=== ALL CHECKS PASSED ===")
    print("Output is 100% correct for Day 15.")
