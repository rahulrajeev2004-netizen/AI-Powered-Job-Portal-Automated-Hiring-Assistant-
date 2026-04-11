import json
import os
import time
import gc
from typing import List, Dict, Any
from ats_engine_optimizer import ATSEngineOptimizer

def run_large_batch():
    print("Starting production run for 85 JDs...")
    
    # 1. Load JDs
    jd_summary_path = "data/processed/jd_parsed_outputs/SAMPLE_SUMMARY.json"
    if not os.path.exists(jd_summary_path):
        print(f"Error: {jd_summary_path} not found.")
        return
        
    with open(jd_summary_path, "r", encoding="utf-8") as f:
        all_jds = json.load(f)
    # Deduplication removed per user request to process all 85 JDs
    
    # 2. Load Resumes
    resumes_dir = "data/samples/labeled"
    resumes = []
    for filename in os.listdir(resumes_dir):
        if filename.endswith("_segmented.json"):
            with open(os.path.join(resumes_dir, filename), "r", encoding="utf-8") as f:
                res_data = json.load(f)
                res_data["name"] = filename.replace("_segmented.json", "")
                resumes.append(res_data)
    
    print(f"Loaded {len(all_jds)} JDs and {len(resumes)} resumes.")
    
    optimizer = ATSEngineOptimizer()
    full_results = []
    
    start_time = time.time()
    
    # 3. Process each JD
    for i, jd in enumerate(all_jds):
        jd_title = jd.get("job_title", f"Job_{i}")
        print(f"[{i+1}/{len(all_jds)}] Processing: {jd_title}...")
        
        try:
            # The optimizer expect a dictionary with 'job_title' and 'requirements'
            # SAMPLE_SUMMARY has 'job_title', 'requirements', etc.
            result = optimizer.process_pipeline(jd, resumes)
            full_results.append(result)
        except Exception as e:
            print(f"Error processing {jd_title}: {e}")
            continue
            
        # Periodic Memory Cleanup
        if i % 10 == 0:
            gc.collect()

    end_time = time.time()
    total_elapsed = end_time - start_time
    
    # 4. Save Consolidated Report
    output_path = "outputs/production_85_jd_report.json"
    os.makedirs("outputs", exist_ok=True)
    
    final_output = {
        "batch_id": "BATCH_PROD_20260411_85JD",
        "processed_count": len(full_results),
        "total_time_seconds": total_elapsed,
        "results": full_results,
        "summary_performance": optimizer.perf_tracker.get_report(),
        "summary_stability": optimizer.stability_tracker.get_report()
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
        
    print(f"\nBatch processing complete!")
    print(f"Total time: {total_elapsed:.2f} seconds")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    run_large_batch()
