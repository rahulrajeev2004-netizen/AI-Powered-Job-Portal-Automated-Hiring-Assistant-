"""
run_transcript_processor.py
-----------------------------
Production-Grade Runner for ATS Scoring Calibration Engine (v6.5)

Usage:
    python run_transcript_processor.py
"""

import json
import os
import sys
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from interview_ai.transcript_processor import BulkTranscriptProcessor

# ── Config ────────────────────────────────────────────────────────────────────
INPUT_FILE  = os.path.join(PROJECT_ROOT, "outputs", "bulk_resumes_voice_eval.json")
OUTPUT_DIR  = os.path.join(PROJECT_ROOT, "outputs")
DATE_STAMP  = datetime.now().strftime("%Y%m%d")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"cleaned_transcripts_{DATE_STAMP}.json")

def print_banner():
    print("=" * 65)
    print("   ATS SCORING CALIBRATION ENGINE (v6.5)  —  Project Zecpath")
    print("=" * 65)
    print(f"  Input  : {INPUT_FILE}")
    print(f"  Output : {OUTPUT_FILE}")
    print(f"  Run At : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

def print_session_summary(idx: int, res: dict):
    profile = res.get("candidate_profile", {})
    summary = res.get("session_summary", {})
    agg     = res.get("aggregated_profile", {})
    
    name    = profile.get("candidate_name", "Unknown")
    role    = agg.get("primary_role", "Unknown Role")[:20]
    score   = summary.get("final_score", 0.0)
    decision = summary.get("decision", "REJECT")
    
    print(f"  [{idx:02d}] {name:<25} | {role:<20} | Score: {score:.3f} | {decision}")

def main():
    print_banner()

    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    print(f"\n[INFO] Loaded {len(raw_records)} records.\n")

    processor = BulkTranscriptProcessor()
    processed_sessions = []

    print("  Processing Sessions:")
    print("  " + "-" * 85)

    for idx, record in enumerate(raw_records, start=1):
        try:
            result = processor.process_session(record)
            processed_sessions.append(result)
            print_session_summary(idx, result)
        except Exception as exc:
            print(f"  [{idx:02d}] FAILED: {exc}")

    print("  " + "-" * 85)

    output_envelope = {
        "metadata": {
            "engine": "ATS Scoring Calibration Engine v6.5",
            "project": "Project Zecpath",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_file": os.path.basename(INPUT_FILE),
            "schema_version": "transcript_processed_v6.5_calibrated"
        },
        "sessions": processed_sessions
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_envelope, f, indent=4, ensure_ascii=False)

    print(f"\n[DONE] Processed {len(processed_sessions)} candidate sessions.")
    print(f"  Output saved to: {OUTPUT_FILE}\n")
    print("=" * 65)

if __name__ == "__main__":
    main()
