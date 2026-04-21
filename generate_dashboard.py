"""
Generates a self-contained ATS Recruiter Dashboard HTML file
from the pipeline output JSON. No server required — opens in browser directly.
"""
import json
import webbrowser
import os

project_root = os.path.dirname(os.path.abspath(__file__))
json_path    = os.path.join(project_root, "outputs", "bulk_resumes_voice_eval.json")
out_html     = os.path.join(project_root, "outputs", "recruiter_dashboard.html")

with open(json_path, "r", encoding="utf-8") as f:
    candidates = json.load(f)

json_blob = json.dumps(candidates, indent=2)

STATUS_COLOR = {
    "SELECTED": "#00e5a0",
    "HOLD":     "#f5a623",
    "REJECTED": "#ff4d6d",
}

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ATS Recruiter Dashboard — Zecpath</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
<style>
  :root {{
    --bg-deep:    #0a0d1a;
    --bg-card:    rgba(255,255,255,0.04);
    --bg-card2:   rgba(255,255,255,0.07);
    --border:     rgba(255,255,255,0.08);
    --accent:     #6c63ff;
    --accent2:    #00e5a0;
    --text:       #e8eaf6;
    --muted:      #8892b0;
    --selected:   #00e5a0;
    --hold:       #f5a623;
    --rejected:   #ff4d6d;
    --radius:     14px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: var(--bg-deep);
    color: var(--text);
    min-height: 100vh;
  }}

  /* ── Header ── */
  header {{
    background: linear-gradient(135deg, #0d1130 0%, #1a0533 100%);
    border-bottom: 1px solid var(--border);
    padding: 28px 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .logo {{ display: flex; align-items: center; gap: 12px; }}
  .logo-icon {{
    width: 42px; height: 42px; border-radius: 10px;
    background: linear-gradient(135deg, #6c63ff, #00e5a0);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
  }}
  .logo-text h1 {{ font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }}
  .logo-text p  {{ font-size: 11px; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; }}
  .header-meta {{ text-align: right; }}
  .header-meta .run-time {{ font-size: 11px; color: var(--muted); }}
  .header-meta .candidate-count {{
    font-size: 28px; font-weight: 800;
    background: linear-gradient(90deg, #6c63ff, #00e5a0);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}

  /* ── Filter Bar ── */
  .filter-bar {{
    padding: 20px 48px;
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
  }}
  .filter-bar label {{ font-size: 12px; color: var(--muted); font-weight: 500; }}
  .filter-btn {{
    padding: 6px 16px; border-radius: 50px; border: 1px solid var(--border);
    background: var(--bg-card); color: var(--muted); font-size: 12px;
    font-family: inherit; cursor: pointer; transition: all 0.2s;
  }}
  .filter-btn:hover, .filter-btn.active {{
    background: var(--accent); color: #fff; border-color: var(--accent);
  }}
  .filter-btn.status-SELECTED.active {{ background: var(--selected); border-color: var(--selected); color: #000; }}
  .filter-btn.status-HOLD.active     {{ background: var(--hold);     border-color: var(--hold);     color: #000; }}
  .filter-btn.status-REJECTED.active {{ background: var(--rejected); border-color: var(--rejected); }}
  .search-input {{
    margin-left: auto; padding: 7px 14px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg-card);
    color: var(--text); font-family: inherit; font-size: 13px; width: 220px;
  }}
  .search-input:focus {{ outline: none; border-color: var(--accent); }}

  /* ── Stats Row ── */
  .stats-row {{
    display: flex; gap: 16px; padding: 24px 48px; flex-wrap: wrap;
  }}
  .stat-card {{
    flex: 1; min-width: 120px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 22px;
    backdrop-filter: blur(8px);
  }}
  .stat-card .stat-val {{
    font-size: 32px; font-weight: 800;
    background: linear-gradient(135deg, #6c63ff, #00e5a0);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .stat-card .stat-lbl {{ font-size: 11px; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }}

  /* ── Candidate Grid ── */
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 20px; padding: 0 48px 48px;
  }}

  /* ── Candidate Card ── */
  .card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    backdrop-filter: blur(8px);
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    border-color: rgba(108,99,255,0.4);
  }}
  .card-header {{
    display: flex; align-items: center; gap: 14px;
    padding: 20px 22px 16px;
    border-bottom: 1px solid var(--border);
  }}

  /* Score Ring */
  .score-ring {{
    flex-shrink: 0;
    position: relative; width: 64px; height: 64px;
  }}
  .score-ring svg {{ transform: rotate(-90deg); }}
  .score-ring-bg  {{ fill: none; stroke: rgba(255,255,255,0.08); stroke-width: 5; }}
  .score-ring-val {{ fill: none; stroke-width: 5; stroke-linecap: round; transition: stroke-dashoffset 0.8s ease; }}
  .score-ring-text {{
    position: absolute; inset: 0;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; line-height: 1;
  }}
  .score-ring-text span {{ font-size: 9px; color: var(--muted); font-weight: 400; }}

  .card-title {{ flex: 1; }}
  .card-title h3 {{ font-size: 15px; font-weight: 600; }}
  .card-title .role-tag {{
    display: inline-block; margin-top: 5px;
    padding: 2px 10px; border-radius: 50px;
    background: rgba(108,99,255,0.15); color: #a8a2ff;
    font-size: 11px; font-weight: 500;
  }}
  .status-badge {{
    padding: 4px 12px; border-radius: 50px; font-size: 11px; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase; flex-shrink: 0;
  }}
  .badge-SELECTED {{ background: rgba(0,229,160,0.15); color: var(--selected); border: 1px solid rgba(0,229,160,0.3); }}
  .badge-HOLD     {{ background: rgba(245,166,35,0.15); color: var(--hold);     border: 1px solid rgba(245,166,35,0.3); }}
  .badge-REJECTED {{ background: rgba(255,77,109,0.15); color: var(--rejected); border: 1px solid rgba(255,77,109,0.3); }}

  /* Card Body */
  .card-body {{ padding: 16px 22px; }}

  .profile-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px; margin-bottom: 14px;
  }}
  .profile-item .lbl {{ font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; }}
  .profile-item .val {{ font-size: 13px; font-weight: 500; margin-top: 2px; }}

  /* Score Bars */
  .score-bars {{ display: flex; flex-direction: column; gap: 7px; margin-bottom: 14px; }}
  .bar-row {{ display: flex; align-items: center; gap: 8px; }}
  .bar-lbl {{ font-size: 11px; color: var(--muted); width: 90px; flex-shrink: 0; }}
  .bar-track {{
    flex: 1; height: 5px; border-radius: 50px;
    background: rgba(255,255,255,0.07);
  }}
  .bar-fill {{
    height: 100%; border-radius: 50px;
    background: linear-gradient(90deg, #6c63ff, #00e5a0);
    transition: width 0.8s ease;
  }}
  .bar-val {{ font-size: 11px; color: var(--muted); width: 30px; text-align: right; flex-shrink: 0; }}

  /* Reasoning */
  .reasoning-section {{
    border-top: 1px solid var(--border); padding-top: 12px; margin-top: 2px;
  }}
  .reasoning-title {{
    font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px;
    margin-bottom: 8px;
  }}
  .reasoning-item {{
    background: rgba(108,99,255,0.08);
    border-left: 2px solid #6c63ff;
    border-radius: 0 6px 6px 0;
    padding: 8px 10px;
    font-size: 12px; line-height: 1.5;
    margin-bottom: 6px;
    color: #c5c8e0;
  }}
  .reasoning-item .qid {{
    font-size: 10px; color: #6c63ff; font-weight: 600; margin-bottom: 2px;
  }}

  /* Risk Flags */
  .risk-flags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
  .risk-flag {{
    display: flex; align-items: center; gap: 5px;
    background: rgba(255,77,109,0.1); border: 1px solid rgba(255,77,109,0.2);
    border-radius: 6px; padding: 4px 8px; font-size: 11px; color: #ff8fa3;
  }}
  .risk-flag::before {{ content: '⚠'; font-size: 10px; }}

  /* Rank Badge */
  .rank-badge {{
    font-size: 10px; color: var(--muted);
    margin-top: 8px; text-align: right;
  }}
  .rank-badge strong {{ color: var(--accent2); }}

  /* Expand toggle */
  .expand-btn {{
    width: 100%; background: none; border: none; border-top: 1px solid var(--border);
    padding: 10px; color: var(--muted); font-size: 11px; font-family: inherit;
    cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;
    transition: color 0.2s;
  }}
  .expand-btn:hover {{ color: var(--accent); }}
  .expand-section {{ display: none; }}
  .expand-section.open {{ display: block; }}

  /* QA Table */
  .qa-table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 6px; }}
  .qa-table th {{
    text-align: left; padding: 6px 10px;
    background: rgba(255,255,255,0.04); color: var(--muted);
    font-weight: 500; font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px;
  }}
  .qa-table td {{ padding: 7px 10px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: top; }}
  .qa-table tr:last-child td {{ border-bottom: none; }}
  .qa-table .qid-cell {{ color: #6c63ff; font-weight: 600; white-space: nowrap; }}
  .qa-table .answer-cell {{ color: #c5c8e0; line-height: 1.4; }}
  .depth-chip {{
    display: inline-block; padding: 1px 7px; border-radius: 50px;
    font-size: 10px; font-weight: 600;
  }}
  .depth-hi  {{ background: rgba(0,229,160,0.15); color: var(--selected); }}
  .depth-mid {{ background: rgba(245,166,35,0.15); color: var(--hold); }}
  .depth-lo  {{ background: rgba(255,77,109,0.15); color: var(--rejected); }}

  /* No results */
  .no-results {{
    grid-column: 1/-1; text-align: center;
    padding: 60px; color: var(--muted);
  }}

  /* Responsive */
  @media (max-width: 600px) {{
    header, .filter-bar, .stats-row, .grid {{ padding-left: 16px; padding-right: 16px; }}
  }}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">⚡</div>
    <div class="logo-text">
      <h1>Zecpath ATS</h1>
      <p>Recruiter Intelligence Dashboard</p>
    </div>
  </div>
  <div class="header-meta">
    <div class="candidate-count" id="visibleCount">—</div>
    <div class="run-time">candidates evaluated</div>
  </div>
</header>

<div class="filter-bar">
  <label>STATUS</label>
  <button class="filter-btn active" onclick="setFilter('status','ALL',this)" id="f-all">All</button>
  <button class="filter-btn status-SELECTED" onclick="setFilter('status','SELECTED',this)">✅ Selected</button>
  <button class="filter-btn status-HOLD"     onclick="setFilter('status','HOLD',this)">⏳ Hold</button>
  <button class="filter-btn status-REJECTED" onclick="setFilter('status','REJECTED',this)">❌ Rejected</button>
  <label style="margin-left:16px">ROLE</label>
  <button class="filter-btn active" onclick="setFilter('role','ALL',this)" id="f-role-all">All Roles</button>
  <button class="filter-btn" onclick="setFilter('role','Staff Nurse',this)">🏥 Nurse</button>
  <button class="filter-btn" onclick="setFilter('role','Software Engineer',this)">💻 Engineer</button>
  <button class="filter-btn" onclick="setFilter('role','Sales Executive',this)">📈 Sales</button>
  <input class="search-input" id="searchInput" placeholder="🔍  Search candidate or ID..." oninput="render()"/>
</div>

<div class="stats-row" id="statsRow"></div>
<div class="grid" id="grid"></div>

<script>
const DATA = {json_blob};

let filters = {{ status: 'ALL', role: 'ALL' }};

function setFilter(type, val, btn) {{
  filters[type] = val;
  // Reset sibling buttons
  const group = btn.parentElement.querySelectorAll(
    type === 'status'
      ? '.filter-btn:not([onclick*="role"])'
      : '.filter-btn[onclick*="role"]'
  );
  group.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  render();
}}

function scoreColor(s) {{
  if (s >= 0.75) return '#00e5a0';
  if (s >= 0.65) return '#f5a623';
  return '#ff4d6d';
}}

function depthChip(v) {{
  if (v >= 0.7) return `<span class="depth-chip depth-hi">${{(v*100).toFixed(0)}}%</span>`;
  if (v >= 0.55) return `<span class="depth-chip depth-mid">${{(v*100).toFixed(0)}}%</span>`;
  return `<span class="depth-chip depth-lo">${{(v*100).toFixed(0)}}%</span>`;
}}

function buildRing(score) {{
  const r = 26, circ = 2 * Math.PI * r;
  const offset = circ - score * circ;
  const col = scoreColor(score);
  return `
    <div class="score-ring">
      <svg viewBox="0 0 64 64" width="64" height="64">
        <circle class="score-ring-bg" cx="32" cy="32" r="${{r}}"/>
        <circle class="score-ring-val" cx="32" cy="32" r="${{r}}"
          stroke="${{col}}"
          stroke-dasharray="${{circ}}"
          stroke-dashoffset="${{offset}}"/>
      </svg>
      <div class="score-ring-text">
        ${{(score*100).toFixed(0)}}<span>%</span>
      </div>
    </div>`;
}}

function getFiltered() {{
  const q = document.getElementById('searchInput').value.toLowerCase();
  return DATA.filter(c => {{
    if (filters.status !== 'ALL' && c.final_decision.status !== filters.status) return false;
    if (filters.role   !== 'ALL' && c.classified_role !== filters.role) return false;
    if (q) {{
      const hay = (c.application.candidate_id + c.classified_role + c.candidate_file).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
}}

function renderStats(visible) {{
  const total    = visible.length;
  const selected = visible.filter(c => c.final_decision.status === 'SELECTED').length;
  const hold     = visible.filter(c => c.final_decision.status === 'HOLD').length;
  const rejected = visible.filter(c => c.final_decision.status === 'REJECTED').length;
  const avgScore = total ? (visible.reduce((a,c) => a + c.aggregate_scores.overall_score, 0) / total) : 0;

  document.getElementById('statsRow').innerHTML = `
    <div class="stat-card"><div class="stat-val">${{total}}</div><div class="stat-lbl">Total</div></div>
    <div class="stat-card"><div class="stat-val" style="background:linear-gradient(135deg,#00e5a0,#00b37d);-webkit-background-clip:text">${{selected}}</div><div class="stat-lbl">Selected</div></div>
    <div class="stat-card"><div class="stat-val" style="background:linear-gradient(135deg,#f5a623,#d4850a);-webkit-background-clip:text;-webkit-text-fill-color:transparent">${{hold}}</div><div class="stat-lbl">Hold</div></div>
    <div class="stat-card"><div class="stat-val" style="background:linear-gradient(135deg,#ff4d6d,#c0002a);-webkit-background-clip:text;-webkit-text-fill-color:transparent">${{rejected}}</div><div class="stat-lbl">Rejected</div></div>
    <div class="stat-card"><div class="stat-val">${{(avgScore*100).toFixed(1)}}%</div><div class="stat-lbl">Avg Score</div></div>
  `;
}}

function cardHTML(c, idx) {{
  const s  = c.aggregate_scores;
  const p  = c.normalized_profile;
  const fd = c.final_decision;
  const dt = c.decision_trace || {{}};
  const rk = c.ranking || {{}};
  const rf = c.risk_flags || [];
  const status = fd.status;

  const reasons = (fd.explainable_reasoning || []).slice(0,3).map(r =>
    `<div class="reasoning-item"><div class="qid">${{r.evidence_question_id}} · conf ${{(r.confidence||0).toFixed(2)}}</div>${{r.statement}}</div>`
  ).join('');

  const riskHTML = rf.map(f => `<div class="risk-flag">${{f}}</div>`).join('');

  const qaRows = (c.qa_breakdown || []).map(qa => {{
    const td = qa.score ? qa.score.technical_depth : 0;
    return `<tr>
      <td class="qid-cell">${{qa.question_id}}</td>
      <td class="answer-cell">${{(qa.answer_normalized||'').slice(0,90)}}${{(qa.answer_normalized||'').length>90?'…':''}}</td>
      <td>${{depthChip(td)}}</td>
    </tr>`;
  }}).join('');

  const rankLine = rk.rank
    ? `<div class="rank-badge">Rank <strong>#${{rk.rank}}</strong> of ${{rk.total_candidates}} in ${{rk.domain||c.application.job_id}}</div>`
    : '';

  const drivingFactors = (dt.driving_factors||[]).join(', ') || '—';

  return `
<div class="card" id="card-${{idx}}">
  <div class="card-header">
    ${{buildRing(s.overall_score)}}
    <div class="card-title">
      <h3>${{c.candidate_file || c.application.candidate_id}}</h3>
      <span class="role-tag">${{c.classified_role}}</span>
    </div>
    <span class="status-badge badge-${{status}}">${{status}}</span>
  </div>

  <div class="card-body">
    <div class="profile-grid">
      <div class="profile-item">
        <div class="lbl">📍 Location</div>
        <div class="val">${{p.location?.current_location || '—'}}</div>
      </div>
      <div class="profile-item">
        <div class="lbl">🔄 Relocate</div>
        <div class="val">${{p.location?.willing_to_relocate ? '✅ Yes' : '❌ No'}}</div>
      </div>
      <div class="profile-item">
        <div class="lbl">💰 Current Sal</div>
        <div class="val">${{p.salary?.current?.amount || '—'}} USD/mo</div>
      </div>
      <div class="profile-item">
        <div class="lbl">💰 Expected</div>
        <div class="val">${{p.salary?.expected?.amount || '—'}} USD/mo</div>
      </div>
      <div class="profile-item">
        <div class="lbl">📅 Notice</div>
        <div class="val">${{p.notice_period?.days || '—'}}d · ${{p.notice_period?.negotiable ? 'Negotiable' : 'Fixed'}}</div>
      </div>
      <div class="profile-item">
        <div class="lbl">🎯 Driving</div>
        <div class="val" style="font-size:11px;color:#8892b0">${{drivingFactors}}</div>
      </div>
    </div>

    <div class="score-bars">
      <div class="bar-row">
        <span class="bar-lbl">Technical</span>
        <div class="bar-track"><div class="bar-fill" style="width:${{s.technical_competency*100}}%"></div></div>
        <span class="bar-val">${{(s.technical_competency*100).toFixed(0)}}%</span>
      </div>
      <div class="bar-row">
        <span class="bar-lbl">Relevance</span>
        <div class="bar-track"><div class="bar-fill" style="width:${{s.overall_relevance*100}}%"></div></div>
        <span class="bar-val">${{(s.overall_relevance*100).toFixed(0)}}%</span>
      </div>
      <div class="bar-row">
        <span class="bar-lbl">Communication</span>
        <div class="bar-track"><div class="bar-fill" style="width:${{s.overall_communication*100}}%"></div></div>
        <span class="bar-val">${{(s.overall_communication*100).toFixed(0)}}%</span>
      </div>
    </div>

    ${{reasons ? `<div class="reasoning-section"><div class="reasoning-title">🧠 Reasoning</div>${{reasons}}</div>` : ''}}
    ${{riskHTML ? `<div class="risk-flags">${{riskHTML}}</div>` : ''}}
    ${{rankLine}}
  </div>

  <button class="expand-btn" onclick="toggleExpand(${{idx}})">
    <span id="expand-icon-${{idx}}">▼</span> Full QA Breakdown
  </button>
  <div class="expand-section" id="expand-${{idx}}">
    <div style="padding: 0 22px 16px">
      <table class="qa-table">
        <thead><tr><th>Q ID</th><th>Answer</th><th>Depth</th></tr></thead>
        <tbody>${{qaRows}}</tbody>
      </table>
    </div>
  </div>
</div>`;
}}

function toggleExpand(idx) {{
  const sec  = document.getElementById('expand-' + idx);
  const icon = document.getElementById('expand-icon-' + idx);
  const open = sec.classList.toggle('open');
  icon.textContent = open ? '▲' : '▼';
}}

function render() {{
  const visible = getFiltered();
  document.getElementById('visibleCount').textContent = visible.length;
  renderStats(visible);
  const grid = document.getElementById('grid');
  if (!visible.length) {{
    grid.innerHTML = '<div class="no-results">🔍 No candidates match your filters.</div>';
    return;
  }}
  grid.innerHTML = visible.map((c,i) => cardHTML(c, i)).join('');
}}

render();
</script>
</body>
</html>"""

with open(out_html, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard generated: {out_html}")
webbrowser.open(f"file:///{out_html.replace(os.sep, '/')}")
