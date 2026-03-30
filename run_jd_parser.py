

import os
import sys
import json
import argparse

# Force UTF-8 output on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from parsers.jd_parser import parse_jd, save_parsed_jd
from utils.logger import get_logger

logger = get_logger("run_jd_parser", "logs/jd_parsing.log")

SAMPLES_PATH   = "data/samples/sample_jds.json"
OUTPUT_DIR     = "data/processed/jd_parsed_outputs"


def run_from_samples():
    logger.info("=== JD Parser Pipeline – Batch Mode ===")
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples = json.load(f)

    results = []
    for sample in samples:
        # Fallback to job_summary if raw_text is missing
        raw_text = sample.get("raw_text") or f"{sample.get('job_title', 'Job')}\n\n{sample.get('job_summary', '')}"
        if not raw_text:
            continue

        job_id = sample.get("job_id", "")
        profile = parse_jd(raw_text=raw_text, job_id=job_id)

        out_path = os.path.join(OUTPUT_DIR, f"{profile['job_id']}.json")
        save_parsed_jd(profile, out_path)
        results.append(profile)

        print(f"\n{'='*60}")
        print(f"  JD ID    : {profile['job_id']}")
        print(f"  Title    : {profile['job_title']}")
        print(f"  Company  : {profile['company_name']}")
        print(f"  Work Type: {profile['location'].get('work_type', 'N/A')}")
        exp = profile['requirements'].get('experience', {})
        print(f"  Exp (min): {exp.get('min_years', 'N/A')} years  |  Field: {exp.get('relevant_field', 'N/A')}")
        edu = profile['requirements'].get('education', {})
        print(f"  Education: {edu.get('min_degree', 'N/A')}  |  Preferred: {edu.get('preferred_degree', 'N/A')}")
        skills = profile['requirements']['skills']
        print(f"  Mandatory Skills: {skills['mandatory']}")
        print(f"  Preferred Skills: {skills['preferred']}")
        print(f"  Responsibilities : {len(profile['responsibilities'])} items")
        print(f"  Benefits         : {len(profile['benefits'])} items")
        print(f"  Output saved     : {out_path}")

    print(f"\n{'='*60}")
    print(f"✅  Parsed {len(results)} job descriptions successfully.")
    print(f"    Outputs saved to: {OUTPUT_DIR}/")
    logger.info(f"Pipeline complete. {len(results)} JDs processed.")
    return results


def run_from_file(jd_file_path: str):
    logger.info(f"=== JD Parser Pipeline – Single File Mode: {jd_file_path} ===")
    with open(jd_file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    profile = parse_jd(raw_text=raw_text)
    out_path = os.path.join(OUTPUT_DIR, f"{profile['job_id']}.json")
    save_parsed_jd(profile, out_path)
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    print(f"\n✅  Output saved to: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zecpath JD Parser Runner")
    parser.add_argument("--jd", type=str, default=None, help="Path to a single raw JD text file")
    args = parser.parse_args()

    if args.jd:
        run_from_file(args.jd)
    else:
        run_from_samples()
