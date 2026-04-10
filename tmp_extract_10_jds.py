import json

# Define the target jobs
target_jobs = [
    "Critical Care Nurse",
    "Staff Nurse",
    "Nurse Educator",
    "Data Analyst",
    "Business Analyst",
    "ICU Nurse",
    "Pediatric Nurse",
    "Dialysis Nurse",
    "Director of Nursing",
    "School Nurse"
]

with open(r'c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\outputs\comprehensive_match_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

results = {job: {} for job in target_jobs}

for candidate, matches in report.items():
    for match in matches:
        title = match['job_title']
        if title in target_jobs:
            results[title][candidate] = match

with open(r'c:\Users\Rahul Rajeev\OneDrive\Desktop\Project Zecpath\outputs\extracted_10_jds.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print("Extraction complete.")
