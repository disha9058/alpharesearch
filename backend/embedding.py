"""
DAY 1 — SCRIPT 2: Embeddings — Feel the Concept
=================================================
What this does: converts sentences into vectors (lists of numbers)
and shows you that similar sentences produce similar vectors.

This is the foundation of RAG. If you understand this script,
you understand how vector search works.

HOW TO RUN:
  python day1_step2_embeddings.py

NOTE: First run downloads ~90MB model. Wait for it — it's one time only.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

print("Loading embedding model... (first run: ~90MB download, be patient)")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Model loaded!\n")


def embed(text: str) -> np.ndarray:
    """Convert any text into a vector of 384 numbers."""
    return model.encode(text)


def similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Cosine similarity — measures how close two vectors are.
    Score of 1.0 = identical meaning
    Score of 0.0 = completely unrelated
    
    This is EXACTLY what Pinecone does when you search it.
    """
    return float(
        np.dot(vec_a, vec_b) /
        (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    )


# ─────────────────────────────────────────────────────────────
# EXPERIMENT 1: What does an embedding look like?
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("EXPERIMENT 1: A sentence converted to numbers")
print("=" * 55)

sentence = "Infosys reported strong quarterly earnings."
vector = embed(sentence)

print(f"\nSentence : '{sentence}'")
print(f"Vector   : {len(vector)} numbers total")
print(f"First 6  : {vector[:6].round(4)}")
print("\nThis is the sentence's MEANING stored as math.\n")


# ─────────────────────────────────────────────────────────────
# EXPERIMENT 2: Similar meaning → similar vector → high score
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("EXPERIMENT 2: Similarity scores")
print("=" * 55)

base_sentence = "What are the risks for Tata Motors?"
base_vec = embed(base_sentence)

test_sentences = [
    ("What challenges does Tata Motors face?",     "same meaning, different words"),
    ("What threats exist for Tata Motors in 2025?","similar meaning"),
    ("Tata Motors revenue and profit margins",      "related but different topic"),
    ("How to make biryani at home",                "completely unrelated"),
]

print(f"\nBase: '{base_sentence}'\n")

for sentence, note in test_sentences:
    vec = embed(sentence)
    score = similarity(base_vec, vec)
    filled = int(score * 25)
    bar = "█" * filled + "░" * (25 - filled)
    print(f"  {score:.3f} |{bar}|")
    print(f"         '{sentence}'")
    print(f"          → {note}\n")


# ─────────────────────────────────────────────────────────────
# EXPERIMENT 3: Mini semantic search — this IS what RAG does
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("EXPERIMENT 3: Semantic search over document chunks")
print("= This is the R in RAG =")
print("=" * 55)

# These are 5 fake "chunks" from an annual report
chunks = [
    "The company's revenue grew 14% year-over-year driven by cloud services.",
    "Key risks include regulatory changes and rising competition from global players.",
    "The board approved a share buyback program worth ₹5,000 crores.",
    "Total employee headcount reached 342,000 globally this fiscal year.",
    "Raw material cost inflation has compressed operating margins by 2.3%.",
]

query = "What risks does the company face?"
query_vec = embed(query)

print(f"\nQuery: '{query}'")
print("\nSearching all 5 chunks...\n")

results = sorted(
    [(similarity(query_vec, embed(c)), c) for c in chunks],
    reverse=True
)

for rank, (score, chunk) in enumerate(results, 1):
    tag = " ← TOP MATCH (this goes to LLM as context)" if rank == 1 else ""
    print(f"  Rank {rank} | {score:.3f} | {chunk[:65]}...{tag}")

#print("\n✅ Script 2 done. You now understand embeddings and vector search.")
#print("➡️  Now run: python rag.py")