

import os
import re
import sys
import json
import argparse

# Force UTF-8 output on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from parsers.jd_parser import parse_jd, save_parsed_jd
from utils.logger import get_logger

logger = get_logger("split_and_parse_jds", "logs/jd_parsing.log")

OUTPUT_DIR = "data/processed/jd_parsed_outputs"

# Matches lines like:  "1. Staff Nurse (Registered Nurse - RN)"
#                      "25. Endocrinology Nurse"
SPLIT_PATTERN = re.compile(r"^\s*(\d{1,3})\.\s+(.+)$")


def split_jd_file(file_path: str) -> list[dict]:
    """
    Read a multi-JD text file and split it into individual JD blocks.
    Returns a list of dicts: {job_number, raw_title, raw_text}
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    blocks = []
    current_num = None
    current_title = ""
    current_lines = []

    for line in lines:
        stripped = line.rstrip("\r\n")
        m = SPLIT_PATTERN.match(stripped)
        if m:
            # Save previous block
            if current_num is not None and current_lines:
                blocks.append({
                    "job_number": current_num,
                    "raw_title":  current_title,
                    "raw_text":   current_title + "\n" + "\n".join(current_lines),
                })
            current_num   = int(m.group(1))
            current_title = m.group(2).strip()
            current_lines = []
        else:
            if current_num is not None:
                current_lines.append(stripped)

    # Save last block
    if current_num is not None and current_lines:
        blocks.append({
            "job_number": current_num,
            "raw_title":  current_title,
            "raw_text":   current_title + "\n" + "\n".join(current_lines),
        })

    return blocks


def run(input_path: str):
    logger.info(f"=== Split & Parse JDs from: {input_path} ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    blocks = split_jd_file(input_path)
    logger.info(f"Detected {len(blocks)} JD blocks in file.")
    print(f"\nDetected {len(blocks)} job descriptions in '{input_path}'\n")
    print(f"{'='*65}")

    all_results = []

    for block in blocks:
        job_id = f"JOB-SAMPLE-{block['job_number']:03d}"
        profile = parse_jd(
            raw_text=block["raw_text"],
            job_id=job_id,
        )

        # Override title with the clean numbered title from the file
        # (parser may not detect it from dense nursing-style text)
        if not profile["job_title"]:
            # Strip parenthetical aliases e.g. "(Registered Nurse – RN)"
            clean_title = re.sub(r"\s*\(.*?\)", "", block["raw_title"]).strip()
            profile["job_title"] = clean_title

        # Build a safe filename
        safe_title = re.sub(r"[^\w\s-]", "", profile["job_title"]).strip().replace(" ", "_")
        out_filename = f"{safe_title}.json"
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        save_parsed_jd(profile, out_path)
        all_results.append(profile)

        mandatory = profile["requirements"]["skills"]["mandatory"]
        preferred = profile["requirements"]["skills"]["preferred"]
        edu       = profile["requirements"]["education"]
        exp       = profile["requirements"]["experience"]

        print(f"  [{job_id}] {profile['job_title']}")
        print(f"    Mandatory Skills : {mandatory if mandatory else 'N/A'}")
        print(f"    Preferred Skills : {preferred if preferred else 'N/A'}")
        print(f"    Education        : {edu.get('min_degree','N/A')}")
        print(f"    Experience (min) : {exp.get('min_years','N/A')} yrs | {exp.get('relevant_field','N/A')}")
        print(f"    Responsibilities : {len(profile['responsibilities'])} items")
        print(f"    Saved to         : {out_path}")
        print(f"    {'-'*60}")

    print(f"\n[DONE] Parsed and saved {len(all_results)} JD files to: {OUTPUT_DIR}/")

    # Also write a combined summary JSON
    summary_path = os.path.join(OUTPUT_DIR, "SAMPLE_SUMMARY.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"[DONE] Combined summary: {summary_path}")
    logger.info(f"Complete. {len(all_results)} JDs saved. Summary: {summary_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split & Parse Multi-JD File")
    parser.add_argument(
        "--input", type=str,
        default="data/samples/Sample.txt",
        help="Path to the multi-JD text file"
    )
    args = parser.parse_args()
    run(args.input)
