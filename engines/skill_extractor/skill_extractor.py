import re
import json
import difflib
import spacy
from typing import List, Dict, Set, Tuple
from spacy.matcher import PhraseMatcher
from utils.logger import get_logger

logger = get_logger("skill_extractor", "logs/skill_extraction.log")

class SkillExtractor:
    def __init__(self, dictionary_path: str):
        self.dictionary_path = dictionary_path
        self.master_skills = self._load_dictionary()
        
        # Initialize mappings before setup
        self.alias_to_canonical = {}
        self.skill_to_category = {}
        self._build_mappings()

        self.nlp = self._load_spacy_model()
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._setup_matcher()

    def _load_dictionary(self) -> Dict:
        """Load the master skill dictionary from JSON."""
        try:
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load skill dictionary: {e}")
            return {"tech": {}, "business": {}, "creative": {}, "stacks": {}}

    def _load_spacy_model(self):
        """Load the spaCy model, download if missing."""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.info("Downloading en_core_web_sm...")
            from spacy.cli import download
            download("en_core_web_sm")
            return spacy.load("en_core_web_sm")

    def _build_mappings(self):
        """Cache all synonyms for fast lookup and normalization."""
        # Categorize everything except 'stacks' which are handled separately
        for section in self.master_skills.keys():
            if section == "stacks": continue
            
            for canonical, data in self.master_skills.get(section, {}).items():
                self.skill_to_category[canonical] = data.get("category", section)
                self.alias_to_canonical[canonical.lower()] = canonical
                for syn in data.get("synonyms", []):
                    self.alias_to_canonical[syn.lower()] = canonical
        
        # Add stacks
        for stack_name, data in self.master_skills.get("stacks", {}).items():
            self.alias_to_canonical[stack_name.lower()] = stack_name
            for syn in data.get("synonyms", []):
                self.alias_to_canonical[syn.lower()] = stack_name

    def _setup_matcher(self):
        """Add all skills and synonyms to the spaCy PhraseMatcher."""
        for alias in self.alias_to_canonical.keys():
            patterns = [self.nlp.make_doc(alias)]
            self.matcher.add("SKILL", patterns)

    def extract_skills(self, text: str, section_context: str = "general") -> List[Dict]:
        """
        Extract skills from text, normalize them, and assign confidence scores.
        
        Returns:
            List of dicts: [{"skill": "Python", "confidence": 1.0, "category": "tech", "variants": [...]}]
        """
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        found_map = {} # canonical -> {confidence, category, variants}

        for match_id, start, end in matches:
            span = doc[start:end]
            raw_match = span.text
            match_lower = raw_match.lower()
            
            canonical = self.alias_to_canonical.get(match_lower)
            if not canonical:
                continue

            # Confidence scoring
            is_exact = (raw_match.lower() == canonical.lower())
            base_score = 1.0 if is_exact else 0.95
            
            # Context boost
            if section_context.lower() in ["skills", "technical skills", "requirements", "core competencies"]:
                base_score = min(1.0, base_score + 0.05)

            if canonical not in found_map:
                found_map[canonical] = {
                    "skill": canonical,
                    "confidence": base_score,
                    "category": self.skill_to_category.get(canonical, "other"),
                    "variants": {raw_match}
                }
            else:
                found_map[canonical]["confidence"] = max(found_map[canonical]["confidence"], base_score)
                found_map[canonical]["variants"].add(raw_match)

        # Handle spelling variations & fuzzy matches
        self._fuzzy_match_extraction(text, found_map)

        # Convert to list for final processing (deduplication & stack expansion)
        final_list = self._expand_stacks(found_map)
        
        # Final cleanup: variants to sorted list
        for item in final_list:
            if isinstance(item["variants"], set):
                item["variants"] = sorted(list(item["variants"]))
            elif isinstance(item["variants"], str):
                item["variants"] = [item["variants"]]
            
        return sorted(final_list, key=lambda x: x["confidence"], reverse=True)

    def _fuzzy_match_extraction(self, text: str, found_map: Dict):
        """Try to find skills that might be misspelled."""
        # Clean text for word extraction
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
        known_aliases = list(self.alias_to_canonical.keys())
        
        for word in set(words):
            word_lower = word.lower()
            if word_lower in self.alias_to_canonical:
                continue
            
            close_matches = difflib.get_close_matches(word_lower, known_aliases, n=1, cutoff=0.88)
            if close_matches:
                match_alias = close_matches[0]
                canonical = self.alias_to_canonical[match_alias]
                confidence = 0.80 # Lower confidence for fuzzy match
                
                if canonical not in found_map:
                    found_map[canonical] = {
                        "skill": canonical,
                        "confidence": confidence,
                        "category": self.skill_to_category.get(canonical, "other"),
                        "variants": {word}
                    }
                else:
                    found_map[canonical]["variants"].add(f"{word} (fuzzy)")

    def _expand_stacks(self, found_map: Dict) -> List[Dict]:
        """Expand found stacks into constituent skills."""
        stacks_dict = self.master_skills.get("stacks", {})
        results_map = found_map.copy()
        
        # Collect stacks found
        found_stacks = [s for s in found_map if s in stacks_dict]
        
        for stack_name in found_stacks:
            stack_data = stacks_dict[stack_name]
            sub_skills = stack_data.get("skills", [])
            for ss in sub_skills:
                # If the sub-skill is NOT already found, add it but flag as implied
                if ss not in results_map:
                    results_map[ss] = {
                        "skill": ss,
                        "confidence": 0.85, # Implied skill
                        "category": f"{self.skill_to_category.get(ss, 'tech')} (impllied)",
                        "variants": {f"Implied by {stack_name}"}
                    }
                else:
                    # If it IS found, maybe we boost its confidence?
                    results_map[ss]["confidence"] = max(results_map[ss]["confidence"], 0.95)
                    results_map[ss]["variants"].add(f"Reinforced by {stack_name}")

        return list(results_map.values())


def test_extraction():
    extractor = SkillExtractor("data/skills/master_skills.json")
    sample_text = """
    We are looking for a Python developer with experience in React and the MERN stack.
    Knowledge of AWS and Pythn is a plus. Also need someone with Project Management skills.
    """
    skills = extractor.extract_skills(sample_text)
    print(json.dumps(skills, indent=2))

if __name__ == "__main__":
    test_extraction()
