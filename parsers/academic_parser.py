import re
import json
from typing import List, Dict, Optional

DEGREE_PATTERNS = [
    (r"\b(?:Ph\.?D\.?|Doctor\s+of\s+Philosophy|Doctor\s+of\s+Nursing\s+Practice|DNP)\b", "phd"),
    (r"\b(?:M\.?Tech|Master\s+of\s+Technology|MBA|Master\s+of\s+Business\s+Administration|M\.?S\.?c?\.?|Master\s+of\s+Science|M\.?E\.?|MCA|MSc\s+Nursing)\b", "master"),
    (r"\b(?:B\.?Tech|Bachelor\s+of\s+Technology|B\.?E\.?|Bachelor\s+of\s+Engineering|B\.?S\.?c?\.?|Bachelor\s+of\s+Science|B\.?C\.?A\.?|BBA|B\.?Com|BSc\s+Nursing|Post\s+Basic\s+BSc\s+Nursing)\b", "bachelor"),
    (r"\b(?:Diploma|GNM|General\s+Nursing\s+and\s+Midwifery|Vocational)\b", "diploma")
]

class AcademicParser:
    def __init__(self):
        pass

    def extract_education(self, text: str) -> List[Dict]:
        education_entries = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5: continue
            
            degree_token = None
            level_found = None
            for pattern, level in DEGREE_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    degree_token = matches[0]
                    level_found = level
                    break
            
            if degree_token:
                # 1. Graduation Year: Extract the LAST 4-digit date
                dates = re.findall(r"\b(?:19|20)\d{2}\b", line)
                grad_year = int(dates[-1]) if dates else None
                
                # 2. Field Extraction/Inference (MANDATORY)
                field = "not specified"
                # Remove year/symbols for keyword matching
                clean_line = re.sub(r"\b\d{4}\b", " ", line)
                clean_line = re.sub(r"[\(\)\d\-\–\—]", " ", clean_line)
                
                # Sort keywords by length descending to match 'analytical chemistry' before 'chemistry'
                field_keywords = [
                    "computer science", "information technology", "mechanical engineering", 
                    "civil engineering", "business administration", "analytical chemistry", 
                    "chemistry", "nursing", "healthcare", "medicine", "biological sciences",
                    "data science", "biotechnology"
                ]
                for kw in sorted(field_keywords, key=len, reverse=True):
                    if kw in clean_line.lower() or kw in degree_token.lower():
                        field = kw
                        break
                
                # Mandatory Inference if still not specified
                if field == "not specified":
                    lt = line.lower()
                    dt = degree_token.lower()
                    if any(x in dt or x in lt for x in ["nursing", "rn", "gnm", "medicine", "health", "clinical", "bcs"]): 
                        field = "nursing" if any(x in dt or x in lt for x in ["nursing", "nurse"]) else "healthcare"
                    elif any(x in dt or x in lt for x in ["computer", "bca", "mca", "software", "it", "information"]): field = "computer science"
                    elif "tech" in dt: field = "engineering"
                
                # 3. Institution Extraction (CLEAN)
                institution = "not specified"
                segments = re.split(r"\s*[\-|\–|—|,|\|]\s*", line)
                
                # If segments found, check them
                if len(segments) > 1:
                    for segment in segments:
                        seg = segment.strip()
                        if any(x in seg.lower() for x in ["college", "university", "institute", "school", "hospital", "board", "st joseph", "rajagiri"]):
                             if degree_token.lower() not in seg.lower() and len(seg) > 5:
                                 institution = seg
                                 break
                
                # Fallback: Scrape remaining part of line if institution still not found
                if institution == "not specified":
                    # Remove degree from the line before looking for institution
                    remaining = line.replace(degree_token, "")
                    
                    # DO NOT remove field if it might be part of an institution name (like 'Nursing College')
                    # Instead of re.sub(re.escape(field), "", remaining, flags=re.IGNORECASE)
                    # We only remove it if it's clearly a qualification prefix (e.g. 'in nursing')
                    remaining = re.sub(rf"\bin\s+{re.escape(field)}\b", "", remaining, flags=re.IGNORECASE)
                    
                    for date in re.findall(r"\b(?:19|20)\d{2}\b", line):
                        remaining = remaining.replace(str(date), "")
                    
                    # Look for keywords in the remaining string - GREEDY match to capture full name
                    match = re.search(r"\b.*?(?:university|college|institute|school|hospital|board|st joseph|rajagiri).*?\b", remaining, re.IGNORECASE)
                    if match:
                        # Capture more context around the keyword if available
                        full_match = re.search(rf"\b[A-Z\s]*?{re.escape(match.group(0))}[A-Z\s]*\b", remaining, re.IGNORECASE)
                        institution = full_match.group(0).strip() if full_match else match.group(0).strip()
                
                # Cleanup Institution (remove brackets, dates, symbols, score, common fillers)
                institution = re.sub(r"[\d+%]+", "", institution) # Remove scores like '75%'
                institution = re.sub(r"\b(?:19|20)\d{2}\b", "", institution)
                institution = re.sub(r"[\(\)\u2013\u2014\-\[\]]", " ", institution).strip()
                # Remove common prefixes like 'in ', 'at ', 'from ', 'of '
                institution = re.sub(r"^(?:in|at|from|of|on)\b\s*", "", institution, flags=re.IGNORECASE).strip()
                
                # Final field remnant removal - ONLY if it's not part of the institution's core name
                # (e.g., "Rajagiri College of Nursing" -> keep "nursing" if it's the official name)
                # We only remove it if it's a prefix followed by a separator or space in a way that looks like a field description
                if field != "not specified" and field not in ["nursing", "healthcare"]: # Be careful with healthcare/nursing names
                     institution = re.sub(rf"^{re.escape(field)}\b\s*", "", institution, flags=re.IGNORECASE).strip()

                institution = re.sub(r"\s+", " ", institution).lower()

                education_entries.append({
                    "degree": self._normalize_degree_name(degree_token).lower(),
                    "degree_level": level_found.lower(),
                    "field": field.lower(),
                    "institution": institution,
                    "graduation_year": grad_year
                })
                
        return education_entries

    def _normalize_degree_name(self, degree: str) -> str:
        d = degree.lower().replace(".", "").strip()
        if "btech" in d or "b tech" in d: return "bachelor of technology"
        if "be" == d or "b e" in d: return "bachelor of engineering"
        if "bsc" in d or "b sc" in d: return "bachelor of science"
        if "mba" in d: return "master of business administration"
        if "mtech" in d or "m tech" in d: return "master of technology"
        if "ms" == d or "m sc" in d or "msc" in d: return "master of science"
        if "phd" in d: return "phd"
        return degree.lower()

    def extract_certifications(self, text: str) -> List[Dict]:
        certs = []
        seen_norm = set()
        
        # 1. Strip SUMMARY/PROFILE to avoid extraction from descriptive text
        scan_text = re.sub(r"(?i)^SUMMARY.*?\n(?=SKILLS|EXPERIENCE|EDUCATION|CERTIFICATIONS|$)", "", text, flags=re.DOTALL|re.MULTILINE)
        scan_text = re.sub(r"(?i)^PROFILE.*?\n(?=SKILLS|EXPERIENCE|EDUCATION|CERTIFICATIONS|$)", "", scan_text, flags=re.DOTALL|re.MULTILINE)

        # 2. Look for dedicated sections (STRICT: Header must be on its own line/start of line)
        patterns = [
            r"(?i)(?:\n|^)(?:CERTIFICATIONS|LICENSES|COURSES)[\s:]*\n(.*?)(?:\n(?=EDUCATION|EXPERIENCE|PROJECTS|SKILLS|SUMMARY|LANGUAGES|$))"
        ]
        
        for pattern in patterns:
            section_match = re.search(pattern, scan_text, re.DOTALL)
            if section_match:
                lines = section_match.group(1).split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 3: continue
                    # Split list-like lines
                    parts = re.split(r"[,;•\-\*]| and ", line)
                    for p in parts:
                        p_clean = p.strip()
                        # Extra filter: avoid picking up sentences or project descriptions
                        if len(p_clean.split()) > 8: continue 
                        self._add_cert_if_valid(certs, p_clean, seen_norm, confidence=0.95)

        # 3. General Scan (Scan REMAINING text for HIGH CONFIDENCE keywords only)
        lines = scan_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3: continue
            
            # Avoid scanning lines that look like sentences or have 'experience' markers
            if len(line.split()) > 10: continue
            if any(x in line.lower() for x in ["experience", "skilled", "performed", "managed", "worked"]): continue

            if re.search(r"\b(?:bls|acls|rn license|registered nurse license|registered nurse|certified|certification|cpr)\b", line, re.IGNORECASE):
                parts = re.split(r"[,;•\-\*]| and ", line)
                for p in parts:
                    conf = 0.95 if any(x in p.lower() for x in ["bls", "acls", "rn"]) else 0.9
                    self._add_cert_if_valid(certs, p.strip(), seen_norm, confidence=conf)
                        
        return certs

    def _add_cert_if_valid(self, certs, name, seen_norm, confidence):
        if len(name) < 3 or len(name) > 100: return
        
        # Normalize: lower, remove brackets, standardized names
        norm = name.lower()
        norm = re.sub(r"[\(\[].*?[\)\]]", "", norm).strip() # Remove brackets
        
        # Mapping variations for consistency
        if re.search(r"\bbls\b", norm): norm = "basic life support"
        if re.search(r"\bacls\b", norm): norm = "advanced cardiovascular life support"
        if "registered nurse" in norm or (re.search(r"\brn\b", norm) and "licen" not in norm): 
            norm = "registered nurse license"
        
        # Extra Filters: Avoid generic words, sentences, or common personality traits
        noise_words = [
            "detail", "compassionate", "summary", "analytical", "motivated", "contribute", "assisted", "administered",
            "provided", "assisted", "maintained", "supported", "skills", "experience", "patient cares"
        ]
        if any(word == norm for word in noise_words) or len(norm.split()) > 8: return
        if not re.search(r"[a-z]", norm): return # No letters

        # Final cleanup
        norm = re.sub(r"[•\-\*\|]", " ", norm)
        norm = re.sub(r"\s+", " ", norm).strip()
        
        # Deduplication
        if norm and norm not in seen_norm:
            category = "other"
            # Mandatory categorization for known certs (match normalized words)
            if any(x in norm for x in ["nurse", "life support", "acls", "bls", "rn", "clinical", "cpr", "medical", "nursing", "patient"]):
                category = "healthcare"
            elif any(x in norm for x in ["aws", "azure", "cloud", "docker", "gcp"]):
                category = "cloud"
            elif any(x in norm for x in ["data", "learning", "python", "sql", "ai", "machine", "analytics"]):
                category = "data"
            
            certs.append({
                "name": name.lower().strip(),
                "normalized_name": norm,
                "category": category,
                "confidence": confidence
            })
            seen_norm.add(norm)

    def parse_academic_profile(self, resume_text: str) -> Dict:
        return {
            "education": self.extract_education(resume_text),
            "certifications": self.extract_certifications(resume_text)
        }
