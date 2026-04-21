import os
import json
import uuid
import glob
from interview_ai.pipeline import AIVoiceScreeningPipeline

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from parsers.pdf_parser import extract_text_from_pdf
except ImportError:
    def extract_text_from_pdf(file_path): return ""

def determine_role(text, filename):
    text_lower = text.lower()
    filename_lower = filename.lower()
    nurse_signals = ["nurse", "clinical", "hospital", "icu", "bls", "acls", "patient care", "ward"]
    sales_signals = ["sales", "b2b", "revenue", "crm", "deal", "quota", "pipeline"]
    eng_signals   = ["software", "engineer", "developer", "python", "java", "aws", "cloud",
                    "microservices", "docker", "kubernetes", "api", "backend", "frontend"]
    nurse_score = sum(1 for s in nurse_signals if s in text_lower or s in filename_lower)
    sales_score = sum(1 for s in sales_signals if s in text_lower or s in filename_lower)
    eng_score   = sum(1 for s in eng_signals   if s in text_lower or s in filename_lower)
    if nurse_score >= sales_score and nurse_score >= eng_score and nurse_score > 0:
        return "Staff Nurse"
    elif sales_score >= nurse_score and sales_score >= eng_score and sales_score > 0:
        return "Sales Executive"
    elif eng_score > 0:
        return "Software Engineer"
    else:
        # No strong signals -> default to role inferred from highest keyword count
        return "Software Engineer"

def extract_candidate_profile(text, filename):
    """Extract per-candidate salary/location signals from resume text.
    Falls back to deterministic, role-plausible values seeded from filename."""
    import re
    import hashlib
    text_lower = text.lower()

    # Deterministic seed per candidate (reproducible across runs)
    seed = int(hashlib.md5(filename.encode()).hexdigest(), 16) % 1000

    # Location: match known cities in resume text
    city_map = [
        # Indian cities
        ("bangalore", "Bangalore"), ("bengaluru", "Bangalore"),
        ("mumbai", "Mumbai"), ("delhi", "Delhi"), ("new delhi", "Delhi"),
        ("chennai", "Chennai"), ("hyderabad", "Hyderabad"), ("pune", "Pune"),
        ("kolkata", "Kolkata"), ("ahmedabad", "Ahmedabad"),
        ("thiruvananthapuram", "Thiruvananthapuram"), ("trivandrum", "Thiruvananthapuram"),
        ("kochi", "Kochi"), ("cochin", "Kochi"), ("kerala", "Kochi"),
        ("coimbatore", "Coimbatore"), ("jaipur", "Jaipur"),
        ("bhopal", "Bhopal"), ("lucknow", "Lucknow"), ("chandigarh", "Chandigarh"),
        # US cities
        ("new york", "New York"), ("san francisco", "San Francisco"),
        ("chicago", "Chicago"), ("austin", "Austin"), ("seattle", "Seattle"),
        ("boston", "Boston"), ("los angeles", "Los Angeles"), ("dallas", "Dallas"),
        # Others
        ("london", "London"), ("dubai", "Dubai"), ("singapore", "Singapore")
    ]

    # Role-specific fallback salary pools (monthly USD / USD-equivalent)
    # Used only when no salary keyword is found in resume
    nurse_salaries   = [3800, 4200, 4500, 4800, 5000, 5200, 5500, 5800, 6000, 6500]
    eng_salaries     = [4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000]
    sales_salaries   = [4000, 4500, 5000, 5200, 5500, 5800, 6000, 6500, 7000, 7500]
    default_salaries = [4500, 5000, 5200, 5500, 5800, 6000, 6200, 6500, 6800, 7000]

    # Detect role from text to pick salary pool
    eng_score   = sum(1 for s in ["software", "engineer", "developer", "python", "aws", "cloud"]
                      if s in text_lower)
    nurse_score = sum(1 for s in ["nurse", "clinical", "hospital", "icu", "patient"]
                      if s in text_lower)
    sales_score = sum(1 for s in ["sales", "b2b", "revenue", "crm"]
                      if s in text_lower)

    if nurse_score >= max(eng_score, sales_score) and nurse_score > 0:
        salary_pool = nurse_salaries
        notice_pool = [30, 30, 30, 45, 60, 30, 45, 30, 60, 30]
    elif sales_score >= max(nurse_score, eng_score) and sales_score > 0:
        salary_pool = sales_salaries
        notice_pool = [30, 45, 30, 60, 30, 45, 30, 30, 45, 60]
    elif eng_score > 0:
        salary_pool = eng_salaries
        notice_pool = [30, 60, 90, 30, 60, 45, 30, 90, 60, 30]
    else:
        salary_pool = default_salaries
        notice_pool = [30, 45, 30, 60, 30, 30, 45, 60, 30, 45]

    # Deterministic picks
    salary_curr = salary_pool[seed % len(salary_pool)]
    salary_exp  = round(salary_curr * (1.18 + (seed % 5) * 0.02))  # 18-26% hike
    notice_days = notice_pool[seed % len(notice_pool)]
    location    = "New York"  # default fallback

    # Override defaults from resume text if signals found
    for city_key, city_val in city_map:
        if city_key in text_lower:
            location = city_val
            break

    # Salary: strict extraction — keyword must immediately precede a number
    sal_matches = re.findall(
        r'\b(?:salary|ctc|compensation|package|earn|lpa)\b[^\d\n]{0,15}(\d+[\d,]*)',
        text_lower
    )
    if sal_matches:
        try:
            raw_val = int(sal_matches[0].replace(',', ''))
            if 5 <= raw_val <= 100:           # LPA range
                salary_curr = round((raw_val * 100000) / 12)
                salary_exp  = round(salary_curr * 1.20)
            elif raw_val >= 1000:             # Absolute monthly
                salary_curr = raw_val
                salary_exp  = round(salary_curr * 1.20)
            # else: implausible, keep deterministic fallback
        except:
            pass

    # Notice period: look for explicit mention in resume
    np_matches = re.findall(r'(\d+)\s*(?:day|days)\s*notice', text_lower)
    if np_matches:
        val = int(np_matches[0])
        if 0 < val <= 365:
            notice_days = val

    return {
        "location": location,
        "salary_curr": salary_curr,
        "salary_exp": salary_exp,
        "notice_days": notice_days
    }

