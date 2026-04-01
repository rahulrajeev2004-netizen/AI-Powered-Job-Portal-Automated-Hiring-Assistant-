from sentence_transformers import SentenceTransformer
import numpy as np
import os
import warnings
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# HuggingFace performance configs
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

hf_token = os.getenv("HF_TOKEN")
if hf_token:
    os.environ["HF_TOKEN"] = hf_token

warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")


class Embedder:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        """
        Initialize embedding model (optimized for semantic similarity).
        """
        self.model = SentenceTransformer(model_name)

    # =========================
    # TEXT CLEANING (IMPROVED)
    # =========================
    def clean_text(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return ""

        text = text.lower()

        # Remove bullets, special symbols, numbers-only tokens
        text = re.sub(r'[\•\●\▪\■\-–—]', ' ', text)
        text = re.sub(r'[^a-z\s]', ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    # =========================
    # JOB TITLE CLEANING
    # =========================
    def clean_job_title(self, title: str) -> str:
        if not title:
            return ""

        # Remove leading numbers (e.g., "82 ICU Nurse")
        title = re.sub(r'^\d+\s*', '', title)

        # Remove extra noise
        title = self.clean_text(title)

        return title

    # =========================
    # DEDUPLICATION
    # =========================
    def deduplicate_entries(self, entries):
        seen = set()
        cleaned = []

        for e in entries:
            e = self.clean_text(e)
            if e and e not in seen:
                seen.add(e)
                cleaned.append(e)

        return cleaned

    # =========================
    # CORE EMBEDDING FUNCTION
    # =========================
    def get_embeddings(self, texts):
        """
        Generate high-quality normalized embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        # Clean + remove empty
        cleaned_texts = []
        for t in texts:
            ct = self.clean_text(t)
            if ct:
                cleaned_texts.append(ct)

        if not cleaned_texts:
            return np.array([])

        # DEBUG (Day 12 requirement)
        print("\n[DEBUG] Cleaned Texts for Embedding:")
        for t in cleaned_texts:
            print(" -", t)

        # Generate embeddings (normalized → cosine works correctly)
        embeddings = self.model.encode(
            cleaned_texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings

    # =========================
    # EXPERIENCE TEXT BUILDER
    # =========================
    def build_experience_text(self, experiences):
        """
        Convert list of experience entries into one meaningful semantic block.
        """
        if not experiences:
            return ""

        cleaned_exp = [self.clean_text(e) for e in experiences if e]
        return " ".join(cleaned_exp)

    # =========================
    # SKILL PREPARATION
    # =========================
    def prepare_skills(self, skills):
        """
        Clean + deduplicate skills before embedding.
        """
        if not skills:
            return []

        skills = [self.clean_text(s) for s in skills if s]
        skills = list(dict.fromkeys(skills))  # preserve order

        return skills