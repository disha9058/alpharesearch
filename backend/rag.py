"""
DAY 1 — SCRIPT 3: Complete Mini RAG Pipeline (using Groq — free)
=================================================================
Full RAG loop: chunk → embed → store → search → answer.
Groq handles the LLM calls. sentence-transformers handles embeddings locally.

HOW TO RUN:
  python rag.py

WHAT TO NOTICE:
  - The LLM answers ONLY from the text provided
  - Ask about something NOT in the text → it says "I don't know"
  - No hallucination — just reading and summarizing
"""

import os
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

client  = Groq(api_key=os.getenv("GROQ_API_KEY"))
embedder = SentenceTransformer("all-MiniLM-L6-v2")
MODEL   = "llama-3.3-70b-versatile"


# ─────────────────────────────────────────────────────────────
# FAKE ANNUAL REPORT TEXT
# Day 2: replace this with a real PDF loaded via pypdf
# ─────────────────────────────────────────────────────────────
ANNUAL_REPORT = """
Infosys Annual Report FY2025 — Selected Excerpts

FINANCIAL PERFORMANCE
Revenue for FY2025 reached $18.56 billion, a growth of 1.4% in constant currency.
Operating margin stood at 20.7%, within the guided range of 20-22%.
Net profit was $3.2 billion, up 8.9% year-over-year.
Free cash flow conversion remained strong at 103% of net profit.
Earnings per share grew by 9.4% to reach $0.74 for the fiscal year.

RISK FACTORS
The company faces significant headwinds from reduced discretionary IT spending by clients,
particularly in the BFSI segment in North America and Europe.
Currency fluctuation risk remains elevated — 60% of revenues are USD-denominated.
Increasing competition from global IT peers and AI-based automation tools
may impact traditional service models and pricing power.
Attrition rate decreased to 12.7% versus 24.3% in the prior year.
Geopolitical tensions and visa restrictions in key markets remain a concern.

STRATEGIC PRIORITIES
Infosys is investing in AI through its Infosys Topaz platform for enterprise clients.
The company signed 12 large deals worth over $100 million each in FY2024.
Cloud migration services grew 28% year-over-year, the fastest-growing segment.
Revenue guidance for FY2025 is set at 4-7% growth in constant currency.

HEADCOUNT
Total employees: 317,240 — a reduction of 26,000 from the FY2023 peak.
The company operates across 56 countries with 250+ delivery centers globally.
Women represent 39.4% of the total workforce.
"""


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 80, overlap: int = 15) -> list[str]:
    """Split text into overlapping word-level chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if len(chunk.strip()) > 40:
            chunks.append(chunk.strip())
        i += chunk_size - overlap
    return chunks


def embed(text: str) -> np.ndarray:
    """Convert text to a vector using local sentence-transformers (free, no API)."""
    return embedder.encode(text)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Measure how similar two vectors are. 1.0 = identical, 0.0 = unrelated."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ─────────────────────────────────────────────────────────────
# IN-MEMORY VECTOR STORE
# Day 2: swap this for Pinecone — same add() / search() interface
# ─────────────────────────────────────────────────────────────

class VectorStore:
    def __init__(self):
        self.texts: list[str] = []
        self.vectors: list[np.ndarray] = []

    def add(self, text: str):
        self.texts.append(text)
        self.vectors.append(embed(text))

    def search(self, query: str, top_k: int = 3) -> list[tuple[float, str]]:
        query_vec = embed(query)
        scored = [(cosine_similarity(query_vec, v), t)
                  for v, t in zip(self.vectors, self.texts)]
        return sorted(scored, reverse=True)[:top_k]


# ─────────────────────────────────────────────────────────────
# RAG PIPELINE
# ─────────────────────────────────────────────────────────────

def generate_answer(question: str, context_chunks: list[str]) -> str:
    """Pass retrieved chunks as context → Groq reads them → answers from them."""
    context = "\n\n".join(context_chunks)

    prompt = f"""You are a financial analyst. Answer using ONLY the context below.
If the context doesn't contain the answer, say: "The provided documents don't cover this."
Never use your own knowledge — only read and summarize from the context.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350,
        temperature=0
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Day 1, Script 3: Mini RAG Pipeline")
    print("=" * 60)

    print("\n📄 Chunking annual report...")
    chunks = chunk_text(ANNUAL_REPORT)
    print(f"   Created {len(chunks)} chunks")

    print("\n🔢 Embedding and storing chunks...")
    store = VectorStore()
    for chunk in chunks:
        store.add(chunk)
    print(f"   Stored {len(store.texts)} vectors")

    questions = [
        "What risks does Infosys face?",
        "How did Infosys perform financially in FY2024?",
        "What is Infosys doing with AI?",
        "How many employees does Infosys have?",
        "What is Infosys's stance on climate change?",  # NOT in the doc
    ]

    for question in questions:
        print("\n" + "─" * 60)
        print(f" Q.{question}")

        results = store.search(question, top_k=2)
        print("\n   Top retrieved chunks:")
        for score, chunk in results:
            print(f"   [{score:.3f}] {chunk[:75]}...")

        answer = generate_answer(question, [c for _, c in results])
        print(f"\n Ans {answer}")

    print("\n" + "=" * 60)
    print("RAG pipeline working with Groq.")
    print("=" * 60)
    """
    print("\nTomorrow — Day 2:")
    print("  → Load a real Infosys PDF annual report")
    print("  → Replace VectorStore with Pinecone")
    print("  → Your RAG becomes persistent and production-grade")
    """