def generate_mock_voice_answers(role, text, dataset_qbank, role_flow, profile=None):
    if profile is None:
        profile = {"location": "New York", "salary_curr": 5000, "salary_exp": 6500, "notice_days": 30}
    stt_payload = []
    text_lower = text.lower()
    
    for i, q_id in enumerate(role_flow):
        q_info = dataset_qbank.get(q_id, {})
        q_text = q_info.get("question_text", {}).get("en", "Unknown question?")
        
        conf = 0.90 + (0.1 * (hash(q_id) % 10) / 10.0)
        duration = 10.0 + (i % 5)
        
        answer_raw = ""
        if "INTRO_01" in q_id:
            answer_raw = f"Hi, I am an experienced {role}. I have been in this field for many years."
        elif "INTRO_02" in q_id:
            answer_raw = "Yes, I am currently employed but looking for better opportunities."
        elif "EDU_01" in q_id:
            if "stanford" in text_lower:
                answer_raw = "I got my Master of Science in Computer Science from Stanford University."
            else:
                answer_raw = "I hold a Bachelor's degree from the State University."
        elif "EDU_03" in q_id:
            answer_raw = "Yes, I hold a valid Nursing Council registration."
        elif "EDU_06" in q_id or "EDU_07" in q_id:
            answer_raw = "Yes, I have completed a few specialized bootcamps."
        elif "EXP_01" in q_id:
            if "ten years" in text_lower or "10 years" in text_lower:
                answer_raw = "I have over 10 years of professional experience."
            else:
                answer_raw = "I have 4.5 years of professional experience."
        elif "EXP_02" in q_id:
            answer_raw = "I have exactly 3.5 years of clinical experience in the ICU."
        elif "EXP_08" in q_id:
            answer_raw = "Once a patient was aggressive. I used de-escalation techniques and called for support."
        elif "EXP_09" in q_id or "EXP_10" in q_id:
            answer_raw = "I successfully migrated our legacy system to microservices." if "Software" in role else "I closed a major deal by demonstrating long-term ROI."
        elif "EXP_11" in q_id:
            answer_raw = "I have 3 years of experience in cloud infrastructure."
        elif "SKILL_01" in q_id:
            answer_raw = "I would rate my Python skills at an 8 out of 10."
        elif "SKILL_05" in q_id:
            answer_raw = "Yes, I have deployed containers using Docker and Kubernetes."
        elif "SKILL_06" in q_id:
            answer_raw = "My experience is primarily in B2B corporate sales."
        elif "SKILL_07" in q_id:
            answer_raw = "Yes, I hold valid BLS and ACLS certifications."
        elif "SKILL_08" in q_id:
            answer_raw = "I would immediately check their airway, start CPR if needed, and call a Code Blue while applying oxygen."
        elif "SKILL_09" in q_id:
            answer_raw = "I check database locks, index usage, and add read replicas if needed."
        elif "SKILL_10" in q_id or "SKILL_11" in q_id:
            answer_raw = "I use LinkedIn Sales Navigator to reach decision-makers directly."
        elif "LOC_01" in q_id:
            answer_raw = f"I am currently located in {profile['location']}."
        elif "LOC_02" in q_id:
            answer_raw = "Yes, I am absolutely willing to relocate for this role."
        elif "SAL_01" in q_id:
            answer_raw = f"My current take-home salary is {profile['salary_curr']} dollars."
        elif "SAL_02" in q_id:
            answer_raw = f"I am expecting around {profile['salary_exp']} dollars."
        elif "NP_01" in q_id:
            answer_raw = f"My current notice period is {profile['notice_days']} days."
        elif "NP_02" in q_id:
            answer_raw = "Yes, my notice period can be negotiated or bought out."
        else:
            answer_raw = "Yes."

        answer_raw = "Um, " + answer_raw if i % 2 == 0 else answer_raw

        stt_payload.append({
            "question_id": q_id,
            "question_text": q_text,
            "raw_transcript": {
                "text": answer_raw,
                "confidence": conf,
                "duration_seconds": duration
            }
        })
    return stt_payload

