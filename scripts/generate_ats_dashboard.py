import json
import os

def generate_dashboard(json_path, output_path):
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATS Recruitment Intelligence Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg: #f8fafc;
            --card-bg: rgba(255, 255, 255, 0.8);
            --text-main: #1e293b;
            --text-muted: #64748b;
        }

        * { margin:0; padding:0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem;
        }

        .container { max-width: 1200px; margin: 0 auto; }

        header {
            margin-bottom: 3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
            background: var(--card-bg);
            padding: 1.5rem 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }

        .brand h1 { font-size: 1.5rem; color: var(--primary); font-weight: 700; }
        .stats { display: flex; gap: 2rem; }
        .stat-item { text-align: center; }
        .stat-val { font-size: 1.25rem; font-weight: 700; display: block; }
        .stat-label { font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); }

        .job-card {
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            margin-bottom: 2rem;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.3);
        }

        .job-header {
            padding: 1.5rem 2rem;
            background: rgba(37, 99, 235, 0.05);
            border-bottom: 1px solid rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .job-title { font-size: 1.25rem; font-weight: 600; }
        .jd-id { font-size: 0.875rem; color: var(--text-muted); }

        .candidate-table {
            width: 100%;
            border-collapse: collapse;
        }

        .candidate-table th {
            text-align: left;
            padding: 1rem 2rem;
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.05em;
            background: rgba(0,0,0,0.02);
        }

        .candidate-table td {
            padding: 1.25rem 2rem;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }

        .rank { font-weight: 700; color: var(--text-muted); margin-right: 0.5rem; }
        .c-name { font-weight: 600; display: block; }
        .c-tier { font-size: 0.75rem; color: var(--text-muted); }

        .score-pill {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.875rem;
        }

        .status-pill {
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .S-Shortlist { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        .S-Review { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
        .S-Reject { background: rgba(239, 68, 68, 0.1); color: var(--danger); }

        .flags { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
        .flag { 
            font-size: 0.65rem; 
            padding: 0.1rem 0.4rem; 
            border-radius: 0.25rem; 
            font-weight: 600;
        }
        .green { background: #d1fae5; color: #065f46; }
        .red { background: #fee2e2; color: #991b1b; }

        .explanation { font-size: 0.875rem; color: var(--text-muted); max-width: 400px; line-height: 1.4; }

        .progress-bar {
            width: 100px;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            overflow: hidden;
            display: inline-block;
            vertical-align: middle;
        }
        .progress-fill { height: 100%; background: var(--primary); }

        footer { text-align: center; color: var(--text-muted); margin-top: 4rem; font-size: 0.875rem; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <h1>ATS Intel Dashboard v3.0</h1>
                <p style="color: var(--text-muted); font-size: 0.875rem;">Batch ID: {{batch_id}}</p>
            </div>
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-val">{{total_jobs}}</span>
                    <span class="stat-label">Jobs</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val">{{total_candidates}}</span>
                    <span class="stat-label">Total Applicants</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val" style="color: var(--success);">{{avg_shortlist}}%</span>
                    <span class="stat-label">Avg Shortlist</span>
                </div>
            </div>
        </header>

        {{jobs_html}}

        <footer>
            &copy; 2026 Antigravity Enterprise Recruitment Solutions. AI-Powered Precision.
        </footer>
    </div>
</body>
</html>
    """.replace("{{", "PLACEHOLDER_OPEN").replace("}}", "PLACEHOLDER_CLOSE").replace("{", "{{").replace("}", "}}").replace("PLACEHOLDER_OPEN", "{").replace("PLACEHOLDER_CLOSE", "}")

    jobs_html = ""
    total_candidates = 0
    total_shortlisted = 0

    for job in data.get("results", []):
        candidates_html = ""
        job_title = job.get("job_title", "Untitled Role")
        job_id = job.get("job_id", "N/A")
        cands = job.get("candidates", [])
        total_candidates += len(cands)
        
        for cand in cands:
            score = cand.get("final_score", 0)
            status = cand.get("status", "Review")
            if status == "Shortlist": total_shortlisted += 1
            
            green_flags = cand.get("indicators", {}).get("green_flags", [])
            red_flags = cand.get("indicators", {}).get("red_flags", [])
            
            flags_html = ""
            for gf in green_flags: flags_html += f'<span class="flag green">✔ {gf}</span>'
            for rf in red_flags: flags_html += f'<span class="flag red">✘ {rf}</span>'
            
            candidates_html += f"""
                <tr>
                    <td>
                        <div style="display:flex; align-items:center;">
                            <span class="rank">#{cand.get('rank')}</span>
                            <div>
                                <span class="c-name">{cand.get('candidate_id')}</span>
                                <span class="c-tier">{cand.get('seniority_tier')} Profile</span>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="status-pill S-{status}">{status}</span>
                    </td>
                    <td>
                        <div style="display:flex; align-items:center; gap: 0.5rem;">
                            <span style="font-weight:700; min-width: 40px;">{int(score*100)}%</span>
                            <div class="progress-bar"><div class="progress-fill" style="width: {score*100}%"></div></div>
                        </div>
                    </td>
                    <td>
                        <p class="explanation">{cand.get('explanation')}</p>
                        <div class="flags">{flags_html}</div>
                    </td>
                </tr>
            """

        jobs_html += f"""
        <div class="job-card">
            <div class="job-header">
                <div>
                    <h2 class="job-title">{job_title}</h2>
                    <span class="jd-id">{job_id}</span>
                </div>
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-val" style="font-size:1rem;">{len(cands)}</span>
                        <span class="stat-label">Applicants</span>
                    </div>
                </div>
            </div>
            <table class="candidate-table">
                <thead>
                    <tr>
                        <th>Candidate Info</th>
                        <th>Recruiter Decision</th>
                        <th>ATS score</th>
                        <th>Intelligence Summary</th>
                    </tr>
                </thead>
                <tbody>
                    {candidates_html}
                </tbody>
            </table>
        </div>
        """

    avg_shortlist = round((total_shortlisted / total_candidates * 100) if total_candidates > 0 else 0, 1)

    final_html = html_template.format(
        batch_id=data.get("batch_id", "STABLE_PROD_B1"),
        total_jobs=len(data.get("results", [])),
        total_candidates=total_candidates,
        avg_shortlist=avg_shortlist,
        jobs_html=jobs_html
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"Professional Dashboard generated at: {output_path}")

if __name__ == "__main__":
    generate_dashboard("outputs/day20_production_eval.json", "outputs/ATS_Recruiter_Dashboard.html")
