from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

t1 = "Provided patient care"
t2 = "Deliver direct patient care"

# Clean as per requested logic
def clean(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

c1 = clean(t1)
c2 = clean(t2)

e1 = model.encode([c1], normalize_embeddings=True)
e2 = model.encode([c2], normalize_embeddings=True)

sim = cosine_similarity(e1, e2)[0][0]
print(f"Similarity: {sim:.4f}")
