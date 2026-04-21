import json
from datetime import datetime

def go():
    with open('outputs/bulk_resumes_voice_eval.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for c in data:
        seq = c.get('transcript', [])
        seq.sort(key=lambda x: x.get('timestamp', ''))
        
        for i in range(len(seq)):
            # Optional derivations
            if i < len(seq) - 1:
                try:
                    t1 = datetime.fromisoformat(seq[i]['timestamp'].replace('Z', '+00:00'))
                    t2 = datetime.fromisoformat(seq[i+1]['timestamp'].replace('Z', '+00:00'))
                    dur = (t2 - t1).total_seconds()
                    seq[i]['duration_seconds'] = round(dur, 2)
                except:
                    pass
            
            # Intent estimation
            qid = seq[i].get('question_id', '')
            if 'INTRO' in qid: seq[i]['intent'] = 'introduction'
            elif 'EXP' in qid: seq[i]['intent'] = 'experience'
            elif 'EDU' in qid: seq[i]['intent'] = 'education'
            elif 'SKILL' in qid: seq[i]['intent'] = 'skills'
            elif 'SAL' in qid: seq[i]['intent'] = 'salary'
            elif 'LOC' in qid: seq[i]['intent'] = 'location'
            elif 'NP' in qid: seq[i]['intent'] = 'notice_period'
            else: seq[i]['intent'] = 'other'
            
            seq[i]['noise_level'] = 'low'
            
    with open('outputs/bulk_resumes_voice_eval.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    go()
