import json

with open('outputs/bulk_resumes_voice_eval.json', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total candidates: {len(data)}\n")

for c in data:
    cid = c['application']['candidate_id']
    role = c['classified_role']
    prof = c['normalized_profile']
    loc = prof['location']
    sal = prof['salary']
    np_ = prof['notice_period']
    score = c['aggregate_scores']['overall_score']
    status = c['final_decision']['status']

    print(f"=== {cid} | {role} ===")
    print(f"  Score      : {score}  Status: {status}")
    print(f"  Location   : {loc['current_location']} (conf={loc['confidence']}, relocate={loc['willing_to_relocate']})")
    print(f"  Salary Curr: {sal['current']['amount']} USD (conf={sal['current']['confidence']})")
    print(f"  Salary Exp : {sal['expected']['amount']} USD (conf={sal['expected']['confidence']})")
    print(f"  Notice     : {np_['days']}d  negotiable={np_['negotiable']} (conf={np_['confidence']})")

    qa_map = {qa['question_id']: qa['answer_normalized'] for qa in c['qa_breakdown']}
    loc01 = qa_map.get('Q_LOC_01', 'NOT FOUND')[:80]
    loc02 = qa_map.get('Q_LOC_02', 'NOT FOUND')[:80]
    sal01 = qa_map.get('Q_SAL_01', 'NOT FOUND')[:80]
    sal02 = qa_map.get('Q_SAL_02', 'NOT FOUND')[:80]
    np01  = qa_map.get('Q_NP_01',  'NOT FOUND')[:80]

    print(f"  LOC_01 ans : {loc01}")
    print(f"  LOC_02 ans : {loc02}")
    print(f"  SAL_01 ans : {sal01}")
    print(f"  SAL_02 ans : {sal02}")
    print(f"  NP_01  ans : {np01}")

    # Consistency check
    issues = []
    if sal['current']['amount'] == 0:
        issues.append("FAIL: current salary not extracted")
    if sal['expected']['amount'] == 0:
        issues.append("FAIL: expected salary not extracted")
    if loc['current_location'] == 'Unknown':
        issues.append("FAIL: location not extracted")
    if np_['days'] == 0:
        issues.append("FAIL: notice period not extracted")
    if "willing" not in loc02.lower() and "yes" not in loc02.lower():
        issues.append("WARN: LOC_02 may not be a relocation intent answer")
    if issues:
        for issue in issues:
            print(f"  ** {issue}")
    else:
        print("  [OK] All profile fields correctly extracted from answers")
    print()
