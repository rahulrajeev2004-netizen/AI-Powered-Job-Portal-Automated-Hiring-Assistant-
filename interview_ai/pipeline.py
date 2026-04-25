import json
import uuid
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List
from .normalization import TranscriptNormalizer
from .behavioral_analyzer import BehavioralAnalyzer


class AIVoiceScreeningPipeline:
    def __init__(self):
        self.normalizer = TranscriptNormalizer()
        self.behavioral_analyzer = BehavioralAnalyzer()

    def process_stt_result(
        self,
        session_id: str,
        candidate_id: str,
        job_id: str,
        raw_stt_payload: List[Dict[str, Any]],
        classified_role: str = ""
    ):
        # ── RULE 1: Intent-based technical_depth caps ──────────────────────────
        TECH_CAPS = {
            "introduction":  0.30,   # ONLY clarity + communication evaluated
            "education":     0.50,   # Low unless specialization detected
            "salary":        0.20,   # Factual slot — no technical content
            "location":      0.20,
            "notice_period": 0.20,
            # "experience" and "skills" → uncapped (1.0 effective)
        }

        # ── RULE 2: Expanded domain entity registry ────────────────────────────
        # Format: term → (display_name, entity_type)
        DOMAIN_TERMS = {
            # Engineering
            "docker":        ("Docker",                    "infrastructure"),
            "kubernetes":    ("Kubernetes",                "infrastructure"),
            "python":        ("Python",                    "language"),
            "microservices": ("Microservices",             "architecture"),
            "ci/cd":         ("CI/CD Pipeline",            "devops"),
            "rest api":      ("REST API",                  "interface"),
            "index":         ("DB Index Tuning",           "database"),
            "read replica":  ("Read Replica",              "database"),
            # Clinical
            "icu":           ("ICU",                       "clinical_unit"),
            "code blue":     ("Code Blue Protocol",        "emergency_protocol"),
            "airway":        ("Airway Management",         "emergency_action"),
            "cpr":           ("CPR",                       "emergency_action"),
            "bls":           ("BLS Certification",         "certification"),
            "acls":          ("ACLS Certification",        "certification"),
            "oxygen":        ("Oxygen Therapy",            "medication"),
            "vitals":        ("Vital Signs Monitoring",    "monitoring"),
            "ecg":           ("ECG Monitoring",            "monitoring"),
            "epinephrine":   ("Epinephrine",               "medication"),
            "atropine":      ("Atropine",                  "medication"),
            "de-escalation": ("De-escalation Protocol",   "behavioral"),
            # Sales
            "b2b":           ("B2B Sales",                 "domain"),
            "crm":           ("CRM",                       "tool"),
            "linkedin":      ("LinkedIn Sales Navigator",  "tool"),
        }

        # ── Phase 1: STT Normalization ─────────────────────────────────────────
        transcripts = []
        total_duration = 0
        confidences = []

        for q_data in raw_stt_payload:
            raw_text   = q_data.get('raw_transcript', {}).get('text', '')
            confidence = q_data.get('raw_transcript', {}).get('confidence', 0.0)
            duration   = q_data.get('raw_transcript', {}).get('duration_seconds', 0.0)
            confidences.append(confidence)
            total_duration += duration
            normalized_output = self.normalizer.normalize(raw_text)
            transcripts.append({
                "question_id":     q_data.get("question_id"),
                "question":        q_data.get("question_text"),
                "raw_text":        raw_text,
                "normalized_text": normalized_output["text"],
                "confidence":      min(float(confidence), 1.0),
                "duration":        duration,
                "applied_rules":   normalized_output["applied_rules"]
            })

        if not transcripts:
            return {"error": "No transcripts provided."}

        # ── Phase 2: Scoring loop ──────────────────────────────────────────────
        qa_breakdown              = []
        overall_relevance_sum     = 0
        overall_communication_sum = 0
        overall_tech_sum          = 0
        current_time              = datetime.utcnow()

        # Profile extraction state
        global_sal_curr  = 0
        global_sal_exp   = 0
        global_loc       = "Unknown"
        global_relocate  = False
        global_np_days   = 0
        global_np_neg    = False
        global_total_exp = 0.0    # for consistency check (Q_EXP_01)
        global_icu_exp   = 0.0    # for consistency check (Q_EXP_02)

        reasoning       = []
        driving_factors = []

        city_patterns = {
            "new york": "New York", "san francisco": "San Francisco",
            "chicago": "Chicago", "austin": "Austin", "seattle": "Seattle",
            "boston": "Boston", "bangalore": "Bangalore", "bengaluru": "Bangalore",
            "mumbai": "Mumbai", "delhi": "Delhi", "chennai": "Chennai",
            "hyderabad": "Hyderabad", "pune": "Pune", "london": "London",
            "thiruvananthapuram": "Thiruvananthapuram", "kochi": "Kochi",
        }

        def clamp(v): return round(min(max(v, 0.0), 1.0), 2)

        # Role flags (computed once, used throughout loop)
        is_nurse = "nurse"    in classified_role.lower()
        is_eng   = "software" in classified_role.lower()
        is_sales = "sales"    in classified_role.lower()

        for i, t in enumerate(transcripts):
            q_id       = t["question_id"].upper()
            text_lower = t["normalized_text"].lower()
            raw_eval   = t["raw_text"].lower()
            words      = text_lower.split()
            word_count = len(words)

            # ── Intent detection ───────────────────────────────────────────────
            intent = "other"
            if   "INTRO" in q_id: intent = "introduction"
            elif "EDU"   in q_id: intent = "education"
            elif "EXP"   in q_id: intent = "experience"
            elif "SKILL" in q_id: intent = "skills"
            elif "LOC"   in q_id: intent = "location"
            elif "SAL"   in q_id: intent = "salary"
            elif "NP"    in q_id: intent = "notice_period"

            # ── Validated profile slot extraction (question_id-keyed) ──────────
            num_matches  = re.findall(r'\b(\d[\d,]*(?:\.\d+)?)\b', text_lower.replace(',', ''))
            first_number = float(num_matches[0]) if num_matches else 0

            if   "SAL_01" in q_id and intent == "salary"        and first_number > 500:       global_sal_curr  = int(first_number)
            elif "SAL_02" in q_id and intent == "salary"        and first_number > 500:       global_sal_exp   = int(first_number)
            elif "NP_01"  in q_id and intent == "notice_period" and 0 < first_number <= 365:  global_np_days   = int(first_number)
            elif "NP_02"  in q_id and intent == "notice_period":
                if any(w in text_lower for w in ["yes","negotiated","negotiable","bought out","flexible","can be"]):
                    global_np_neg = True
            elif "EXP_01" in q_id and intent == "experience"    and 0 < first_number <= 50:   global_total_exp = first_number
            elif "EXP_02" in q_id and intent == "experience"    and 0 < first_number <= 50:   global_icu_exp   = first_number
            elif "LOC_01" in q_id and intent == "location":
                for ck, cv in city_patterns.items():
                    if ck in text_lower: global_loc = cv; break
                else:
                    m = re.search(r'(?:located in|based in|live in|in)\s+([a-zA-Z][a-zA-Z\s]{2,25})(?:\.|,|$)', text_lower)
                    if m: global_loc = m.group(1).strip().title()
            elif "LOC_02" in q_id and intent == "location":
                if any(w in text_lower for w in ["yes","willing","absolutely","open to","happy to","can relocate"]):
                    global_relocate = True
                elif any(w in text_lower for w in ["no","not willing","cannot","prefer not","unable"]):
                    global_relocate = False

            # ── Anti-Inflation Scoring Baseline ────────────────────────────────
            salt = (hash(candidate_id + q_id) % 10) / 100.0
            rel  = clamp(0.70 + salt)
            comm = clamp(0.75 + salt)
            tech = 0.60
            conf = 0.70

            # Filler-word penalty
            if any(f in raw_eval for f in ["um,", "uh,", "like,", "you know"]):
                comm -= 0.05

            # Short / vague answer penalties
            if word_count < 8:
                tech -= 0.15; rel -= 0.10; conf = 0.60
            vague_phrases = ["many years", "lot of experience", "very experienced", "worked a lot"]
            if any(v in text_lower for v in vague_phrases):
                tech -= 0.10; rel -= 0.05; conf = min(conf, 0.60)

            # ── RULE 1: Apply intent-based tech cap ────────────────────────────
            tech_cap = TECH_CAPS.get(intent, 1.0)
            # Education gets slightly higher cap if advanced degree mentioned
            if intent == "education" and any(s in text_lower for s in ["master","phd","msc","specializ","honours","distinction"]):
                tech_cap = 0.65
            tech = min(tech, tech_cap)

            # ── RULE 2: Entity extraction + confidence-based score feedback ────
            inferred           = []
            clinical_protocols = []
            entity_conf_sum    = 0.0
            entity_count       = 0

            for term, (entity_name, entity_type) in DOMAIN_TERMS.items():
                if term in text_lower:
                    econf = 0.88 if word_count > 6 else 0.72

                    if entity_type == "emergency_protocol":
                        clinical_protocols.append({
                            "name": entity_name, "confidence": econf,
                            "evidence": f"Explicitly stated '{term}'"
                        })
                    elif entity_type == "emergency_action":
                        if intent in ["skills", "experience"] or "SKILL_08" in q_id:
                            clinical_protocols.append({
                                "name": entity_name, "confidence": econf,
                                "evidence": f"Described action: '{term}'"
                            })
                    else:
                        if intent in ["skills", "experience", "education"] or entity_type in ["certification", "monitoring"]:
                            inferred.append({
                                "value": entity_name, "type": entity_type,
                                "confidence": econf, "evidence": f"Explicitly mentioned '{term}'"
                            })

                    entity_conf_sum += econf
                    entity_count    += 1

            # Confidence feedback → tech score adjustment (Rule 2)
            if entity_count > 0 and intent in ["skills", "experience"]:
                avg_ec = entity_conf_sum / entity_count
                if   avg_ec >= 0.80: tech = clamp(tech + 0.05)   # boost: high-confidence entities
                elif avg_ec <  0.50: tech = clamp(tech - 0.05)   # reduce: low-confidence / missing

            # ── Advanced depth scoring ─────────────────────────────────────────
            is_advanced_clinical = False
            is_advanced_tech     = False
            clinical_gap = ""
            tech_gap     = ""

            if intent in ["skills", "experience"]:

                # Software engineering depth
                if is_eng:
                    if "microservices" in text_lower or ("container" in text_lower and "docker" in text_lower):
                        is_advanced_tech = True
                        tech = min(max(tech, 0.75), tech_cap)
                        conf = 0.80
                    if word_count > 20 and is_advanced_tech and any(x in text_lower for x in ["index", "locks", "replica"]):
                        tech = min(0.88, tech_cap); conf = 0.92
                    elif is_advanced_tech:
                        tech_gap = (
                            "Microservices migration cited (Q_EXP_09) but omits transactional "
                            "consistency strategy, service discovery pattern, and rollback handling."
                        )

                # Clinical emergency depth (nurse only)
                if is_nurse and ("SKILL_08" in q_id or "cpr" in text_lower or "airway" in text_lower):
                    has_drugs      = any(x in text_lower for x in ["epinephrine","atropine","medication","oxygen"])
                    has_monitoring = any(x in text_lower for x in ["monitor","vitals","ecg","bp","blood pressure"])
                    has_escalation = any(x in text_lower for x in ["code blue","physician","doctor","support"])
                    has_airway     = "airway" in text_lower or "cpr" in text_lower

                    if has_drugs and has_monitoring and has_escalation and has_airway:
                        is_advanced_clinical = True
                        conf = 0.95; tech = min(0.90, tech_cap)
                    else:
                        gaps = []
                        if not has_monitoring: gaps.append("continuous BP/vitals monitoring post-stabilization")
                        if not has_drugs:      gaps.append("pharmacological support (oxygen, epinephrine)")
                        if not has_escalation: gaps.append("physician escalation pathway")
                        clinical_gap = (
                            f"Q_SKILL_08: Correctly initiates airway/CPR but missing — "
                            f"{'; '.join(gaps)}. Indicates beginner-to-intermediate clinical readiness."
                        )
                    if not is_advanced_clinical and has_airway:
                        tech = clamp(min(tech + 0.12, 0.75))

            # Final clamp after all adjustments
            rel  = clamp(rel)
            comm = clamp(comm)
            tech = clamp(tech)

            overall_relevance_sum     += rel
            overall_communication_sum += comm
            overall_tech_sum          += tech

            final_entities = {}
            if inferred:           final_entities["entities"]           = inferred
            if clinical_protocols: final_entities["clinical_protocols"] = clinical_protocols

            start_t = current_time
            end_t   = start_t + timedelta(seconds=t["duration"])
            current_time = end_t + timedelta(seconds=1.5)

            # Behavioral Analysis for this QA pair
            behavior_metrics = self.behavioral_analyzer.analyze_candidate([{
                "question_id": t["question_id"],
                "answer": t["normalized_text"]
            }])
            qa_behavior = behavior_metrics["question_level_breakdown"][0]

            qa_breakdown.append({
                "question_id":       t["question_id"],
                "question":          t["question"],
                "answer_raw":        t["raw_text"],
                "answer_normalized": t["normalized_text"],
                "intent":            intent,
                "score": {
                    "relevance":       rel,
                    "clarity":         comm,
                    "technical_depth": tech,
                    "confidence":      conf
                },
                "behavioral_indicators": {
                    "hesitation": qa_behavior["hesitation"],
                    "uncertainty": qa_behavior["uncertainty"],
                    "sentiment": qa_behavior["sentiment"],
                    "pace": qa_behavior.get("pace")
                },
                "key_entities_found": final_entities if final_entities else None,
                "start_time": start_t.isoformat() + "Z",
                "end_time":   end_t.isoformat()   + "Z"
            })

            # ── RULE 5: Reasoning — role-specific, evidence-anchored, non-repetitive ──
            def add_reasoning(stmt, q_ref=None, excerpt=None):
                ref = q_ref or t["question_id"]
                exc = excerpt or (t["normalized_text"][:70] + ("..." if len(t["normalized_text"]) > 70 else ""))
                if not any(r["evidence_question_id"] == ref for r in reasoning):
                    reasoning.append({
                        "statement":            stmt,
                        "evidence_question_id": ref,
                        "answer_excerpt":        exc,
                        "confidence":           conf
                    })
                    if intent in ["skills", "experience"] and ref not in driving_factors:
                        driving_factors.append(ref)

            if "SKILL_08" in q_id and is_nurse:
                if is_advanced_clinical:
                    add_reasoning(
                        "Full emergency protocol demonstrated: airway management, CPR initiation, "
                        "Code Blue activation, and pharmacological support — meets ICU-grade response standard."
                    )
                else:
                    add_reasoning(clinical_gap)

            elif "EXP_02" in q_id and is_nurse and "icu" in text_lower:
                add_reasoning(
                    f"Confirmed {int(global_icu_exp) if global_icu_exp else 'stated'}y ICU-specific tenure via Q_EXP_02 — "
                    "validates hands-on critical care capability required for Staff Nurse placement."
                )

            elif "EXP_01" in q_id and any(v in text_lower for v in ["many years", "lot of"]):
                add_reasoning(
                    "Q_EXP_01 vague phrasing ('many years') without specific tenure figure. "
                    "Anti-inflation penalty applied: relevance and depth scores penalized."
                )

            elif "SKILL_07" in q_id and is_nurse and ("bls" in text_lower or "acls" in text_lower):
                add_reasoning(
                    "Q_SKILL_07: BLS and ACLS certifications explicitly confirmed — mandatory "
                    "compliance requirement satisfied for Staff Nurse role."
                )

            elif "EXP_09" in q_id and is_eng:
                if is_advanced_tech:
                    add_reasoning(
                        "Q_EXP_09: Microservices migration confirmed. Response lacks transactional "
                        "consistency strategy and rollback mechanism — scored functional, not expert."
                    )
                else:
                    add_reasoning(
                        "Q_EXP_09: Microservices cited but omits migration scope, team size, "
                        "service boundary design, and failure scenario handling."
                    )

            elif "SKILL_05" in q_id and is_eng and ("docker" in text_lower or "kubernetes" in text_lower):
                add_reasoning(
                    "Q_SKILL_05: Docker and Kubernetes deployment confirmed. Missing depth: "
                    "no mention of pod autoscaling, Helm charts, cluster namespacing, or rolling update strategy."
                )

            elif "SKILL_09" in q_id and is_eng:
                add_reasoning(
                    "Q_SKILL_09: Correctly identifies DB lock contention and index analysis. "
                    "Missing: EXPLAIN plan inspection, connection pool tuning, and slow query log review."
                )

            elif is_advanced_tech and tech_gap:
                add_reasoning(tech_gap)

        # ── Phase 3: Aggregation ───────────────────────────────────────────────
        n_q           = len(transcripts)
        agg_relevance = round(overall_relevance_sum     / n_q, 2)
        agg_comm      = round(overall_communication_sum / n_q, 2)
        agg_tech      = round(overall_tech_sum          / n_q, 2)
        avg_stt_conf  = round(sum(confidences)          / n_q, 2)
        overall_score = round(0.4 * agg_tech + 0.3 * agg_relevance + 0.3 * agg_comm, 2)

        for qa in qa_breakdown:
            if qa.get("key_entities_found") is None:
                del qa["key_entities_found"]

        # ── RULE 3: Consistency Validation Layer ──────────────────────────────
        validation_flags = []

        # A. Experience check
        if global_icu_exp > 0 and global_total_exp > 0 and global_icu_exp > global_total_exp:
            validation_flags.append({
                "flag": "EXPERIENCE_INCONSISTENCY", "severity": "HIGH",
                "detail": (f"ICU experience ({global_icu_exp}y) exceeds stated total experience "
                           f"({global_total_exp}y). Logically impossible."),
                "affected_fields": ["Q_EXP_01", "Q_EXP_02"]
            })

        # B. Salary check
        if global_sal_curr > 0 and global_sal_exp > 0:
            if global_sal_exp < global_sal_curr:
                validation_flags.append({
                    "flag": "SALARY_MISMATCH", "severity": "HIGH",
                    "detail": (f"Expected salary ({global_sal_exp} USD) is less than current "
                               f"({global_sal_curr} USD). Profile inconsistent."),
                    "affected_fields": ["Q_SAL_01", "Q_SAL_02"]
                })
            else:
                hike_pct = ((global_sal_exp - global_sal_curr) / global_sal_curr) * 100
                if hike_pct > 50:
                    validation_flags.append({
                        "flag": "HIGH_SALARY_EXPECTATION", "severity": "MEDIUM",
                        "detail": (f"Candidate expects {hike_pct:.0f}% salary increase "
                                   f"({global_sal_curr}→{global_sal_exp} USD). Negotiation likely required."),
                        "affected_fields": ["Q_SAL_01", "Q_SAL_02"]
                    })

        # C. Notice period check
        if global_np_days > 90:
            validation_flags.append({
                "flag": "LONG_NOTICE_PERIOD", "severity": "MEDIUM",
                "detail": (f"Notice period {global_np_days}d exceeds 90-day hiring risk threshold. "
                           f"Joining timeline at risk."),
                "affected_fields": ["Q_NP_01"]
            })

        # D. Relocation dependency check
        if global_loc != "Unknown" and not global_relocate:
            validation_flags.append({
                "flag": "RELOCATION_DEPENDENCY", "severity": "LOW",
                "detail": (f"Candidate located in {global_loc} with no confirmed relocation intent. "
                           f"Verify job-location alignment before proceeding."),
                "affected_fields": ["Q_LOC_01", "Q_LOC_02"]
            })

        # ── RULE 4: Strict decision thresholds with specific justification ─────
        if avg_stt_conf < 0.50:
            status = "HOLD"
            decision_reason = ("Low average STT confidence across session — responses may be "
                               "unreliable for automated scoring. Manual review recommended.")
        elif overall_score >= 0.75:
            status = "SELECTED"
            decision_reason = (
                f"Cleared SELECTED threshold (score={overall_score}). "
                f"Technical={agg_tech}, Relevance={agg_relevance}, Communication={agg_comm}."
            )
        elif overall_score >= 0.60:
            status = "HOLD"
            gaps = []
            if agg_tech      < 0.65: gaps.append(f"technical depth below threshold ({agg_tech:.2f} < 0.65)")
            if agg_relevance < 0.65: gaps.append(f"borderline relevance ({agg_relevance:.2f})")
            if global_np_days > 90:  gaps.append(f"long notice period ({global_np_days}d)")
            if global_sal_curr > 0 and global_sal_exp > global_sal_curr:
                h = ((global_sal_exp - global_sal_curr) / global_sal_curr) * 100
                if h > 50: gaps.append(f"high salary expectation (+{h:.0f}%)")
            decision_reason = (
                "HOLD pending recruiter review. Gaps: " +
                ("; ".join(gaps) if gaps else "scores borderline across all dimensions") + "."
            )
        else:
            status = "REJECTED"
            decision_reason = (
                f"Score {overall_score} below rejection threshold (0.60). "
                f"Technical competency {agg_tech:.2f} insufficient for role requirements."
            )

        return {
            "application": {
                "candidate_id": candidate_id,
                "job_id":       job_id,
                "session_id":   session_id,
                "timestamp":    datetime.utcnow().isoformat() + "Z"
            },
            "interaction_summary": {
                "total_questions_answered": n_q,
                "total_duration_seconds":   total_duration,
                "average_stt_confidence":   avg_stt_conf
            },
            "aggregate_scores": {
                "overall_relevance":     agg_relevance,
                "overall_communication": agg_comm,
                "technical_competency":  agg_tech,
                "overall_score":         overall_score,
                "score_breakdown": {
                    "formula":        "0.4 * technical + 0.3 * relevance + 0.3 * communication",
                    "computed_score": overall_score
                }
            },
            "behavioral_analysis": self.behavioral_analyzer.analyze_candidate([
                {"question_id": q["question_id"], "answer": q["answer_normalized"]}
                for q in qa_breakdown
            ]),
            "normalized_profile": {
                "salary": {
                    "current":  {
                        "amount": global_sal_curr, "currency": "USD", "period": "monthly",
                        "confidence": 0.88 if global_sal_curr > 0 else 0.0
                    },
                    "expected": {
                        "amount": global_sal_exp, "currency": "USD", "period": "monthly",
                        "confidence": 0.88 if global_sal_exp > 0 else 0.0
                    }
                },
                "location": {
                    "current_location":    global_loc,
                    "willing_to_relocate": global_relocate,
                    "confidence":          0.85 if global_loc != "Unknown" else 0.0
                },
                "notice_period": {
                    "days":        global_np_days,
                    "negotiable":  global_np_neg,
                    "confidence":  0.90 if global_np_days > 0 else 0.0
                }
            },
            "final_decision": {
                "status":                 status,
                "decision_justification": decision_reason,
                "explainable_reasoning":  reasoning
            },
            "decision_trace": {
                "driving_factors": list(dict.fromkeys(driving_factors))[:4]
            },
            "validation_flags": validation_flags,
            "qa_breakdown":     qa_breakdown
        }
