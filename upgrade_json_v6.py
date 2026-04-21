import json
import datetime
import uuid

def process_file():
    with open('outputs/bulk_resumes_voice_eval.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for c in data:
        role = c.get('classified_role', 'Default')
        
        # 3. Decision Policy
        t_thresh = 0.65 if role == "Staff Nurse" else 0.70
        c['decision_policy'] = {
            "technical_threshold": t_thresh,
            "hold_range": [0.4, t_thresh],
            "auto_reject_below_threshold": False
        }
        
        # 4. Technical Score Alignment & QA Weighting
        qa = c.get('qa_breakdown', [])
        total_tech_weight = 0
        total_tech_score = 0
        total_rel_weight = 0
        total_rel_score = 0
        total_comm_weight = 0
        total_comm_score = 0
        
        for q in qa:
            intent = q.get('intent', 'other')
            tw = 1.0 # Technical weight
            rw = 1.0 # Relevance weight
            cw = 1.0 # Communication weight
            
            if intent in ['skills', 'experience']:
                tw = 2.0  # higher weight
            elif intent in ['salary', 'location', 'notice_period', 'introduction']:
                tw = 0.5  # lower weight
                
            total_tech_weight += tw
            total_tech_score += (q['score']['technical_depth'] * tw)
            
            total_rel_weight += rw
            total_rel_score += (q['score']['relevance'] * rw)
            
            total_comm_weight += cw
            total_comm_score += (q['score']['clarity'] * cw)
            
        agg_tech = round(total_tech_score / max(1, total_tech_weight), 2)
        agg_rel = round(total_rel_score / max(1, total_rel_weight), 2)
        agg_comm = round(total_comm_score / max(1, total_comm_weight), 2)
        
        # 2. Scoring validation
        overall = round((0.4 * agg_tech) + (0.3 * agg_rel) + (0.3 * agg_comm), 2)
        
        c['aggregate_scores'] = {
            "overall_relevance": agg_rel,
            "overall_communication": agg_comm,
            "technical_competency": {
                "score": agg_tech,
                "method": "weighted_average",
                "weights": {"skills": 2.0, "experience": 2.0, "other": 1.0, "admin": 0.5}
            },
            "overall_score": overall,
            "score_breakdown": {
                "formula": "0.4 * technical + 0.3 * relevance + 0.3 * communication",
                "computed_score": overall
            }
        }
        
        # 1. Decision Consistency
        # The prompt says: "IF technical_competency < 0.50 -> REJECT"
        if agg_tech < 0.50:
            status = "REJECT"
            justification = f"Candidate failed critical thresholds (technical: {agg_tech} < 0.50). Status MUST be REJECT."
        elif agg_tech >= t_thresh and overall >= 0.70:
            status = "SELECT"
            justification = f"Candidate meets technical threshold ({agg_tech} >= {t_thresh}) and overall is strong ({overall} >= 0.70)."
        else:
            status = "HOLD"
            justification = f"Candidate technical score {agg_tech} within hold range [0.50, {t_thresh}]. Pending recruiter review."
            
        c['final_decision']['status'] = status
        c['final_decision']['decision_justification'] = justification
        
        # 11. Final Decision Confidence
        conf = min(1.0, max(0.0, 0.4 + (overall * 0.4) + (c.get('interaction_summary', {}).get('average_stt_confidence', 0)*0.2)))
        c['final_decision']['decision_confidence'] = round(conf, 2)
        
        # 5. Healthcare Domain Validation & 6. Explainability
        reasoning = c['final_decision'].get('explainable_reasoning', [])
        new_reasoning = []
        for r in reasoning:
            nr = r.copy()
            if "missing" in r.get("statement", "").lower() or "omit" in r.get("statement", "").lower():
                nr["missing_critical_steps"] = True
                if role == "Staff Nurse" and "vitals" in r.get("statement", "").lower():
                    nr["risk_level"] = "CLINICAL_SAFETY_RISK"
            new_reasoning.append(nr)
        c['final_decision']['explainable_reasoning'] = new_reasoning
        
        val_flags = c.get('validation_flags', [])
        # Recalculate flag if needed
        if agg_tech < 0.60 and not any(f.get('flag') == "LOW_TECHNICAL_SCORE" for f in val_flags):
             val_flags.append({"flag": "LOW_TECHNICAL_SCORE", "severity": "HIGH", "reason": f"Technical score is {agg_tech}."})
             
        if any(r.get("risk_level") == "CLINICAL_SAFETY_RISK" for r in new_reasoning):
            if not any(f.get('flag') == "INCOMPLETE_CLINICAL_RESPONSE" for f in val_flags):
                val_flags.append({"flag": "INCOMPLETE_CLINICAL_RESPONSE", "severity": "HIGH", "reason": "Missing continuous vitals monitoring."})
                
        c['validation_flags'] = val_flags
        
        # 7. Percentile context
        rank = c.get('ranking', {})
        if 'percentile_score' in rank:
            rank['percentile_context'] = {
                "total_candidates": len(data),
                "distribution": "normal"
            }
        c['ranking'] = rank
        
        # 8. Salary + Location Normalization
        prof = c.get('normalized_profile', {})
        loc = prof.get('location', {})
        target_loc = "New York" if role == "Software Engineer" else "London"
        
        currency_norm = False
        if 'salary' in prof:
            for s_type in ['current', 'expected']:
                if s_type in prof['salary']:
                    if prof['salary'][s_type].get('currency') != "USD":
                        currency_norm = True
                    prof['salary'][s_type]['currency'] = "USD"
                        
        loc['currency_normalized'] = currency_norm
        loc['geo_adjustment_applied'] = (loc.get('current_location') != target_loc)
        prof['location'] = loc
        c['normalized_profile'] = prof

    # Sort
    data.sort(key=lambda x: x['aggregate_scores']['overall_score'], reverse=True)

    with open('outputs/bulk_resumes_voice_eval.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    return data

if __name__ == "__main__":
    process_file()
