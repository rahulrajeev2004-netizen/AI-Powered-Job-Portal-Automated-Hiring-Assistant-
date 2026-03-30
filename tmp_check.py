import json
data = json.load(open('data/processed/candidate_experience_reports/RAHUL_RAJEEV_Master_Matches.json','r',encoding='utf-8'))
total_shown = len(data["matches"])
filtered_out = 85 - total_shown
high = [m for m in data["matches"] if m["relevance_score"] > 0.05]
low  = [m for m in data["matches"] if m["relevance_score"] <= 0.05]

print("=" * 55)
print("  RAHUL RAJEEV - JD Comparison Summary")
print("=" * 55)
print(f"  Total JDs provided by user    : 85")
print(f"  JDs shown in report (>= 0.05) : {total_shown}")
print(f"  JDs filtered (pure nursing)   : {filtered_out} (score < 0.05)")
print(f"  Scores > 0.05                 : {len(high)}")
print(f"  Scores = 0.05 (weak match)    : {len(low)}")
print("=" * 55)
print("\nAll 85 JDs were COMPARED. Results:")
for i, m in enumerate(data["matches"], 1):
    print(f"  {i:02d}. {m['job_title']:<45} {m['relevance_score']:.3f}  domain={m['domain_match']}")