def main():
    pipeline = AIVoiceScreeningPipeline()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    dataset_path = os.path.join(project_root, "data", "output", "hr_screening_dataset.json")
    with open(dataset_path, "r", encoding='utf-8') as f:
        dataset = json.load(f)
        
    role_flows = dataset['conversation_flow']['role_based_flow']
    q_bank = {q['question_id']: q for q in dataset['question_bank']}
    
    resumes_dir = os.path.join(project_root, "data", "resumes")
    resume_files = []
    for ext in ["*.pdf", "*.txt"]:
        resume_files.extend(glob.glob(os.path.join(resumes_dir, ext)))
        
    outputs = []
    
    for r_file in resume_files:
        filename = os.path.basename(r_file)
        
        if r_file.endswith(".pdf"):
            text = extract_text_from_pdf(r_file)
        else:
            with open(r_file, "r", encoding="utf-8") as rf:
                text = rf.read()
                
        role = determine_role(text, filename)
        job_id = f"ROLE_{role.replace(' ', '_').upper()}"
        cand_id = "cand_" + uuid.uuid4().hex[:8]
        sess_id = "sess_" + uuid.uuid4().hex[:8]
        
        print(f"Processing candidate file: {filename} --> Auto-Classified as: {role}")
        
        profile = extract_candidate_profile(text, filename)
        flow = role_flows.get(role, [])
        mock_stt = generate_mock_voice_answers(role, text, q_bank, flow, profile=profile)
        
        result = pipeline.process_stt_result(
            session_id=sess_id,
            candidate_id=cand_id,
            job_id=job_id,
            raw_stt_payload=mock_stt,
            classified_role=role
        )
        
        result["candidate_file"] = filename
        result["classified_role"] = role
        outputs.append(result)

    # Cross-candidate duplicate detection (HARD DELETE)
    import hashlib
    seen_hashes = set()
    unique_outputs = []
    
    for cand in outputs:
        fingerprint_string = f"{cand['aggregate_scores']['overall_score']}_{cand['interaction_summary']['total_duration_seconds']}_{cand['classified_role']}"
        fingerprint = hashlib.md5(fingerprint_string.encode()).hexdigest()
        
        if fingerprint not in seen_hashes:
            seen_hashes.add(fingerprint)
            unique_outputs.append(cand)
            
    outputs = unique_outputs
        
    output_path = os.path.join(project_root, "outputs", "bulk_resumes_voice_eval.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=4)
        
    print(f"\nBulk processing completed successfully. Evaluated {len(outputs)} candidates from respository.")
    print(f"Aggregated structured output saved to: {output_path}")

if __name__ == "__main__":
    main()
